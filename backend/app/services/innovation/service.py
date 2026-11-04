"""Business logic and database persistence for Phase 7B Innovation Analyzer.

Orchestrates idempotent analysis execution, transactional persistence of
project profiles and cohort matches, and fast retrieval without LLM invocation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.innovation import (
    ProjectInnovationAnalysis,
    ProjectInnovationMatch,
)
from app.schemas.innovation import (
    InnovationAnalysisResponse,
    InnovationMatchSchema,
    InnovationProfileSchema,
)
from app.services.innovation.analyzer import (
    InnovationAnalyzer,
    InnovationAnalysisResult,
)
from app.services.llm.client import OpenRouterClient


class InnovationService:
    """Service layer for Innovation and Distinctiveness Analysis."""

    @classmethod
    def analyze_project(
        cls,
        db: Session,
        project_id: str,
        client: Optional[OpenRouterClient] = None,
        call_llm: bool = True,
    ) -> InnovationAnalysisResponse:
        """Run or re-run innovation analysis and persist results idempotently."""
        # Run pipeline
        result = InnovationAnalyzer.analyze(
            db=db, project_id=project_id, client=client, call_llm=call_llm
        )

        # Transactional idempotent persistence: delete previous analyses for this project
        existing = (
            db.query(ProjectInnovationAnalysis)
            .filter(ProjectInnovationAnalysis.project_id == project_id)
            .all()
        )
        for prev in existing:
            db.delete(prev)
        db.flush()

        # Insert new analysis record
        now = datetime.now(timezone.utc)
        record = ProjectInnovationAnalysis(
            project_id=project_id,
            analysis_status=result.analysis_status,
            advisory_category=result.advisory_category,
            project_profile=result.profile.to_dict(),
            cohort_size=result.cohort_size,
            comparison_method=result.comparison_method,
            dimension_scores=result.dimension_scores,
            limitations=result.limitations,
            rules_version=result.rules_version,
            llm_provider=result.llm_provider,
            llm_model=result.llm_model,
            llm_interpretation_status=result.llm_interpretation_status,
            structured_interpretation=result.structured_interpretation or {},
            created_at=now,
            updated_at=now,
        )
        db.add(record)
        db.flush()

        # Insert match records
        for m in result.matches:
            match_row = ProjectInnovationMatch(
                analysis_id=record.id,
                project_id=project_id,
                compared_project_id=m["compared_project_id"],
                problem_similarity=m["problem_similarity"],
                solution_similarity=m["solution_similarity"],
                feature_similarity=m["feature_similarity"],
                technology_overlap=m["technology_overlap"],
                technical_approach_similarity=m["technical_approach_similarity"],
                overall_similarity=m["overall_similarity"],
                difference_summary=m["difference_summary"],
                evidence_references=m["evidence_references"],
                created_at=now,
            )
            db.add(match_row)

        db.commit()
        db.refresh(record)

        return cls._serialize_analysis(record)

    @classmethod
    def get_latest_analysis(
        cls, db: Session, project_id: str
    ) -> Optional[InnovationAnalysisResponse]:
        """Retrieve the latest saved innovation analysis (no LLM call)."""
        record = (
            db.query(ProjectInnovationAnalysis)
            .filter(ProjectInnovationAnalysis.project_id == project_id)
            .order_by(ProjectInnovationAnalysis.created_at.desc())
            .first()
        )
        if not record:
            return None
        return cls._serialize_analysis(record)

    # ------------------------------------------------------------------
    # Serialization Helper
    # ------------------------------------------------------------------

    @classmethod
    def _serialize_analysis(
        cls, record: ProjectInnovationAnalysis
    ) -> InnovationAnalysisResponse:
        """Convert ORM record into response schema."""
        matches_out: List[InnovationMatchSchema] = []
        for m in (record.matches or []):
            compared_title = m.compared_project_id
            if m.compared_project:
                compared_title = m.compared_project.title or m.compared_project_id

            matches_out.append(
                InnovationMatchSchema(
                    comparedProjectId=m.compared_project_id,
                    comparedProjectTitle=compared_title,
                    problemSimilarity=m.problem_similarity,
                    solutionSimilarity=m.solution_similarity,
                    featureSimilarity=m.feature_similarity,
                    technologyOverlap=m.technology_overlap,
                    technicalApproachSimilarity=m.technical_approach_similarity,
                    overallSimilarity=m.overall_similarity,
                    differenceSummary=m.difference_summary,
                    evidenceReferences=m.evidence_references or [],
                )
            )

        profile_schema = InnovationProfileSchema.model_validate(
            record.project_profile or {}
        )

        return InnovationAnalysisResponse(
            id=record.id,
            projectId=record.project_id,
            analysisStatus=record.analysis_status,
            advisoryCategory=record.advisory_category,
            profile=profile_schema,
            cohortSize=record.cohort_size,
            comparisonMethod=record.comparison_method,
            matches=matches_out,
            dimensionScores=record.dimension_scores or {},
            limitations=record.limitations or [],
            rulesVersion=record.rules_version,
            llmProvider=record.llm_provider,
            llmModel=record.llm_model,
            llmInterpretationStatus=record.llm_interpretation_status,
            structuredInterpretation=record.structured_interpretation or {},
            createdAt=record.created_at,
            updatedAt=record.updated_at,
        )

