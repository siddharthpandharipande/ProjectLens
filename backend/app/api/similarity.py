from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.project import Project
from app.services.similarity_service import compare_two_projects

router = APIRouter(prefix="/projects", tags=["similarity"])

class ProjectCompareRequest(BaseModel):
    project_ids: Optional[List[str]] = None
    project_a_id: Optional[str] = None
    project_b_id: Optional[str] = None

@router.post("/compare", status_code=status.HTTP_200_OK)
def compare_projects_endpoint(payload: ProjectCompareRequest, db: Session = Depends(get_db)):
    """
    Compare two projects using Token, AST, and Semantic Similarity Fusion.
    """
    id_a = payload.project_a_id or (payload.project_ids[0] if payload.project_ids and len(payload.project_ids) >= 1 else None)
    id_b = payload.project_b_id or (payload.project_ids[1] if payload.project_ids and len(payload.project_ids) >= 2 else None)

    if not id_a or not id_b:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two project IDs are required for comparison (project_a_id and project_b_id)."
        )

    try:
        res = compare_two_projects(db, id_a, id_b)
        return res
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{project_id}/similarity", status_code=status.HTTP_200_OK)
def get_project_similarity(project_id: str, db: Session = Depends(get_db)):
    """
    Get similarity score and comparison summary for a given project against other existing projects.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    other_project = db.query(Project).filter(Project.id != project_id).first()
    if not other_project:
        return {
            "project_id": project_id,
            "overall_similarity": 0.0,
            "confidence": "N/A",
            "message": "No other repository available for comparison.",
            "matching_files": []
        }

    return compare_two_projects(db, project_id, other_project.id)
