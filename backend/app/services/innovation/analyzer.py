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
        llm_provider = settings.LLM_PROVIDER
        llm_model = settings.LLM_MODEL
        llm_status: Optional[str] = "not_requested"
        structured_interp: Dict[str, Any] = {}

        if not call_llm:
            llm_status = "not_requested"
        elif not settings.LLM_ENABLED:
            llm_status = "disabled"
        else:
            if client is None:
                client = OpenRouterClient()

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
                            "Upstream OpenRouter free model was temporarily rate-limited (HTTP 429). "
                            "Deterministic distinctiveness evidence remains fully intact."
                        )
                    elif isinstance(exc, LLMTimeoutError):
                        limitations.append("OpenRouter LLM request timed out.")
                    else:
                        limitations.append(f"LLM interpretation failed: {type(exc).__name__}.")

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

