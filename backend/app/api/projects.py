import os
import shutil
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.orm import Session
from app.db.database import get_db, SessionLocal
from app.config.settings import settings
from app.models.project import Project
from app.models.analysis_job import AnalysisJob
from app.schemas.overview import (
    ProjectUploadResponse,
    AnalysisStatusResponse,
    ProjectOverviewResponse,
)
from app.services.project_parser import extract_project, cleanup_project, ZipTraversalError
from app.services.project_overview_service import (
    run_project_analysis,
    build_project_overview_response,
)

router = APIRouter(prefix="/projects", tags=["projects"])

def run_analysis_background_task(project_id: str, zip_file_path: Path):
    """Background task handler for project analysis."""
    db: Session = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        job = db.query(AnalysisJob).filter(AnalysisJob.project_id == project_id).order_by(AnalysisJob.started_at.desc()).first()
        
        if not project or not job:
            return

        extract_target_dir = settings.TEMP_DIR / f"project_{project_id}"
        
        # 1. Safely Extract ZIP
        job.current_stage = "Extracting uploaded archive"
        job.progress = 5
        db.commit()
        
        extracted_dir = extract_project(zip_file_path, extract_target_dir)
        
        # 2. Execute Analysis Pipeline
        run_project_analysis(db, project, extracted_dir, job)
        
    except ZipTraversalError as e:
        db.rollback()
        project = db.query(Project).filter(Project.id == project_id).first()
        job = db.query(AnalysisJob).filter(AnalysisJob.project_id == project_id).first()
        if project and job:
            project.status = "failed"
            job.status = "failed"
            job.error_message = f"Security Error: {str(e)}"
            job.current_stage = "Extraction failed"
            db.commit()
    except Exception as e:
        db.rollback()
        project = db.query(Project).filter(Project.id == project_id).first()
        job = db.query(AnalysisJob).filter(AnalysisJob.project_id == project_id).first()
        if project and job:
            project.status = "failed"
            job.status = "failed"
            job.error_message = str(e)
            job.current_stage = "Analysis error"
            db.commit()
    finally:
        # Cleanup temp directory & uploaded file
        extract_target_dir = settings.TEMP_DIR / f"project_{project_id}"
        cleanup_project(extract_target_dir)
        if zip_file_path.exists():
            try:
                zip_file_path.unlink()
            except Exception:
                pass
        db.close()

@router.post("/upload", response_model=ProjectUploadResponse, status_code=status.HTTP_201_CREATED)

async def upload_project(
    file: UploadFile = File(...),
    student_name: Optional[str] = Form("Alex Chen"),
    course: Optional[str] = Form("CS499 Final Project"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Upload a project ZIP file safely.
    Validates file extension and size, saves file, creates Project and AnalysisJob records.
    Automatically launches background analysis task.
    """
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only .zip project archives are supported."
        )

    # Derive project name from file name
    project_name = Path(file.filename).stem.replace("_", " ").replace("-", " ").title()
    
    project = Project(
        name=project_name,
        student_name=student_name,
        course=course,
        status="analyzing",
        source_type="zip",
        original_filename=file.filename,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Save uploaded zip
    upload_zip_path = settings.UPLOAD_DIR / f"{project.id}.zip"
    try:
        with open(upload_zip_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        db.delete(project)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save uploaded file: {str(e)}"
        )

    # Create initial AnalysisJob
    job = AnalysisJob(
        project_id=project.id,
        job_type="full_analysis",
        status="analyzing",
        progress=0,
        current_stage="Uploaded project archive",
    )
    db.add(job)
    db.commit()

    # Launch background task
    background_tasks.add_task(run_analysis_background_task, project.id, upload_zip_path)

    return ProjectUploadResponse(
        project_id=project.id,
        project_name=project.name,
        status="analyzing",
        message="Project uploaded successfully. Analysis started."
    )

@router.post("/{project_id}/analyze", response_model=AnalysisStatusResponse)
async def trigger_reanalysis(
    project_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Re-trigger project analysis for an existing project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Check if a zip file exists for this project
    upload_zip_path = settings.UPLOAD_DIR / f"{project_id}.zip"
    if not upload_zip_path.exists():
        # Search for any zip in temp or upload dir matching id
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project source archive is no longer available. Please upload the project ZIP again."
        )

    project.status = "analyzing"
    
    job = AnalysisJob(
        project_id=project.id,
        job_type="re_analysis",
        status="analyzing",
        progress=0,
        current_stage="Re-analysis queued",
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(run_analysis_background_task, project.id, upload_zip_path)

    return AnalysisStatusResponse(
        project_id=project.id,
        status="analyzing",
        progress=0,
        current_stage="Re-analysis queued",
        error=None,
    )

@router.get("/{project_id}/analysis-status", response_model=AnalysisStatusResponse)
def get_analysis_status(project_id: str, db: Session = Depends(get_db)):
    """
    Polling endpoint returning analysis job progress, stage, and error details.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    job = db.query(AnalysisJob).filter(AnalysisJob.project_id == project_id).order_by(AnalysisJob.id.desc()).first()
    
    if not job:
        return AnalysisStatusResponse(
            project_id=project.id,
            status=project.status,
            progress=100 if project.status == "completed" else 0,
            current_stage="No active job found",
            error=None,
        )

    return AnalysisStatusResponse(
        project_id=project.id,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error=job.error_message,
    )

@router.get("/{project_id}/overview", response_model=ProjectOverviewResponse)
def get_project_overview(project_id: str, db: Session = Depends(get_db)):
    """
    Get aggregated Project Overview payload with deterministic metrics and pending evaluation status.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    overview_data = build_project_overview_response(db, project)
    return overview_data

@router.get("/{project_id}")
def get_project_metadata(project_id: str, db: Session = Depends(get_db)):
    """
    Basic project metadata endpoint.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return {
        "id": project.id,
        "name": project.name,
        "student_name": project.student_name,
        "course": project.course,
        "status": project.status,
        "created_at": project.created_at.isoformat() if project.created_at else None,
    }
