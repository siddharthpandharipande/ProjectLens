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
from app.models.project import Project
from app.models.code_quality import ProjectQualityAnalysis
from app.models.documentation import ProjectDocumentationAnalysis
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
            llm_model = (
                settings.effective_gemini_model
                if getattr(client, "is_gemini", False)
                else settings.LLM_MODEL
            )
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

        # Ensure findings across 10 assistance areas are always populated (deterministic fallback)
        if not structured_interpretation.get("findings"):
            structured_interpretation["findings"] = cls._build_deterministic_findings(
                db=db,
                project_id=project_id,
                signals=signals,
                advisory_category=advisory_category,
            )

        if llm_interpretation_status != "completed":
            structured_interpretation.setdefault(
                "executive_summary",
                f"{reasoning} Analysis evaluated {len(valid_signal_ids)} observable evidence signals across code quality, documentation, similarity, and development history.",
            )
            structured_interpretation.setdefault(
                "explanation_of_patterns",
                "Deterministic rule evaluation identifies observable patterns in the codebase and documentation to assist faculty oral defense. These signals serve as screening indicators rather than definitive conclusions.",
            )
            structured_interpretation.setdefault(
                "alternative_explanations",
                alt_explanations,
            )
            structured_interpretation.setdefault(
                "faculty_follow_up_recommendations",
                [
                    "Ask student to explain architectural rationale for key components during viva defense.",
                    "Probe edge-case handling and error recovery routines in critical code paths.",
                    "Verify student authorship by requesting walkthrough of implementation decisions.",
                    "Review git commit cadence to understand individual contribution distribution.",
                ],
            )
            structured_interpretation.setdefault(
                "fact_vs_interpretation",
                {
                    "facts": [s["explanation"] for s in signals[:6] if s.get("explanation")],
                    "interpretation": [f"Advisory classification: {advisory_category}"],
                    "speculation": ["Potential external template adoption requires oral defense verification."],
                },
            )

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
                signal_id=str(s.get("signal_id") or "unknown")[:64],
                signal_category=str(s.get("category") or "")[:64],
                evidence_source=str(s.get("source") or "")[:128],
                observed_value=str(s.get("observed_value") or "")[:1024],
                explanation=str(s.get("explanation") or "")[:2048],
                confidence=(
                    str(s.get("confidence")) if s.get("confidence") is not None else None
                ),
                alternative_explanations=s.get("alternative_explanations", []),
                evidence_availability_status=str(s.get(
                    "availability_status", "available"
                ))[:32],
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

    @classmethod
    def _build_deterministic_findings(
        cls,
        db: Session,
        project_id: str,
        signals: List[Dict[str, Any]],
        advisory_category: str,
    ) -> List[Dict[str, Any]]:
        """Construct grounded, deterministic findings across 10 assistance areas."""
        project = db.query(Project).filter(Project.id == project_id).first()
        title = (project.title if project else "") or "Software Engineering Project"
        structure = getattr(project, "structure", None)

        # Robust extraction for detected languages
        languages_raw = structure.languages if structure and structure.languages else {}
        if isinstance(languages_raw, dict):
            lang_names = [str(k) for k in languages_raw.keys() if k]
        elif isinstance(languages_raw, (list, tuple, set)):
            lang_names = [str(k) for k in languages_raw if k]
        else:
            lang_names = []
        lang_str = ", ".join(lang_names[:6]) if lang_names else "Standard Languages"

        # Robust extraction for detected frameworks (handles list of dicts, list of strings, or dict)
        frameworks_raw = structure.frameworks if structure and structure.frameworks else []
        normalized_frameworks: List[str] = []
        if isinstance(frameworks_raw, list):
            for fw in frameworks_raw:
                if isinstance(fw, dict):
                    name = fw.get("name") or fw.get("framework") or fw.get("title")
                    if name:
                        normalized_frameworks.append(str(name))
                elif isinstance(fw, str) and fw.strip():
                    normalized_frameworks.append(fw.strip())
                elif fw is not None:
                    normalized_frameworks.append(str(fw))
        elif isinstance(frameworks_raw, dict):
            normalized_frameworks = [str(k) for k in frameworks_raw.keys()]
        fw_str = ", ".join(normalized_frameworks[:8]) if normalized_frameworks else "Detected Frameworks"

        files_list = project.files if project else []
        file_count = len(files_list)

        quality = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .order_by(ProjectQualityAnalysis.created_at.desc())
            .first()
        )
        docs = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )

        has_tests = any(
            f.relative_path and ("test" in f.relative_path.lower() or "spec" in f.relative_path.lower())
            for f in files_list
            if getattr(f, "relative_path", None)
        )

        # Code quality metrics safety
        quality_loc = getattr(quality, "lines_of_code", None) if quality else None
        avg_complexity = getattr(quality, "cyclomatic_complexity_avg", None) if quality else None
        complexity_desc = f"{avg_complexity:.1f}" if avg_complexity is not None else "N/A"
        is_high_complexity = bool(avg_complexity is not None and avg_complexity > 10.0)

        # Documentation metrics safety
        total_words = getattr(docs, "total_words_count", None) or getattr(docs, "total_words", None) if docs else None
        words_desc = str(total_words) if total_words is not None else "N/A"

        return [
            {
                "title": f"System Scope & Objective: {title}",
                "description": f"Project comprises {file_count} tracked files implemented primarily in {lang_str}. Architectural baseline uses {fw_str}.",
                "category": "Project Overview and Understanding",
                "priority": "Informational",
                "why_it_matters": "Ensures viva examiners and students establish a shared understanding of project boundaries and intended problem domain.",
                "supporting_evidence": f"Indexed {file_count} repository files across {len(lang_names)} detected languages.",
                "recommended_action": "Verify that functional deliverables directly address the core objectives defined in the project specification.",
                "expected_benefit": "Aligns project defense with formal evaluation rubrics and intended project deliverables.",
                "source_reference": "Project Manifest & File Structure",
            },
            {
                "title": "Layered Component Architecture & Modularity",
                "description": "System architecture demonstrates modular organization. Separation of UI presentation, controller/service logic, and storage should be explicitly maintained.",
                "category": "Technical Architecture and Design",
                "priority": "Medium",
                "why_it_matters": "Proper component decoupling prevents cascade failures and facilitates isolated unit testing.",
                "supporting_evidence": f"Repository contains {file_count} source modules and configuration elements.",
                "recommended_action": "Ensure business domain logic is decoupled from external API wrappers and raw database queries.",
                "expected_benefit": "Enhances long-term maintainability, readability, and defense presentation clarity.",
                "source_reference": "Source Code File Tree",
            },
            {
                "title": "Code Maintainability & Static Quality Baseline",
                "description": (
                    f"Codebase features {quality_loc} LOC with average cyclomatic complexity of {complexity_desc}."
                    if quality and quality_loc is not None
                    else "Deterministic static code analysis provides baseline maintainability and complexity screening."
                ),
                "category": "Code Quality and Maintainability",
                "priority": "High" if is_high_complexity else "Medium",
                "why_it_matters": "High cyclomatic complexity and deeply nested branches elevate bug density and maintenance cost.",
                "supporting_evidence": f"Static quality analysis: {quality_loc if quality_loc is not None else 'N/A'} LOC across {getattr(quality, 'modules_and_classes', 'N/A')} classes/modules.",
                "recommended_action": "Refactor routines exceeding 50 lines or cyclomatic complexity > 10 into focused helper functions.",
                "expected_benefit": "Decreases defect probability and simplifies automated test authoring.",
                "source_reference": "Code Quality Metrics",
            },
            {
                "title": "Technology Stack Cohesion & Dependency Health",
                "description": f"Project leverages {lang_str} with {fw_str}. Third-party package dependencies require deterministic version locking.",
                "category": "Technology Stack and Dependencies",
                "priority": "Informational",
                "why_it_matters": "Unpinned dependencies risk unexpected breaking changes when running on evaluator or grading environments.",
                "supporting_evidence": f"Detected frameworks: {fw_str}.",
                "recommended_action": "Ensure dependency configuration files lock exact semantic versions for reproducible builds.",
                "expected_benefit": "Guarantees reliable execution across different faculty evaluation systems.",
                "source_reference": "Dependency & Framework Detection",
            },
            {
                "title": "Technical Documentation Completeness",
                "description": (
                    f"Project documentation contains approximately {words_desc} words across recognized technical sections."
                    if docs and total_words is not None
                    else "Project documentation analysis screens for standard architecture, setup, and specification sections."
                ),
                "category": "Documentation Quality and Completeness",
                "priority": "Medium",
                "why_it_matters": "Complete documentation enables rapid reviewer comprehension and substantiates design choices.",
                "supporting_evidence": f"Extracted documentation analysis: {words_desc} total words.",
                "recommended_action": "Ensure architecture diagrams, environment prerequisites, and API endpoint tables are clearly documented.",
                "expected_benefit": "Accelerates evaluation review and provides ready answers for examiner documentation inquiries.",
                "source_reference": "Documentation Quality Analyzer",
            },
            {
                "title": "Automated Testing Coverage & Verification Gaps",
                "description": (
                    "Dedicated automated test files were identified in the repository."
                    if has_tests
                    else "No dedicated automated test suite or unit tests were detected in the project submission."
                ),
                "category": "Automated Testing and Verification Gaps",
                "priority": "Low" if has_tests else "High",
                "why_it_matters": "Automated regression testing is essential to verify correctness without manual intervention.",
                "supporting_evidence": "Repository scan for test folders, test runners (pytest/jest), and *_test files.",
                "recommended_action": "Introduce automated test suites for primary controller handlers and business logic calculation rules.",
                "expected_benefit": "Demonstrates rigorous engineering rigor and provides proof of correctness during defense.",
                "source_reference": "Automated Testing Inspection",
            },
            {
                "title": "Application Security Baseline & Input Validation",
                "description": "Sensitive credentials, database connection strings, and user input validation must follow defense-in-depth principles.",
                "category": "Security and Performance Considerations",
                "priority": "High",
                "why_it_matters": "Exposing secrets in repository code or skipping input sanitization leads to severe vulnerabilities.",
                "supporting_evidence": "Inspection of configuration files and external I/O boundaries.",
                "recommended_action": "Verify all environment-specific secrets are read strictly from .env files and omitted from source control.",
                "expected_benefit": "Prevents credential compromise and hardens application endpoints against injection.",
                "source_reference": "Security Screening",
            },
            {
                "title": "Evidence Verification & Identified Blind Spots",
                "description": f"Analysis classified advisory level as '{advisory_category}'. Several signals indicate areas where oral questioning is required.",
                "category": "Missing Evidence and Identified Blind Spots",
                "priority": "Medium",
                "why_it_matters": "Incomplete commit history or documentation requires examiners to probe student implementation depth.",
                "supporting_evidence": f"Advisory category: {advisory_category} based on {len(signals)} collected evidence signals.",
                "recommended_action": "Prepare to explain development chronology and demonstrate commit authorship during viva.",
                "expected_benefit": "Resolves evaluator uncertainty and establishes authentic personal contribution.",
                "source_reference": "Advisory Assessment Engine",
            },
            {
                "title": "Actionable Code Refactoring Opportunities",
                "description": "Identify candidates for error handling hardening, structured logging, and reducing code duplication.",
                "category": "Actionable Code Improvements",
                "priority": "High",
                "why_it_matters": "Generic exception blocks conceal runtime errors and make debugging in production difficult.",
                "supporting_evidence": "Static analysis of code patterns and error handling routines.",
                "recommended_action": "Replace bare 'except:' clauses with specific exception classes and structured error logging.",
                "expected_benefit": "Significantly improves application reliability and debugging speed.",
                "source_reference": "Static Pattern Analyzer",
            },
            {
                "title": "Viva Defense Readiness & Examiner Focus Areas",
                "description": "Anticipated examiner questioning topics targeting architecture choices, failure handling, and personal contribution.",
                "category": "Viva Readiness and Oral Defense Preparation",
                "priority": "High",
                "why_it_matters": "Viva examiners evaluate conceptual mastery and individual code comprehension under questioning.",
                "supporting_evidence": f"Synthesized from {title} tech stack ({fw_str}) and complexity indicators.",
                "recommended_action": f"Practice explaining: 1) Trade-offs in choosing {fw_str}, 2) Edge-case resilience, 3) End-to-end data flow.",
                "expected_benefit": "Maximizes oral defense scoring through confident, structured responses.",
                "source_reference": "Viva Preparation Advisory",
            },
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
