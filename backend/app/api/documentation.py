from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.project import Project
from app.services.doc_service import analyze_project_documentation

router = APIRouter(prefix="/projects", tags=["documentation"])

@router.get("/{project_id}/documentation", status_code=status.HTTP_200_OK)
def get_documentation_analysis(project_id: str, db: Session = Depends(get_db)):
    """
    Get Phase 5 Documentation Analysis: section coverage, Code ↔ Doc mismatches, and weighted score.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    return analyze_project_documentation(db, project)
