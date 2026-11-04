"""AI-Assistance Analyzer service (Phase 7A).

Orchestrates:
  1. Collecting deterministic evidence from saved Phase 3-6 results.
  2. Computing an advisory category via transparent, testable rules.
  3. Calling OpenRouter (only when LLM is enabled and configured) to interpret
     the evidence, with full validation of the response.
  4. Persisting the analysis and evidence signals to PostgreSQL idempotently.

No source code, personal identifiers, or secrets are sent to the LLM or stored.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.services.llm import (
    OpenRouterClient,
    build_llm_error_payload,
    EvidenceSummary,
    EvidenceSignal,
    LLMInterpretation,
    InterpretationStatus,
    LLMConfigurationError,
    LLMRateLimitError,
    LLMQuotaExceededError,
    LLMConnectionError,
    LLMTimeoutError,
    LLMAuthenticationError,
    LLMModelUnavailableError,
    LLMProviderUnavailableError,
    LLMInvalidResponseError,
    LLMInvalidReferenceError,
)
from app.services.ai_assistance.evidence_collector import EvidenceCollector
from app.services.ai_assistance.analyzer import AdvisoryAnalyzer
from app.models.ai_assistance import (
    ProjectAIAssistanceAnalysis,
    ProjectAIAssistanceEvidenceSignal,
)
from app.schemas.ai_assistance import (
    AIAssistanceAnalysisResponse,
    AIAssistanceSignalSchema,
)

RULES_VERSION = "v1.0-deterministic"


class AIAssistanceService:
    """Business logic for the AI-Assistance Analyzer."""

    @classmethod
    def analyze_project(
        cls,
        db: Session,
        project_id: str,
        force_llm: bool = False,
    ) -> AIAssistanceAnalysisResponse:
        """Run (or re-run) AI-assistance analysis for a project."""
        # 1. Collect deterministic evidence.
        signals = EvidenceCollector.collect_all(db, project_id)
        valid_signal_ids = [s["signal_id"] for s in signals]

        # 2. Deterministic advisory assessment.
        advisory_category, reasoning, alt_explanations = AdvisoryAnalyzer.assess(signals)

        # 3. Build evidence summary for the LLM.
        evidence_summary = cls._build_evidence_summary(
            project_id=project_id,
            signals=signals,
            advisory_category=advisory_category,
        )

        # 4. Call OpenRouter only when enabled and configured.
        llm_provider: Optional[str] = None
        llm_model: Optional[str] = None
        llm_interpretation_status: Optional[str] = None
        structured_interpretation: Dict[str, Any] = {}
        limitations: List[str] = []

        client = OpenRouterClient()
        if client.is_available():
            llm_provider = settings.LLM_PROVIDER
            llm_model = settings.LLM_MODEL
            try:
                interpretation = client.interpret_evidence(
                    evidence=evidence_summary,
                    valid_signal_ids=valid_signal_ids,
                    discard_invalid_references=True,
                )
                llm_interpretation_status = interpretation.interpretation_status
                structured_interpretation = interpretation.model_dump()
                limitations = list(interpretation.limitations or [])
            except LLMConfigurationError:
                llm_interpretation_status = "not_requested"
                limitations.append("LLM integration is not configured.")
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
                llm_interpretation_status = "error"
                payload = build_llm_error_payload(exc)
                structured_interpretation = {"llm_error": payload}
                if isinstance(exc, LLMRateLimitError):
                    limitations.append(f"LLM provider rate limit reached (HTTP {payload.get('status_code') or 429}).")
                elif isinstance(exc, LLMAuthenticationError):
                    limitations.append("LLM provider authentication failed.")
                elif isinstance(exc, LLMQuotaExceededError):
                    limitations.append("LLM provider account quota exceeded or credits depleted.")
                elif isinstance(exc, LLMTimeoutError):
                    limitations.append("LLM provider request timed out.")
                elif isinstance(exc, LLMConnectionError):
                    limitations.append("Unable to connect to LLM provider network.")
                elif isinstance(exc, LLMModelUnavailableError):
                    limitations.append("Configured LLM model is unavailable.")
                elif isinstance(exc, LLMProviderUnavailableError):
                    limitations.append("LLM provider is unavailable.")
                elif isinstance(exc, LLMInvalidResponseError):
                    limitations.append("LLM provider returned an invalid response.")
                elif isinstance(exc, LLMInvalidReferenceError):
                    limitations.append("LLM referenced evidence that was not supplied.")
                else:
                    limitations.append(f"LLM interpretation failed: {type(exc).__name__}")
        else:
            if not settings.LLM_ENABLED:
                llm_interpretation_status = "disabled"
                limitations.append("LLM integration is disabled (LLM_ENABLED=false).")
            else:
                llm_interpretation_status = "not_requested"
                limitations.append("LLM credentials are not configured.")

        # 5. Persist to PostgreSQL (idempotent).
        analysis = cls._persist(
            db=db,
            project_id=project_id,
            advisory_category=advisory_category,
            evidence_summary=evidence_summary.model_dump(),
            structured_interpretation=structured_interpretation,
            llm_provider=llm_provider,
            llm_model=llm_model,
            llm_interpretation_status=llm_interpretation_status,
            limitations=limitations,
        )

        # 6. Build and return the response.
        return cls._to_response(analysis, signals)

    @classmethod
    def get_latest_analysis(
        cls, db: Session, project_id: str
    ) -> Optional[AIAssistanceAnalysisResponse]:
        """Retrieve the latest saved AI-assistance analysis (no LLM call)."""
        analysis = (
            db.query(ProjectAIAssistanceAnalysis)
            .filter(ProjectAIAssistanceAnalysis.project_id == project_id)
            .order_by(ProjectAIAssistanceAnalysis.created_at.desc())
            .first()
        )
        if not analysis:
            return None
        # Re-collect signals from DB for the evidence_summary section.
        signals = cls._load_signals_from_db(analysis)
        return cls._to_response(analysis, signals)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @classmethod
    def _build_evidence_summary(
        cls,
        project_id: str,
        signals: List[Dict[str, Any]],
        advisory_category: str,
    ) -> EvidenceSummary:
        """Build the structured evidence summary sent to the LLM."""
        signal_models = [
            EvidenceSignal(
                signal_id=s["signal_id"],
                category=s["category"],
                source=s["source"],
                observed_value=s["observed_value"],
                explanation=s["explanation"],
                confidence=s.get("confidence"),
                alternative_explanations=s.get("alternative_explanations", []),
                availability_status=s.get("availability_status", "available"),
            )
            for s in signals
        ]
        return EvidenceSummary(
            project_id=project_id,
            signals=signal_models,
            rules_version=RULES_VERSION,
            advisory_category=advisory_category,
        )

    @classmethod
    def _persist(
        cls,
        db: Session,
        project_id: str,
        advisory_category: str,
        evidence_summary: Dict[str, Any],
        structured_interpretation: Dict[str, Any],
        llm_provider: Optional[str],
        llm_model: Optional[str],
        llm_interpretation_status: Optional[str],
        limitations: List[str],
    ) -> ProjectAIAssistanceAnalysis:
        """Idempotently save the analysis and its evidence signals."""
        # Find or create the analysis row.
        existing = (
            db.query(ProjectAIAssistanceAnalysis)
            .filter(ProjectAIAssistanceAnalysis.project_id == project_id)
            .order_by(ProjectAIAssistanceAnalysis.created_at.desc())
            .first()
        )

        if existing:
            # Update in place to keep a single row per project (idempotent).
            existing.analysis_status = "completed"
            existing.advisory_category = advisory_category
            existing.evidence_summary = evidence_summary
            existing.rules_version = RULES_VERSION
            existing.llm_provider = llm_provider
            existing.llm_model = llm_model
            existing.llm_interpretation_status = llm_interpretation_status
            existing.structured_interpretation = structured_interpretation
            existing.limitations = limitations
            # Remove old evidence signals to avoid duplicates.
            db.query(ProjectAIAssistanceEvidenceSignal).filter(
                ProjectAIAssistanceEvidenceSignal.analysis_id == existing.id
            ).delete()
            db.flush()
            analysis = existing
        else:
            analysis = ProjectAIAssistanceAnalysis(
                project_id=project_id,
                analysis_status="completed",
                advisory_category=advisory_category,
                evidence_summary=evidence_summary,
                rules_version=RULES_VERSION,
                llm_provider=llm_provider,
                llm_model=llm_model,
                llm_interpretation_status=llm_interpretation_status,
                structured_interpretation=structured_interpretation,
                limitations=limitations,
            )
            db.add(analysis)
            db.flush()

        # Persist evidence signals as child rows.
        for s in evidence_summary.get("signals", []):
            signal = ProjectAIAssistanceEvidenceSignal(
                analysis_id=analysis.id,
                signal_id=s.get("signal_id", "unknown"),
                signal_category=s.get("category", ""),
                evidence_source=s.get("source", ""),
                observed_value=s.get("observed_value", ""),
                explanation=s.get("explanation", ""),
                confidence=(
                    str(s.get("confidence")) if s.get("confidence") is not None else None
                ),
                alternative_explanations=s.get("alternative_explanations", []),
                evidence_availability_status=s.get(
                    "availability_status", "available"
                ),
            )
            db.add(signal)

        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def _load_signals_from_db(
        analysis: ProjectAIAssistanceAnalysis,
    ) -> List[Dict[str, Any]]:
        """Convert persisted evidence rows back to the public signal shape."""
        return [
            {
                "signal_id": signal.signal_id,
                "category": signal.signal_category,
                "source": signal.evidence_source,
                "observed_value": signal.observed_value,
                "explanation": signal.explanation,
                "confidence": (
                    float(signal.confidence)
                    if signal.confidence is not None
                    else None
                ),
                "alternative_explanations": signal.alternative_explanations or [],
                "availability_status": signal.evidence_availability_status,
            }
            for signal in (analysis.evidence_signals or [])
        ]

    @staticmethod
    def _to_response(
        analysis: ProjectAIAssistanceAnalysis,
        signals: List[Dict[str, Any]],
    ) -> AIAssistanceAnalysisResponse:
        """Serialize an ORM analysis and its evidence into the API contract."""
        return AIAssistanceAnalysisResponse(
            id=analysis.id,
            projectId=analysis.project_id,
            analysisStatus=analysis.analysis_status,
            advisoryCategory=analysis.advisory_category,
            evidenceSummary=signals,
            rulesVersion=analysis.rules_version,
            llmProvider=analysis.llm_provider,
            llmModel=analysis.llm_model,
            llmInterpretationStatus=analysis.llm_interpretation_status,
            structuredInterpretation=analysis.structured_interpretation or {},
            limitations=analysis.limitations or [],
            createdAt=analysis.created_at,
            updatedAt=analysis.updated_at,
        )
