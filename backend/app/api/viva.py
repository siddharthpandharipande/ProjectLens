"""Viva Question Generator API Endpoints (Phase 8).

Provides endpoints for generating viva questions with Google Gemini AI or deterministic
fallback, tracking student practice progress, and regenerating individual questions.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.project_service import ProjectService
from app.services.viva.service import VivaService
from app.schemas.viva import (
    VivaQuestionSchema,
    VivaQuestionSetResponse,
    VivaGenerateRequest,
    VivaPracticeUpdateRequest,
    VivaProgressResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects/{project_id}/viva", tags=["Viva Questions"])


@router.post(
    "/generate",
    response_model=VivaQuestionSetResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate personalized viva questions for a project",
)
def generate_viva_questions(
    project_id: str,
    payload: VivaGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate personalized viva questions using Gemini AI or deterministic fallback."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        return VivaService.generate_questions(
            db=db,
            project_id=project_id,
            mode=payload.mode,
            difficulty=payload.difficulty or "all",
            question_count=payload.question_count,
            force_regenerate=payload.force_regenerate,
        )
    except Exception as exc:
        db.rollback()
        logger.exception("Viva generation failed for project %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate viva questions: {type(exc).__name__}: {str(exc)}",
        ) from exc


@router.get(
    "/questions",
    response_model=Optional[VivaQuestionSetResponse],
    status_code=status.HTTP_200_OK,
    summary="Get saved viva questions for a project",
)
def get_viva_questions(
    project_id: str,
    category: Optional[str] = Query(None, description="Filter by category"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty (beginner, intermediate, advanced)"),
    is_practiced: Optional[bool] = Query(None, description="Filter by practiced status"),
    db: Session = Depends(get_db),
):
    """Retrieve saved viva questions for a project without triggering re-generation."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    q_set = VivaService.get_latest_question_set(
        db=db,
        project_id=project_id,
        category=category,
        difficulty=difficulty,
        is_practiced=is_practiced,
    )
    return q_set


@router.patch(
    "/questions/{question_id}/practice",
    response_model=VivaQuestionSchema,
    status_code=status.HTTP_200_OK,
    summary="Update practiced status for a viva question",
)
def update_practice_status(
    project_id: str,
    question_id: str,
    payload: VivaPracticeUpdateRequest,
    db: Session = Depends(get_db),
):
    """Toggle or set question practice status and update progress."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        return VivaService.update_practice_status(
            db=db,
            project_id=project_id,
            question_id=question_id,
            is_practiced=payload.is_practiced,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to update practice status: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update practice status: {str(exc)}",
        ) from exc


@router.post(
    "/questions/{question_id}/regenerate",
    response_model=VivaQuestionSchema,
    status_code=status.HTTP_200_OK,
    summary="Regenerate a single viva question",
)
def regenerate_single_question(
    project_id: str,
    question_id: str,
    db: Session = Depends(get_db),
):
    """Replace an individual question with a fresh personalized viva question."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        return VivaService.regenerate_single_question(
            db=db,
            project_id=project_id,
            question_id=question_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Failed to regenerate question %s: %s", question_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate question: {str(exc)}",
        ) from exc


@router.get(
    "/progress",
    response_model=VivaProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get viva preparation practice progress",
)
def get_viva_progress(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve preparation progress stats and practiced counts across categories."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    return VivaService.get_progress(db=db, project_id=project_id)


@router.delete(
    "/questions",
    status_code=status.HTTP_200_OK,
    summary="Clear generated viva questions for a project",
)
def delete_viva_questions(
    project_id: str,
    db: Session = Depends(get_db),
):
    """Delete all generated viva questions and reset progress for a project."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    VivaService.delete_questions(db=db, project_id=project_id)
    return {"message": "Viva questions cleared successfully.", "projectId": project_id}

