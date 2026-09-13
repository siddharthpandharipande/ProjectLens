from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.project import Project
from app.services.code_quality_service import analyze_project_code_quality

router = APIRouter(prefix="/projects", tags=["code-quality"])

@router.get("/{project_id}/code-quality", status_code=status.HTTP_200_OK)
def get_code_quality_analysis(project_id: str, db: Session = Depends(get_db)):
    """
    Get detailed Code Quality findings, metrics, and weighted subscores for a project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return analyze_project_code_quality(db, project)
