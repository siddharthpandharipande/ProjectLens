"""Multi-module analysis orchestrator for ProjectLens overall evaluation (Final Phase).

Consolidates real results across Code Quality, Similarity, Documentation,
Git History, Innovation Analyzer, AI Assistance, and Viva Preparation.
"""

import logging
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectStructure
from app.models.code_quality import ProjectQualityAnalysis
from app.models.similarity import ProjectSimilarityAnalysis
from app.models.documentation import ProjectDocumentationAnalysis
from app.models.git_history import ProjectGitHistoryAnalysis
from app.models.innovation import ProjectInnovationAnalysis
from app.models.ai_assistance import ProjectAIAssistanceAnalysis
from app.models.viva import ProjectVivaQuestionSet

from app.schemas.evaluation import (
    CategoryScoreSchema,
    ActionableRecommendationSchema,
)
from app.services.evaluation.scoring import (
    CATEGORY_DISPLAY_NAMES,
    DEFAULT_CATEGORY_WEIGHTS,
)

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Gathers and consolidates results from all existing ProjectLens modules."""

    @classmethod
    def consolidate_project_evidence(
        cls,
        db: Session,
        project_id: str,
    ) -> Dict[str, Any]:
        """Collect all existing module analyses and synthesize category scores and findings."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        structure = getattr(project, "structure", None)
        files_list = project.files or []
        file_count = len(files_list)

        # 1. Fetch analysis records from DB
        cq = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .order_by(ProjectQualityAnalysis.created_at.desc())
            .first()
        )
        sim = (
            db.query(ProjectSimilarityAnalysis)
            .filter(ProjectSimilarityAnalysis.project_id == project_id)
            .order_by(ProjectSimilarityAnalysis.created_at.desc())
            .first()
        )
        doc = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )
        git_hist = (
            db.query(ProjectGitHistoryAnalysis)
            .filter(ProjectGitHistoryAnalysis.project_id == project_id)
            .order_by(ProjectGitHistoryAnalysis.created_at.desc())
            .first()
        )
        innov = (
            db.query(ProjectInnovationAnalysis)
            .filter(ProjectInnovationAnalysis.project_id == project_id)
            .order_by(ProjectInnovationAnalysis.created_at.desc())
            .first()
        )
        ai_assist = (
            db.query(ProjectAIAssistanceAnalysis)
            .filter(ProjectAIAssistanceAnalysis.project_id == project_id)
            .order_by(ProjectAIAssistanceAnalysis.created_at.desc())
            .first()
        )
        viva_set = (
            db.query(ProjectVivaQuestionSet)
            .filter(ProjectVivaQuestionSet.project_id == project_id)
            .order_by(ProjectVivaQuestionSet.created_at.desc())
            .first()
        )

        # 2. Build Category Scores
        category_scores: List[CategoryScoreSchema] = []
        module_statuses: Dict[str, str] = {}
        strengths: List[str] = []
        weaknesses: List[str] = []
        risks: List[str] = []
        recommendations: List[ActionableRecommendationSchema] = []

        # Category 1: Code Quality & Architecture (30%)
        cq_schema = cls._assess_code_quality(cq)
        category_scores.append(cq_schema)
        module_statuses["code_quality"] = "completed" if cq else "not_started"
        if cq and cq.score is not None:
            if cq.score >= 75.0:
                strengths.append(f"Strong code quality baseline: score {cq.score:.1f}/100 with manageable complexity.")
            else:
                weaknesses.append(f"Code maintainability score is {cq.score:.1f}/100 with identified refactoring opportunities.")
            metrics = cq.metrics_summary or {}
            avg_cc = metrics.get("avg_complexity")
            if avg_cc is not None and avg_cc > 10.0:
                risks.append(f"High average cyclomatic complexity ({avg_cc:.1f}) elevates defect risk.")

        # Category 2: Originality & Similarity Screening (15%)
        sim_schema = cls._assess_similarity(sim)
        category_scores.append(sim_schema)
        module_statuses["similarity"] = (
            "completed" if (sim and sim.status != "not_started") else "not_started"
        )
        if sim and sim.highest_similarity_score is not None:
            if sim.highest_similarity_score <= 20.0:
                strengths.append(f"High project originality: cohort similarity screened at low {sim.highest_similarity_score:.1f}%.")
            elif sim.highest_similarity_score > 50.0:
                risks.append(f"Moderate-to-high cohort similarity ({sim.highest_similarity_score:.1f}%) observed; oral defense recommended.")

        # Category 3: Documentation & Claim Verification (20%)
        doc_schema = cls._assess_documentation(doc)
        category_scores.append(doc_schema)
        module_statuses["documentation"] = "completed" if doc else "not_started"
        if doc and doc.preliminary_score is not None:
            if doc.preliminary_score >= 70.0:
                sec_count = doc.recognized_sections_count if doc.recognized_sections_count is not None else 0
                strengths.append(f"Comprehensive documentation: score {doc.preliminary_score:.1f}/100 across {sec_count} sections.")
            else:
                weaknesses.append("Documentation coverage is incomplete or missing standard architectural specifications.")

        # Category 4: Development History & Version Control (10%)
        git_schema = cls._assess_git_history(git_hist)
        category_scores.append(git_schema)
        module_statuses["git_history"] = (
            "completed" if (git_hist and git_hist.availability == "available") else ("unavailable" if git_hist else "not_started")
        )
        if git_hist and git_hist.availability == "available":
            commits = git_hist.total_commits if git_hist.total_commits is not None else 0
            days = git_hist.duration_days if git_hist.duration_days is not None else 0.0
            strengths.append(f"Active version control history: {commits} commits over {days:.1f} days.")
        else:
            weaknesses.append("No readable Git repository history discovered in archive submission.")

        # Category 5: Innovation & Technical Contribution (15%)
        innov_schema = cls._assess_innovation(innov)
        category_scores.append(innov_schema)
        module_statuses["innovation"] = "completed" if innov else "not_started"
        if innov:
            structured = innov.structured_interpretation or {}
            for s in (structured.get("innovation_strengths") or [])[:2]:
                strengths.append(str(s))
            for m in (structured.get("missing_evidence") or [])[:2]:
                weaknesses.append(str(m))

        # Category 6: Engineering Rigor & Viva Readiness (10%)
        has_tests = any(
            f.relative_path and ("test" in f.relative_path.lower() or "spec" in f.relative_path.lower())
            for f in files_list
            if getattr(f, "relative_path", None)
        )
        has_viva = bool(viva_set and viva_set.questions)
        module_statuses["viva"] = "completed" if has_viva else "not_started"
        module_statuses["ai_assistance"] = "completed" if ai_assist else "not_started"

        eng_schema = cls._assess_engineering_readiness(has_tests, has_viva, ai_assist)
        category_scores.append(eng_schema)

        if has_tests:
            strengths.append("Automated test suite or test specifications present in repository.")
        else:
            weaknesses.append("No dedicated automated test suite or unit tests detected.")
            risks.append("Absence of automated tests increases risk of undetected runtime regression.")

        # Consolidate Recommendations from AI Assistance & Quality Findings
        if ai_assist and ai_assist.structured_interpretation:
            findings_data = ai_assist.structured_interpretation.get("findings", [])
            for f in findings_data[:4]:
                recommendations.append(
                    ActionableRecommendationSchema(
                        title=f.get("title", "Quality Improvement"),
                        description=f.get("description", ""),
                        priority=f.get("priority", "Medium"),
                        category=f.get("category", "General"),
                        whyItMatters=f.get("why_it_matters") or f.get("whyItMatters", "Important for system maintainability."),
                        recommendedAction=f.get("recommended_action") or f.get("recommendedAction", "Review code."),
                        expectedBenefit=f.get("expected_benefit") or f.get("expectedBenefit", "Improves software quality."),
                        sourceModule=f.get("source_reference") or f.get("sourceReference", "AI Assistance"),
                    )
                )

        if not recommendations:
            recommendations.append(
                ActionableRecommendationSchema(
                    title="Implement Automated Regression Tests",
                    description="Introduce unit tests covering primary business logic and controller endpoints.",
                    priority="High",
                    category="Testing",
                    whyItMatters="Ensures functional correctness without manual intervention.",
                    recommendedAction="Add pytest/jest test suites for core application handlers.",
                    expectedBenefit="Demonstrates engineering rigor and guarantees baseline correctness.",
                    sourceModule="Code Quality Analyzer",
                )
            )

        # Fallback default strengths/weaknesses if empty
        if not strengths:
            strengths.append(f"Successfully processed project submission comprising {file_count} tracked files.")
        if not weaknesses:
            weaknesses.append("Submission requires faculty viva questioning to substantiate design decisions.")

        # Build clean executive summary
        summary = (
            f"Consolidated faculty evaluation for project '{project.title or project_id}'. "
            f"Analysis reviewed {file_count} repository files across code quality, documentation, "
            f"similarity screening, and innovation dimensions."
        )

        return {
            "project": project,
            "category_scores": category_scores,
            "module_statuses": module_statuses,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "risks": risks,
            "recommendations": recommendations,
            "executive_summary": summary,
            "cq": cq,
            "sim": sim,
            "doc": doc,
            "git_hist": git_hist,
            "innov": innov,
            "ai_assist": ai_assist,
            "viva_set": viva_set,
        }

    # ------------------------------------------------------------------
    # Category Assessment Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _assess_code_quality(cls, cq: Optional[ProjectQualityAnalysis]) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["code_quality"]
        name = CATEGORY_DISPLAY_NAMES["code_quality"]
        if not cq:
            return CategoryScoreSchema(
                id="code_quality",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="Code quality analysis has not been run.",
            )
        if cq.status != "completed" or cq.score is None:
            return CategoryScoreSchema(
                id="code_quality",
                name=name,
                score=None,
                weight=weight,
                status="insufficient_evidence",
                reason=cq.score_explanation or "Insufficient source code for static quality evaluation.",
            )
        metrics = cq.metrics_summary or {}
        return CategoryScoreSchema(
            id="code_quality",
            name=name,
            score=cq.score,
            weight=weight,
            status="assessed",
            metrics={
                "linesOfCode": metrics.get("total_sloc", 0),
                "classes": metrics.get("total_classes", 0),
                "avgComplexity": metrics.get("avg_complexity", 1.0),
                "maintainability": metrics.get("maintainability_rating", "N/A"),
            },
        )

    @classmethod
    def _assess_similarity(cls, sim: Optional[ProjectSimilarityAnalysis]) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["similarity"]
        name = CATEGORY_DISPLAY_NAMES["similarity"]
        if not sim or sim.status == "not_started":
            return CategoryScoreSchema(
                id="similarity",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="Similarity analysis has not been run or no cohort comparison is available.",
            )
        if sim.status == "no_candidates":
            # Sole project in cohort: award neutral baseline 100
            return CategoryScoreSchema(
                id="similarity",
                name=name,
                score=100.0,
                weight=weight,
                status="assessed",
                reason="No other projects in cohort for comparison.",
                metrics={"highestSimilarity": 0.0},
            )
        highest_sim = sim.highest_similarity_score or 0.0
        # Transform similarity percentage into originality score
        # Higher similarity means lower originality score
        if highest_sim <= 15.0:
            originality_score = 100.0
        else:
            originality_score = max(0.0, 100.0 - (highest_sim - 15.0) * 1.15)
        return CategoryScoreSchema(
            id="similarity",
            name=name,
            score=round(originality_score, 1),
            weight=weight,
            status="assessed",
            metrics={"highestSimilarity": highest_sim, "comparedProjects": sim.compared_projects_count},
        )

    @classmethod
    def _assess_documentation(cls, doc: Optional[ProjectDocumentationAnalysis]) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["documentation"]
        name = CATEGORY_DISPLAY_NAMES["documentation"]
        if not doc or doc.status == "not_started":
            return CategoryScoreSchema(
                id="documentation",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="Documentation analysis has not been run.",
            )
        if doc.status == "insufficient_evidence" or doc.preliminary_score is None:
            return CategoryScoreSchema(
                id="documentation",
                name=name,
                score=None,
                weight=weight,
                status="insufficient_evidence",
                reason="Insufficient documentation files in project archive.",
            )
        return CategoryScoreSchema(
            id="documentation",
            name=name,
            score=doc.preliminary_score,
            weight=weight,
            status="assessed",
            metrics={
                "totalWords": doc.total_words_count,
                "recognizedSections": doc.recognized_sections_count,
                "totalDocuments": doc.total_documents_count,
            },
        )

    @classmethod
    def _assess_git_history(cls, git_hist: Optional[ProjectGitHistoryAnalysis]) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["git_history"]
        name = CATEGORY_DISPLAY_NAMES["git_history"]
        if not git_hist:
            return CategoryScoreSchema(
                id="git_history",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="Git development history analysis has not been run.",
            )
        if git_hist.availability != "available" or not git_hist.total_commits:
            return CategoryScoreSchema(
                id="git_history",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="No readable Git metadata in archive submission (plain ZIP export).",
            )
        # Compute version control score from commits and cadence
        commits = git_hist.total_commits or 1
        duration = git_hist.duration_days or 0.0
        # Normalization: > 10 commits and spread over > 5 days gives high score
        score = min(100.0, 50.0 + min(30.0, commits * 1.5) + min(20.0, duration * 2.0))
        return CategoryScoreSchema(
            id="git_history",
            name=name,
            score=round(score, 1),
            weight=weight,
            status="assessed",
            metrics={"totalCommits": commits, "durationDays": duration},
        )

    @classmethod
    def _assess_innovation(cls, innov: Optional[ProjectInnovationAnalysis]) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["innovation"]
        name = CATEGORY_DISPLAY_NAMES["innovation"]
        if not innov or getattr(innov, "analysis_status", "not_started") == "not_started":
            return CategoryScoreSchema(
                id="innovation",
                name=name,
                score=None,
                weight=weight,
                status="unavailable",
                reason="Innovation analysis has not been run.",
            )
        dims = innov.dimension_scores or {}
        valid_scores = [float(v) for v in dims.values() if v is not None and isinstance(v, (int, float))]
        if valid_scores:
            avg_score = sum(valid_scores) / len(valid_scores)
            return CategoryScoreSchema(
                id="innovation",
                name=name,
                score=round(avg_score, 1),
                weight=weight,
                status="assessed",
                metrics={"dimensionScores": dims},
            )
        # If dimensions are insufficient evidence, score is None
        return CategoryScoreSchema(
            id="innovation",
            name=name,
            score=None,
            weight=weight,
            status="insufficient_evidence",
            reason="Insufficient evidence in documentation claims for innovation scoring.",
        )

    @classmethod
    def _assess_engineering_readiness(
        cls,
        has_tests: bool,
        has_viva: bool,
        ai_assist: Optional[ProjectAIAssistanceAnalysis],
    ) -> CategoryScoreSchema:
        weight = DEFAULT_CATEGORY_WEIGHTS["engineering_readiness"]
        name = CATEGORY_DISPLAY_NAMES["engineering_readiness"]
        score = 60.0
        if has_tests:
            score += 25.0
        if has_viva:
            score += 15.0
        if ai_assist and ai_assist.advisory_category in ("Few Observable Signals", "Standard Verification"):
            score += 5.0
        score = min(100.0, score)
        return CategoryScoreSchema(
            id="engineering_readiness",
            name=name,
            score=round(score, 1),
            weight=weight,
            status="assessed",
            metrics={"hasAutomatedTests": has_tests, "vivaPrepared": has_viva},
        )
