"""Viva Question Generator Service (Phase 8).

Orchestrates viva question generation, Gemini AI integration, deterministic fallback,
practice progress tracking, and database persistence.
"""

import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.viva import ProjectVivaQuestionSet, ProjectVivaQuestion, generate_question_id
from app.models.project import Project
from app.services.viva.evidence_builder import VivaEvidenceBuilder
from app.services.viva.gemini_generator import GeminiVivaGenerator
from app.services.viva.fallback_generator import FallbackVivaGenerator
from app.schemas.viva import (
    VivaQuestionSchema,
    VivaQuestionSetResponse,
    VivaProgressResponse,
    VIVA_CATEGORIES,
)
from app.config import settings

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class VivaService:
    """Service handling Viva generation, database persistence, and practice tracking."""

    @classmethod
    def generate_questions(
        cls,
        db: Session,
        project_id: str,
        mode: str = "complete_viva",
        difficulty: str = "all",
        question_count: int = 10,
        force_regenerate: bool = True,
    ) -> VivaQuestionSetResponse:
        """Generate viva questions using Gemini AI when available, with deterministic fallback."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Build comprehensive project context
        context = VivaEvidenceBuilder.build_project_context(db, project_id)

        # Attempt Gemini AI generation if configured
        raw_questions: Optional[List[Dict[str, Any]]] = None
        generation_source = "deterministic_fallback"
        model_name = None

        if GeminiVivaGenerator.is_available():
            try:
                raw_questions = GeminiVivaGenerator.generate_questions(
                    context=context,
                    mode=mode,
                    difficulty=difficulty,
                    question_count=question_count,
                )
                if raw_questions and len(raw_questions) > 0:
                    generation_source = "gemini"
                    model_name = settings.effective_gemini_model
            except Exception as exc:
                logger.warning("Gemini generation failed, falling back to deterministic: %s", exc)

        # Fallback to deterministic generation if Gemini unavailable or failed
        if not raw_questions:
            logger.info("Using deterministic fallback generator for project %s", project_id)
            raw_questions = FallbackVivaGenerator.generate_questions(
                context=context,
                mode=mode,
                difficulty=difficulty,
                question_count=question_count,
            )
            generation_source = "deterministic_fallback"
            model_name = None

        # Clean existing questions if force_regenerate is True
        if force_regenerate:
            existing_sets = (
                db.query(ProjectVivaQuestionSet)
                .filter(ProjectVivaQuestionSet.project_id == project_id)
                .all()
            )
            for s in existing_sets:
                db.delete(s)
            db.flush()

        # Create new question set
        q_set = ProjectVivaQuestionSet(
            project_id=project_id,
            mode=mode,
            generation_source=generation_source,
            model_name=model_name,
            total_questions=len(raw_questions),
            practiced_count=0,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        db.add(q_set)
        db.flush()

        # Create question entities with strict null-safe normalization
        created_questions: List[ProjectVivaQuestion] = []
        for q_data in raw_questions:
            if not isinstance(q_data, dict):
                continue

            q_text = (q_data.get("question") or "").strip()
            if not q_text:
                continue

            cat = (q_data.get("category") or "").strip()
            if cat not in VIVA_CATEGORIES:
                cat = "Project Fundamentals"

            diff = (q_data.get("difficulty") or "").strip().lower()
            if diff not in ("beginner", "intermediate", "advanced"):
                diff = "intermediate"

            rationale = (
                (q_data.get("examiner_rationale") or q_data.get("examinerRationale") or "").strip()
                or "Assesses foundational software engineering understanding."
            )

            raw_kp = q_data.get("key_points") or q_data.get("keyPoints") or []
            clean_kp: List[str] = []
            if isinstance(raw_kp, list):
                for p in raw_kp:
                    if p is not None and str(p).strip():
                        clean_kp.append(str(p).strip())
            elif isinstance(raw_kp, str) and raw_kp.strip():
                clean_kp = [raw_kp.strip()]
            if not clean_kp:
                clean_kp = ["Technical implementation details", "Design trade-offs evaluated"]

            ans = (
                (q_data.get("suggested_answer") or q_data.get("suggestedAnswer") or "").strip()
                or "Refer to the project implementation files and architecture documentation."
            )

            ev_ref = (q_data.get("evidence_reference") or q_data.get("evidenceReference") or "").strip()
            clean_ev_ref = ev_ref if ev_ref else "Project Documentation & Source Code"

            q_entity = ProjectVivaQuestion(
                id=q_data.get("id") or generate_question_id(),
                set_id=q_set.id,
                project_id=project_id,
                category=cat,
                difficulty=diff,
                question=q_text,
                examiner_rationale=rationale,
                key_points=clean_kp,
                suggested_answer=ans,
                evidence_reference=clean_ev_ref,
                is_practiced=False,
                source=generation_source,
                created_at=utc_now(),
                updated_at=utc_now(),
            )
            db.add(q_entity)
            created_questions.append(q_entity)

        db.commit()
        db.refresh(q_set)

        return cls._build_set_response(q_set, created_questions)

    @classmethod
    def get_latest_question_set(
        cls,
        db: Session,
        project_id: str,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
        is_practiced: Optional[bool] = None,
    ) -> Optional[VivaQuestionSetResponse]:
        """Retrieve the latest viva question set for a project with optional filters."""
        q_set = (
            db.query(ProjectVivaQuestionSet)
            .filter(ProjectVivaQuestionSet.project_id == project_id)
            .order_by(ProjectVivaQuestionSet.created_at.desc())
            .first()
        )
        if not q_set:
            return None

        query = db.query(ProjectVivaQuestion).filter(ProjectVivaQuestion.set_id == q_set.id)
        if category and category.lower() != "all":
            query = query.filter(func.lower(ProjectVivaQuestion.category) == category.lower())
        if difficulty and difficulty.lower() != "all":
            query = query.filter(func.lower(ProjectVivaQuestion.difficulty) == difficulty.lower())
        if is_practiced is not None:
            query = query.filter(ProjectVivaQuestion.is_practiced == is_practiced)

        questions = query.order_by(ProjectVivaQuestion.created_at.asc()).all()
        return cls._build_set_response(q_set, questions)

    @classmethod
    def update_practice_status(
        cls,
        db: Session,
        project_id: str,
        question_id: str,
        is_practiced: bool,
    ) -> VivaQuestionSchema:
        """Mark a question as practiced or unpracticed."""
        question = (
            db.query(ProjectVivaQuestion)
            .filter(
                ProjectVivaQuestion.project_id == project_id,
                ProjectVivaQuestion.id == question_id,
            )
            .first()
        )
        if not question:
            raise ValueError(f"Question '{question_id}' not found for project '{project_id}'.")

        question.is_practiced = is_practiced
        question.updated_at = utc_now()

        # Update set practiced_count
        q_set = db.query(ProjectVivaQuestionSet).filter(ProjectVivaQuestionSet.id == question.set_id).first()
        if q_set:
            count = (
                db.query(ProjectVivaQuestion)
                .filter(
                    ProjectVivaQuestion.set_id == q_set.id,
                    ProjectVivaQuestion.is_practiced.is_(True),
                )
                .count()
            )
            q_set.practiced_count = count
            q_set.updated_at = utc_now()

        db.commit()
        db.refresh(question)
        return VivaQuestionSchema.model_validate(question)

    @classmethod
    def regenerate_single_question(
        cls,
        db: Session,
        project_id: str,
        question_id: str,
    ) -> VivaQuestionSchema:
        """Regenerate a single question while keeping its category and difficulty."""
        question = (
            db.query(ProjectVivaQuestion)
            .filter(
                ProjectVivaQuestion.project_id == project_id,
                ProjectVivaQuestion.id == question_id,
            )
            .first()
        )
        if not question:
            raise ValueError(f"Question '{question_id}' not found.")

        # Get existing question texts in this set to avoid duplicates
        existing_qs = [
            q.question
            for q in db.query(ProjectVivaQuestion.question)
            .filter(ProjectVivaQuestion.project_id == project_id)
            .all()
        ]

        context = VivaEvidenceBuilder.build_project_context(db, project_id)

        new_data: Optional[Dict[str, Any]] = None
        source = "deterministic_fallback"

        if GeminiVivaGenerator.is_available():
            try:
                new_data = GeminiVivaGenerator.regenerate_single_question(
                    context=context,
                    category=question.category,
                    difficulty=question.difficulty,
                    existing_questions=existing_qs,
                )
                if new_data and new_data.get("question"):
                    source = "gemini"
            except Exception as exc:
                logger.warning("Single question Gemini regeneration failed: %s", exc)

        if not new_data:
            # Fallback single question generator
            pool = FallbackVivaGenerator.generate_questions(
                context=context,
                mode="complete_viva",
                difficulty=question.difficulty,
                question_count=15,
            )
            # Find an unused question matching category or difficulty
            for candidate in pool:
                if candidate["question"] not in existing_qs:
                    new_data = candidate
                    break
            if not new_data and pool:
                new_data = pool[0]

        if new_data:
            new_q = (new_data.get("question") or "").strip()
            if new_q:
                question.question = new_q
            new_rat = (new_data.get("examiner_rationale") or new_data.get("examinerRationale") or "").strip()
            if new_rat:
                question.examiner_rationale = new_rat
            raw_kp = new_data.get("key_points") or new_data.get("keyPoints")
            if raw_kp:
                clean_kp = [str(p).strip() for p in raw_kp if p is not None and str(p).strip()]
                if clean_kp:
                    question.key_points = clean_kp
            new_ans = (new_data.get("suggested_answer") or new_data.get("suggestedAnswer") or "").strip()
            if new_ans:
                question.suggested_answer = new_ans
            new_ref = (new_data.get("evidence_reference") or new_data.get("evidenceReference") or "").strip()
            if new_ref:
                question.evidence_reference = new_ref
            question.source = source
            question.updated_at = utc_now()
            db.commit()
            db.refresh(question)

        return VivaQuestionSchema.model_validate(question)

    @classmethod
    def get_progress(cls, db: Session, project_id: str) -> VivaProgressResponse:
        """Calculate practice progress and category breakdown."""
        q_set = (
            db.query(ProjectVivaQuestionSet)
            .filter(ProjectVivaQuestionSet.project_id == project_id)
            .order_by(ProjectVivaQuestionSet.created_at.desc())
            .first()
        )
        if not q_set:
            return VivaProgressResponse(
                projectId=project_id,
                totalQuestions=0,
                practicedCount=0,
                percentage=0.0,
                byCategory={},
                byDifficulty={},
                generationSource="gemini",
                lastGeneratedAt=None,
            )

        questions = (
            db.query(ProjectVivaQuestion)
            .filter(ProjectVivaQuestion.set_id == q_set.id)
            .all()
        )

        total = len(questions)
        practiced = sum(1 for q in questions if q.is_practiced)
        pct = round((practiced / total) * 100, 1) if total > 0 else 0.0

        by_cat: Dict[str, Dict[str, int]] = {}
        by_diff: Dict[str, Dict[str, int]] = {
            "beginner": {"total": 0, "practiced": 0},
            "intermediate": {"total": 0, "practiced": 0},
            "advanced": {"total": 0, "practiced": 0},
        }

        for cat in VIVA_CATEGORIES:
            by_cat[cat] = {"total": 0, "practiced": 0}

        for q in questions:
            cat = q.category
            if cat not in by_cat:
                by_cat[cat] = {"total": 0, "practiced": 0}
            by_cat[cat]["total"] += 1
            if q.is_practiced:
                by_cat[cat]["practiced"] += 1

            diff = (q.difficulty or "intermediate").lower()
            if diff in by_diff:
                by_diff[diff]["total"] += 1
                if q.is_practiced:
                    by_diff[diff]["practiced"] += 1

        return VivaProgressResponse(
            projectId=project_id,
            totalQuestions=total,
            practicedCount=practiced,
            percentage=pct,
            byCategory=by_cat,
            byDifficulty=by_diff,
            generationSource=q_set.generation_source,
            lastGeneratedAt=q_set.created_at,
        )

    @classmethod
    def delete_questions(cls, db: Session, project_id: str) -> None:
        """Delete all generated viva question sets and questions for a project."""
        sets = (
            db.query(ProjectVivaQuestionSet)
            .filter(ProjectVivaQuestionSet.project_id == project_id)
            .all()
        )
        for s in sets:
            db.delete(s)
        db.commit()

    @classmethod
    def _build_set_response(
        cls,
        q_set: ProjectVivaQuestionSet,
        questions: List[ProjectVivaQuestion],
    ) -> VivaQuestionSetResponse:
        """Serialize question set and question list to schema response."""
        q_schemas = [VivaQuestionSchema.model_validate(q) for q in questions]
        return VivaQuestionSetResponse(
            id=q_set.id,
            projectId=q_set.project_id,
            mode=q_set.mode,
            generationSource=q_set.generation_source,
            modelName=q_set.model_name,
            totalQuestions=q_set.total_questions,
            practicedCount=q_set.practiced_count,
            questions=q_schemas,
            createdAt=q_set.created_at,
            updatedAt=q_set.updated_at,
        )

