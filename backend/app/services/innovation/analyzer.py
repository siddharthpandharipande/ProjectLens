"""Innovation analysis orchestrator for Phase 7B.

Coordinates profile extraction, cohort comparison, distinctiveness scoring,
and optional OpenRouter LLM interpretation.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.services.innovation.profile import ProjectProfile
from app.services.innovation.extractor import ProjectProfileExtractor
from app.services.innovation.cohort_comparison import CohortComparisonService
from app.services.innovation.scoring import InnovationScoringEngine, RULES_VERSION
from app.services.innovation.prompts import (
    build_innovation_user_prompt,
    LLMInnovationInterpretation,
)
from app.services.llm.client import OpenRouterClient, build_llm_error_payload
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMInvalidReferenceError,
    LLMInvalidResponseError,
    LLMModelUnavailableError,
    LLMProviderUnavailableError,
    LLMQuotaExceededError,
    LLMRateLimitError,
    LLMTimeoutError,
)

logger = logging.getLogger(__name__)


@dataclass
class InnovationAnalysisResult:
    """In-memory result of innovation analysis before database persistence."""

    project_id: str
    analysis_status: str
    advisory_category: str
    profile: ProjectProfile
    cohort_size: int
    comparison_method: str
    matches: List[Dict[str, Any]]
    dimension_scores: Dict[str, Any]
    limitations: List[str]
    rules_version: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    llm_interpretation_status: Optional[str] = None
    structured_interpretation: Dict[str, Any] = None


class InnovationAnalyzer:
    """Coordinates the deterministic and LLM innovation analysis pipeline."""

    @classmethod
    def analyze(
        cls,
        db: Session,
        project_id: str,
        client: Optional[OpenRouterClient] = None,
        call_llm: bool = True,
    ) -> InnovationAnalysisResult:
        """Execute innovation analysis for project_id."""
        # 1. Profile Extraction
        profile = ProjectProfileExtractor.extract_profile(db, project_id)

        # 2. Cohort Project Comparison
        cohort_size, comparison_method, matches = (
            CohortComparisonService.compare_project_to_cohort(db, profile)
        )

        # 3. Deterministic Distinctiveness Assessment
        advisory_category, dimension_scores, limitations = (
            InnovationScoringEngine.evaluate(profile, cohort_size, matches)
        )

        analysis_status = "completed"
        if profile.is_empty or not profile.is_sufficient:
            analysis_status = "insufficient_evidence"

        # 4. Optional LLM Interpretation
        if client is None:
            client = OpenRouterClient()

        if client and getattr(client, "is_gemini", False):
            llm_provider = settings.LLM_PROVIDER
            llm_model = settings.effective_gemini_model
        else:
            llm_provider = settings.LLM_PROVIDER
            llm_model = settings.LLM_MODEL

        llm_status: Optional[str] = "not_requested"
        structured_interp: Dict[str, Any] = {}

        if not call_llm:
            llm_status = "not_requested"
        elif not settings.LLM_ENABLED:
            llm_status = "disabled"
        else:
            if not client.is_available():
                llm_status = "disabled"
            elif profile.is_empty or not profile.is_sufficient:
                llm_status = "insufficient_evidence"
            else:
                user_prompt = build_innovation_user_prompt(
                    profile, cohort_size, matches, dimension_scores
                )
                valid_evidence_ids = (
                    [f"FEAT-{i}" for i in range(1, len(profile.features) + 1)]
                    + [f.name for f in profile.features]
                )

                try:
                    interp = client.interpret_innovation(
                        user_prompt=user_prompt,
                        valid_evidence_ids=valid_evidence_ids,
                        discard_invalid_references=True,
                    )
                    llm_status = "completed"
                    structured_interp = interp.model_dump()
                except LLMConfigurationError as exc:
                    logger.warning("Innovation LLM config error: %s", exc)
                    llm_status = "disabled"
                except (
                    LLMRateLimitError,
                    LLMQuotaExceededError,
                    LLMAuthenticationError,
                    LLMTimeoutError,
                    LLMConnectionError,
                    LLMModelUnavailableError,
                    LLMProviderUnavailableError,
                    LLMInvalidResponseError,
                    LLMInvalidReferenceError,
                    Exception,
                ) as exc:
                    logger.warning("Innovation LLM error: %s", exc)
                    llm_status = "error"
                    payload = build_llm_error_payload(exc)
                    structured_interp = {"llm_error": payload}
                    if isinstance(exc, LLMRateLimitError):
                        limitations.append(
                            f"Upstream {llm_provider.capitalize() if llm_provider else 'AI'} model was temporarily rate-limited (HTTP {payload.get('status_code') or 429}). "
                            "Deterministic distinctiveness evidence remains fully intact."
                        )
                    elif isinstance(exc, LLMTimeoutError):
                        limitations.append(f"{llm_provider.capitalize() if llm_provider else 'AI'} LLM request timed out.")
                    else:
                        limitations.append(f"LLM interpretation failed: {type(exc).__name__}.")

        if llm_status == "error":
            structured_interp.setdefault(
                "innovation_summary",
                f"Deterministic innovation analysis evaluated {profile.title} against a cohort of {cohort_size} peer projects. Advisory classification: {advisory_category} ({dimension_scores.get('confidence_classification', 'Directly Verified')}).",
            )
            structured_interp.setdefault(
                "problem_understanding",
                profile.problem_statement if profile.problem_statement and profile.problem_statement != "Not identified from the available project documents." else f"Project addresses domain needs in {profile.domain or 'Software Engineering'}.",
            )
            structured_interp.setdefault(
                "proposed_solution_understanding",
                profile.proposed_solution if profile.proposed_solution and profile.proposed_solution != "Not identified from the available project documents." else f"Implemented via {', '.join(profile.languages or ['Standard Tech Stack'])}.",
            )
            structured_interp.setdefault(
                "distinctive_elements",
                [f.name for f in profile.features if f.evidence_type in ("verified_match", "detected_implementation")][:5] or ["Modular software architecture."],
            )
            structured_interp.setdefault(
                "innovation_strengths",
                [f"Verified implementation of: {f.name}" for f in profile.features if f.evidence_type == "verified_match"] or ["Standard software engineering implementation."],
            )
            structured_interp.setdefault(
                "missing_evidence",
                [f"Unverified feature claim: {f.name}" for f in profile.features if f.evidence_type == "unverified_claim"] or ["None identified; core claimed features are supported by code."],
            )
            structured_interp.setdefault(
                "improvement_recommendations",
                [
                    "Document unit testing strategy and test results for critical features.",
                    "Provide explicit architectural block diagrams illustrating data flow.",
                    "Clarify deployment instructions and runtime environment configuration.",
                ],
            )
            structured_interp.setdefault(
                "faculty_follow_up_recommendations",
                [
                    f"Ask student to demonstrate runtime behavior of {profile.features[0].name if profile.features else 'primary feature'}.",
                    "Probe student understanding of chosen algorithm/data structures.",
                    "Verify individual contribution share in collaborative implementation tasks.",
                ],
            )
            structured_interp.setdefault(
                "confidence_classification",
                dimension_scores.get("confidence_classification", "Directly Verified"),
            )
            structured_interp.setdefault(
                "confidence_rationale",
                dimension_scores.get("confidence_rationale", "Grounded in direct static codebase and documentation analysis."),
            )

        return InnovationAnalysisResult(
            project_id=project_id,
            analysis_status=analysis_status,
            advisory_category=advisory_category,
            profile=profile,
            cohort_size=cohort_size,
            comparison_method=comparison_method,
            matches=matches,
            dimension_scores=dimension_scores,
            limitations=limitations,
            rules_version=RULES_VERSION,
            llm_provider=llm_provider if llm_status != "disabled" else None,
            llm_model=llm_model if llm_status != "disabled" else None,
            llm_interpretation_status=llm_status,
            structured_interpretation=structured_interp,
        )

