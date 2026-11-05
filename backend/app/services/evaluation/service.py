"""Business service for ProjectLens overall evaluation and report generation (Final Phase).

Orchestrates multi-module consolidation, scoring calculation, database persistence,
and PDF/JSON report generation.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.evaluation import ProjectEvaluation
from app.schemas.evaluation import (
    ProjectEvaluationResponse,
    CategoryScoreSchema,
    ActionableRecommendationSchema,
    ScoreBreakdownItem,
)
from app.services.evaluation.orchestrator import EvaluationOrchestrator
from app.services.evaluation.scoring import EvaluationScoringEngine
from app.services.evaluation.report_generator import EvaluationReportGenerator

logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """Sanitize filename to prevent directory traversal or filesystem illegal characters."""
    s = re.sub(r'[\\/*?:"<>|]', "", name).strip()
    s = re.sub(r"\s+", "_", s)
    return s[:64] or "project"


class EvaluationService:
    """Consolidated evaluation and report service."""

    @classmethod
    def evaluate_project(
        cls,
        db: Session,
        project_id: str,
    ) -> ProjectEvaluationResponse:
        """Run overall project evaluation across all modules, persist, and update project score."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # 1. Consolidate evidence
        data = EvaluationOrchestrator.consolidate_project_evidence(db, project_id)

        # 2. Compute overall scoring
        overall_score, grade, status_val, coverage_pct, updated_cats, breakdown = (
            EvaluationScoringEngine.calculate_overall_evaluation(data["category_scores"])
        )

        data["overall_score"] = overall_score
        data["grade"] = grade
        data["evaluation_status"] = status_val
        data["coverage_pct"] = coverage_pct
        data["category_scores"] = updated_cats

        # 3. Idempotently persist ProjectEvaluation
        existing = (
            db.query(ProjectEvaluation)
            .filter(ProjectEvaluation.project_id == project_id)
            .order_by(ProjectEvaluation.created_at.desc())
            .first()
        )

        cat_scores_dump = [c.model_dump() for c in updated_cats]
        recs_dump = [r.model_dump(by_alias=True) for r in data["recommendations"]]

        if existing:
            existing.overall_score = overall_score
            existing.grade = grade
            existing.evaluation_status = status_val
            existing.coverage_pct = coverage_pct
            existing.category_scores = cat_scores_dump
            existing.strengths = data["strengths"]
            existing.weaknesses = data["weaknesses"]
            existing.risks = data["risks"]
            existing.recommendations = recs_dump
            existing.module_statuses = data["module_statuses"]
            existing.executive_summary = data["executive_summary"]
            existing.updated_at = datetime.now(timezone.utc)
            eval_record = existing
        else:
            eval_record = ProjectEvaluation(
                project_id=project_id,
                overall_score=overall_score,
                grade=grade,
                evaluation_status=status_val,
                coverage_pct=coverage_pct,
                category_scores=cat_scores_dump,
                strengths=data["strengths"],
                weaknesses=data["weaknesses"],
                risks=data["risks"],
                recommendations=recs_dump,
                module_statuses=data["module_statuses"],
                executive_summary=data["executive_summary"],
            )
            db.add(eval_record)

        # 4. Update Project.score for global header and project card display
        if overall_score is not None:
            project.score = overall_score
        db.commit()
        db.refresh(eval_record)
        db.refresh(project)

        return cls._to_response(eval_record, breakdown)

    @classmethod
    def get_latest_evaluation(
        cls,
        db: Session,
        project_id: str,
    ) -> Optional[ProjectEvaluationResponse]:
        """Retrieve latest saved evaluation for a project."""
        eval_record = (
            db.query(ProjectEvaluation)
            .filter(ProjectEvaluation.project_id == project_id)
            .order_by(ProjectEvaluation.created_at.desc())
            .first()
        )
        if not eval_record:
            return None

        # Reconstruct score breakdown
        breakdown = [
            ScoreBreakdownItem(
                dimension=c.get("name") or c.get("title") or c.get("id") or "Category",
                score=float(c.get("score") if c.get("score") is not None else (c.get("raw_score") or 0.0)),
                maxScore=100.0,
                notes=f"Weight: {c.get('weight', 0)}% | Contribution: {round(float(c.get('contribution') or c.get('weighted_score') or 0.0), 1)} pts",
            )
            for c in (eval_record.category_scores or [])
        ]
        return cls._to_response(eval_record, breakdown)

    @classmethod
    def generate_pdf(
        cls,
        db: Session,
        project_id: str,
    ) -> Tuple[bytes, str]:
        """Generate PDF report bytes and clean safe filename."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Ensure evaluation exists
        data = EvaluationOrchestrator.consolidate_project_evidence(db, project_id)
        overall_score, grade, status_val, coverage_pct, updated_cats, _ = (
            EvaluationScoringEngine.calculate_overall_evaluation(data["category_scores"])
        )
        data["overall_score"] = overall_score
        data["grade"] = grade
        data["evaluation_status"] = status_val
        data["coverage_pct"] = coverage_pct
        data["category_scores"] = updated_cats

        pdf_bytes = EvaluationReportGenerator.generate_pdf_report(data)
        safe_title = sanitize_filename(project.title or project_id)
        filename = f"{safe_title}_evaluation_report.pdf"
        return pdf_bytes, filename

    @classmethod
    def generate_json_export(
        cls,
        db: Session,
        project_id: str,
    ) -> Dict[str, Any]:
        """Generate structured JSON export for evaluation."""
        data = EvaluationOrchestrator.consolidate_project_evidence(db, project_id)
        overall_score, grade, status_val, coverage_pct, updated_cats, _ = (
            EvaluationScoringEngine.calculate_overall_evaluation(data["category_scores"])
        )
        data["overall_score"] = overall_score
        data["grade"] = grade
        data["evaluation_status"] = status_val
        data["coverage_pct"] = coverage_pct
        data["category_scores"] = updated_cats
        return EvaluationReportGenerator.generate_json_export(data)

    @classmethod
    def _to_response(
        cls,
        eval_record: ProjectEvaluation,
        breakdown: List[ScoreBreakdownItem],
    ) -> ProjectEvaluationResponse:
        cats = [CategoryScoreSchema(**c) for c in (eval_record.category_scores or [])]
        recs = [ActionableRecommendationSchema(**r) for r in (eval_record.recommendations or [])]
        return ProjectEvaluationResponse(
            id=eval_record.id,
            projectId=eval_record.project_id,
            overallScore=eval_record.overall_score,
            grade=eval_record.grade,
            evaluationStatus=eval_record.evaluation_status,
            coveragePct=eval_record.coverage_pct,
            categoryScores=cats,
            scoreBreakdown=breakdown,
            strengths=eval_record.strengths or [],
            weaknesses=eval_record.weaknesses or [],
            risks=eval_record.risks or [],
            recommendations=recs,
            moduleStatuses=eval_record.module_statuses or {},
            executiveSummary=eval_record.executive_summary,
            facultyNotes=eval_record.faculty_notes,
            scoringVersion=eval_record.scoring_version,
            reportAvailable=True,
            reportUrl=f"/api/projects/{eval_record.project_id}/report",
            createdAt=eval_record.created_at,
            updatedAt=eval_record.updated_at,
        )
