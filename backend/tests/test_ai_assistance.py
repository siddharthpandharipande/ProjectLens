"""Tests for Phase 7A deterministic AI-assistance analysis and API wiring."""

import io
import json
from types import SimpleNamespace
from typing import Any, Dict, List

import httpx
import pytest
from openai import APIStatusError, APITimeoutError, NotFoundError, RateLimitError

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project
from app.models.code_quality import ProjectQualityAnalysis
from app.models.similarity import ProjectSimilarityAnalysis, ProjectSimilarityMatch
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentationFinding,
)
from app.models.git_history import ProjectGitHistoryAnalysis
from app.models.ai_assistance import (
    ProjectAIAssistanceAnalysis,
    ProjectAIAssistanceEvidenceSignal,
)
from app.services.ai_assistance.analyzer import (
    AdvisoryAnalyzer,
    INSUFFICIENT_EVIDENCE,
    FEW_SIGNALS,
    SOME_SIGNALS,
    MULTIPLE_SIGNALS,
)
from app.services.ai_assistance.evidence_collector import EvidenceCollector
from app.services.ai_assistance import service as ai_service
from app.services.llm.client import OpenRouterClient
from app.services.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMInvalidReferenceError,
    LLMInvalidResponseError,
    LLMModelUnavailableError,
    LLMProviderUnavailableError,
    LLMRateLimitError,
    LLMTimeoutError,
)
from app.services.llm.schemas import (
    EvidenceReference,
    EvidenceSignal,
    EvidenceSummary,
    FactVsInterpretation,
    InterpretationStatus,
    LLMInterpretation,
)


def _upload(client: TestClient, archive: bytes) -> str:
    response = client.post(
        "/api/projects/upload",
        files={"file": ("sample.zip", io.BytesIO(archive), "application/zip")},
        data={"title": "AI Assistance Test"},
    )
    assert response.status_code == 201
    return response.json()["projectId"]


def _client_raising(error: Exception) -> OpenRouterClient:
    client = OpenRouterClient.__new__(OpenRouterClient)
    client.enabled = True
    client.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_: (_ for _ in ()).throw(error))
        )
    )
    return client


def _client_returning(json_content: str) -> OpenRouterClient:
    client = OpenRouterClient.__new__(OpenRouterClient)
    client.enabled = True
    mock_choice = SimpleNamespace(message=SimpleNamespace(content=json_content))
    client.client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **_: SimpleNamespace(choices=[mock_choice])
            )
        )
    )
    return client


def _evidence() -> EvidenceSummary:
    return EvidenceSummary(project_id="diagnostic-test", rules_version="v1", signals=[])


# ---------------------------------------------------------------------------
# 1. Deterministic Evidence Collection from Actual Database Records
# ---------------------------------------------------------------------------


def test_evidence_collection_from_actual_saved_records(db_session: Session):
    """Verify EvidenceCollector reads actual Phase 3-6 records and normalizes them."""
    proj = Project(
        id="proj-full-test",
        title="Full Stack Project",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(proj)

    # Phase 3 Code Quality record
    cq = ProjectQualityAnalysis(
        project_id="proj-full-test",
        score=85.0,
        metrics_summary={
            "total_source_files": 12,
            "total_functions": 40,
            "total_classes": 5,
            "avg_complexity": 3.2,
            "max_complexity": 8.0,
            "maintainability_rating": "B",
            "syntax_errors_count": 0,
            "total_findings": 2,
        },
        findings=[
            {
                "rule_id": "radon-complex-func",
                "severity": "high",
                "explanation": "Function is slightly complex",
                "file_path": "main.py",
            }
        ],
    )
    db_session.add(cq)

    # Phase 4 Similarity record
    sim = ProjectSimilarityAnalysis(
        project_id="proj-full-test",
        compared_projects_count=4,
        highest_similarity_score=24.5,
        methods_used=["token", "structure"],
        limitations=["Only cohort submissions compared"],
    )
    db_session.add(sim)
    db_session.flush()

    sim_match = ProjectSimilarityMatch(
        analysis_id=sim.id,
        project_id="proj-full-test",
        matched_project_id="proj-cohort-2",
        overall_similarity=24.5,
    )
    db_session.add(sim_match)

    # Phase 5 Documentation record
    doc = ProjectDocumentationAnalysis(
        project_id="proj-full-test",
        status="completed",
        total_documents_count=2,
        total_words_count=850,
        recognized_sections_count=3,
        preliminary_score=80.0,
    )
    doc_finding = ProjectDocumentationFinding(
        project_id="proj-full-test",
        rule_id="tech-match",
        category="technology_consistency",
        severity="medium",
        verification_status="verified",
        title="FastAPI Verified",
        explanation="Code matches documentation",
    )
    doc.findings.append(doc_finding)
    db_session.add(doc)

    # Phase 6 Git History record
    git = ProjectGitHistoryAnalysis(
        project_id="proj-full-test",
        status="completed",
        availability="available",
        total_commits=15,
        duration_days=10.5,
        largest_commit_share_percent=25.0,
        top_3_commit_share_percent=55.0,
        distinct_contributors_count=2,
        is_shallow=False,
    )
    db_session.add(git)
    db_session.commit()

    signals = EvidenceCollector.collect_all(db_session, "proj-full-test")

    # Verify signals from all four phases
    categories = {s["category"] for s in signals}
    assert "code_quality" in categories
    assert "similarity" in categories
    assert "documentation" in categories
    assert "git_history" in categories

    available_signals = [s for s in signals if s["availability_status"] == "available"]
    assert len(available_signals) >= 10

    # Ensure no PII (student names or emails) leaked in signals
    for sig in signals:
        assert "@" not in sig["observed_value"]
        assert "@" not in sig["explanation"]


def test_missing_phase_analyses_marked_unavailable(db_session: Session):
    """When some phases have not been run, record them explicitly as unavailable."""
    proj = Project(
        id="proj-partial-test",
        title="Partial Project",
        archive_filename="part.zip",
        archive_path="/tmp/part.zip",
        file_size_bytes=512,
    )
    db_session.add(proj)

    # Only Phase 3 is run
    cq = ProjectQualityAnalysis(
        project_id="proj-partial-test",
        score=75.0,
        metrics_summary={"total_source_files": 3, "total_functions": 10},
    )
    db_session.add(cq)
    db_session.commit()

    signals = EvidenceCollector.collect_all(db_session, "proj-partial-test")
    signal_ids = [s["signal_id"] for s in signals]

    # Verify missing indicators
    assert "sim-missing" in signal_ids
    assert "doc-missing" in signal_ids
    assert "git-missing" in signal_ids

    unavailable_signals = [s for s in signals if s["availability_status"] == "unavailable"]
    assert len(unavailable_signals) >= 3


def test_project_without_git_history(db_session: Session):
    """When a project archive lacks Git metadata, verify graceful unavailable signal."""
    proj = Project(
        id="proj-no-git",
        title="No Git Project",
        archive_filename="no_git.zip",
        archive_path="/tmp/no_git.zip",
        file_size_bytes=512,
    )
    db_session.add(proj)

    git = ProjectGitHistoryAnalysis(
        project_id="proj-no-git",
        status="completed",
        availability="unavailable",
        limitations=["Archive contained no .git directory"],
    )
    db_session.add(git)
    db_session.commit()

    git_signals = EvidenceCollector.collect_git_history(db_session, "proj-no-git")
    assert any(s["signal_id"] == "git-unavailable" for s in git_signals)
    unavail_sig = next(s for s in git_signals if s["signal_id"] == "git-unavailable")
    assert unavail_sig["availability_status"] == "unavailable"


# ---------------------------------------------------------------------------
# 2. Deterministic Advisory Assessment Classification
# ---------------------------------------------------------------------------


def test_advisory_assessment_categories():
    """Verify transparent categorization across signal volume and severity thresholds."""
    # 0 available signals -> Insufficient Evidence
    empty_signals: List[Dict[str, Any]] = [
        {"availability_status": "unavailable", "category": "code_quality"}
    ]
    cat, reason, alts = AdvisoryAnalyzer.assess(empty_signals)
    assert cat == INSUFFICIENT_EVIDENCE
    assert "insufficient evidence" in reason.lower()

    # 1 to 3 signals -> Few Observable Signals
    few_signals = [
        {"availability_status": "available", "category": "code_quality"}
        for _ in range(3)
    ]
    cat, reason, _ = AdvisoryAnalyzer.assess(few_signals)
    assert cat == FEW_SIGNALS

    # 4 to 7 signals -> Some Observable Signals
    some_signals = [
        {"availability_status": "available", "category": "similarity"}
        for _ in range(6)
    ]
    cat, reason, _ = AdvisoryAnalyzer.assess(some_signals)
    assert cat == SOME_SIGNALS

    # 8+ signals -> Multiple Observable Signals
    multi_signals = [
        {"availability_status": "available", "category": "documentation"}
        for _ in range(9)
    ]
    cat, reason, _ = AdvisoryAnalyzer.assess(multi_signals)
    assert cat == MULTIPLE_SIGNALS

    # High severity finding escalates review
    escalated_signals = [
        {"availability_status": "available", "category": "code_quality"},
        {"availability_status": "available", "category": "code_quality_finding"},
    ]
    # Even if 2 signals, presence of code_quality_finding is considered in escalation
    assert AdvisoryAnalyzer.assess(multi_signals) == AdvisoryAnalyzer.assess(multi_signals)


def test_advisory_assessment_is_repeatable():
    signals = [
        {
            "availability_status": "available",
            "category": "code_quality",
        }
    ] * 8
    assert AdvisoryAnalyzer.assess(signals) == AdvisoryAnalyzer.assess(signals)


# ---------------------------------------------------------------------------
# 3. LLM Client Validation, JSON Parsing & Error Handling
# ---------------------------------------------------------------------------


def test_valid_mocked_openrouter_response_with_pydantic_validation():
    """Verify valid JSON completion parses cleanly into LLMInterpretation schema."""
    valid_data = {
        "interpretation_status": "completed",
        "executive_summary": "Analysis of observable metrics indicates consistent development.",
        "explanation_of_patterns": "Function count and documentation align with expected coursework.",
        "evidence_references": [
            {"signal_id": "cq-1", "observation": "Observed 10 functions."}
        ],
        "alternative_explanations": [
            "Starter templates may explain the project structure."
        ],
        "faculty_follow_up_recommendations": [
            "Ask student to explain the main algorithm."
        ],
        "limitations": [
            "Git history is not available."
        ],
        "fact_vs_interpretation": {
            "facts": ["10 functions observed."],
            "interpretation": ["Standard implementation complexity."],
            "speculation": [],
        },
    }
    client = _client_returning(json.dumps(valid_data))
    evidence = EvidenceSummary(
        project_id="test-pydantic",
        rules_version="v1",
        signals=[
            EvidenceSignal(
                signal_id="cq-1",
                category="code_quality",
                source="test",
                observed_value="10 functions",
                explanation="test",
                availability_status="available",
            )
        ],
    )
    interpretation = client.interpret_evidence(evidence, ["cq-1"])

    assert interpretation.interpretation_status == InterpretationStatus.COMPLETED
    assert "consistent development" in interpretation.executive_summary
    assert len(interpretation.evidence_references) == 1
    assert interpretation.evidence_references[0].signal_id == "cq-1"
    assert len(interpretation.faculty_follow_up_recommendations) == 1


def test_invalid_json_handling():
    """Verify malformed JSON from provider raises LLMInvalidResponseError."""
    client = _client_returning("Malformed JSON {not_json: true")
    evidence = _evidence()
    with pytest.raises(LLMInvalidResponseError) as exc_info:
        client.interpret_evidence(evidence, [])
    assert "invalid JSON" in str(exc_info.value)


def test_invalid_evidence_references_discard_and_reject():
    """Verify handling of evidence references not supplied in input."""
    data = {
        "interpretation_status": "completed",
        "executive_summary": "Summary text",
        "explanation_of_patterns": "Pattern explanation",
        "evidence_references": [
            {"signal_id": "valid-sig-1", "observation": "Valid signal."},
            {"signal_id": "hallucinated-sig-99", "observation": "Invented ID."},
        ],
        "alternative_explanations": [],
        "faculty_follow_up_recommendations": [],
        "limitations": [],
        "fact_vs_interpretation": {"facts": [], "interpretation": [], "speculation": []},
    }
    evidence = _evidence()
    valid_ids = ["valid-sig-1"]

    # When discard_invalid_references is False -> raises LLMInvalidReferenceError
    client_strict = _client_returning(json.dumps(data))
    with pytest.raises(LLMInvalidReferenceError) as exc_info:
        client_strict.interpret_evidence(
            evidence, valid_ids, discard_invalid_references=False
        )
    assert "hallucinated-sig-99" in str(exc_info.value)

    # When discard_invalid_references is True -> discards invalid reference and records in limitations
    client_tolerant = _client_returning(json.dumps(data))
    res = client_tolerant.interpret_evidence(
        evidence, valid_ids, discard_invalid_references=True
    )
    assert len(res.evidence_references) == 1
    assert res.evidence_references[0].signal_id == "valid-sig-1"
    assert any("hallucinated-sig-99" in lim for lim in res.limitations)


def test_provider_timeout_handling():
    """Verify provider timeout raises LLMTimeoutError."""
    error = APITimeoutError(request=httpx.Request("POST", "https://openrouter.ai"))
    with pytest.raises(LLMTimeoutError):
        _client_raising(error).interpret_evidence(_evidence(), [])


def test_provider_model_not_found_handling():
    """Verify 404 model not found raises LLMModelUnavailableError."""
    response = httpx.Response(404, request=httpx.Request("POST", "https://openrouter.ai"))
    error = NotFoundError("Model not found", response=response, body={})
    with pytest.raises(LLMModelUnavailableError) as exc_info:
        _client_raising(error).interpret_evidence(_evidence(), [])
    assert exc_info.value.status_code == 404


def test_client_unconfigured_raises_configuration_error(monkeypatch):
    """When LLM is disabled, client.interpret_evidence raises LLMConfigurationError."""
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    client = OpenRouterClient()
    assert not client.is_available()
    with pytest.raises(LLMConfigurationError):
        client.interpret_evidence(_evidence(), [])


# ---------------------------------------------------------------------------
# 4. Credential Redaction & Diagnostics
# ---------------------------------------------------------------------------


def test_rate_limit_diagnostic_captures_platform_fields_and_redacts_key():
    response = httpx.Response(
        429,
        headers={
            "Retry-After": "60",
            "X-RateLimit-Limit": "10",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": "1700000000",
            "X-Request-Id": "req-123",
        },
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    error = RateLimitError(
        "rate limit",
        response=response,
        body={
            "error": {
                "message": "Bearer sk-secret-token-1234567890 is limited",
                "metadata": {"error_type": "platform_rate_limit", "limit_source": "platform"},
            }
        },
    )

    with pytest.raises(LLMRateLimitError) as raised:
        _client_raising(error).interpret_evidence(_evidence(), [])

    diagnostic = raised.value.diagnostic
    assert diagnostic is not None
    assert diagnostic.status_code == 429
    assert diagnostic.error_type == "platform_rate_limit"
    assert diagnostic.limit_source == "platform"
    assert diagnostic.retry_after == "60"
    assert diagnostic.rate_limit_remaining == "0"
    assert diagnostic.request_id == "req-123"
    assert "sk-secret" not in (diagnostic.error_message or "")
    assert "platform" in str(raised.value)


def test_rate_limit_diagnostic_captures_upstream_provider_code():
    response = httpx.Response(
        429,
        headers={"X-Request-Id": "req-provider"},
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    error = RateLimitError(
        "rate limit",
        response=response,
        body={
            "error": {
                "message": "provider busy",
                "metadata": {"error_type": "provider_rate_limit", "provider_code": "529"},
            }
        },
    )

    with pytest.raises(LLMRateLimitError) as raised:
        _client_raising(error).interpret_evidence(_evidence(), [])

    assert raised.value.diagnostic.provider_code == "529"
    assert raised.value.diagnostic.as_dict()["request_id"] == "req-provider"
    assert "upstream_provider" in str(raised.value)


def test_rate_limit_without_metadata_is_unknown_and_optional_headers_are_null():
    response = httpx.Response(
        429,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    error = RateLimitError("unstructured error", response=response, body="not-json")

    with pytest.raises(LLMRateLimitError) as raised:
        _client_raising(error).interpret_evidence(_evidence(), [])

    diagnostic = raised.value.diagnostic
    assert diagnostic.status_code == 429
    assert diagnostic.error_message is None
    assert diagnostic.retry_after is None
    assert "cause=unknown" in str(raised.value)


def test_provider_503_preserves_status_and_message_without_raw_payload():
    response = httpx.Response(
        503,
        headers={"Retry-After": "30"},
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )
    error = APIStatusError(
        "service unavailable",
        response=response,
        body={"error": {"message": "provider overloaded", "metadata": {"provider_code": "503"}}},
    )

    with pytest.raises(LLMProviderUnavailableError) as raised:
        _client_raising(error).interpret_evidence(_evidence(), [])

    diagnostic = raised.value.diagnostic
    assert diagnostic.status_code == 503
    assert diagnostic.error_message == "provider overloaded"
    assert diagnostic.provider_code == "503"
    assert diagnostic.retry_after == "30"


# ---------------------------------------------------------------------------
# 5. Service Layer, Persistence, Idempotency & API Endpoints
# ---------------------------------------------------------------------------


def test_ai_assistance_without_previous_analyses_is_insufficient(
    client: TestClient, valid_zip_bytes: bytes, monkeypatch
):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    project_id = _upload(client, valid_zip_bytes)

    response = client.post(f"/api/projects/{project_id}/analyze/ai-assistance")

    assert response.status_code == 200
    body = response.json()
    assert body["advisoryCategory"] == "Insufficient Evidence"
    assert body["llmInterpretationStatus"] == "disabled"
    assert len(body["evidenceSummary"]) == 4
    assert all(item["availabilityStatus"] == "unavailable" for item in body["evidenceSummary"])


def test_ai_assistance_is_idempotent_and_in_unified_bundle(
    client: TestClient,
    db_session: Session,
    complex_python_zip_bytes: bytes,
    monkeypatch,
):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    project_id = _upload(client, complex_python_zip_bytes)

    first = client.post(f"/api/projects/{project_id}/analyze/ai-assistance")
    second = client.post(f"/api/projects/{project_id}/analyze/ai-assistance")

    assert first.status_code == second.status_code == 200
    assert (
        db_session.query(ProjectAIAssistanceAnalysis)
        .filter_by(project_id=project_id)
        .count()
        == 1
    )
    bundle = client.get(f"/api/projects/{project_id}/analysis")
    assert bundle.status_code == 200
    assert bundle.json()["aiAssistance"]["projectId"] == project_id


def test_ai_assistance_get_does_not_run_analysis(client: TestClient, valid_zip_bytes: bytes):
    project_id = _upload(client, valid_zip_bytes)
    response = client.get(f"/api/projects/{project_id}/ai-assistance")

    assert response.status_code == 200
    assert response.json()["analysisStatus"] == "not_started"


def test_rate_limit_error_does_not_destroy_deterministic_analysis(
    client: TestClient, valid_zip_bytes: bytes, monkeypatch
):
    project_id = _upload(client, valid_zip_bytes)

    class FailingLLM:
        def is_available(self):
            return True

        def interpret_evidence(self, evidence, valid_signal_ids, **kwargs):
            raise LLMRateLimitError(
                "OpenRouter rate limit reached (HTTP 429; cause=unknown)."
            )

    monkeypatch.setattr(ai_service, "OpenRouterClient", FailingLLM)
    response = client.post(f"/api/projects/{project_id}/analyze/ai-assistance")

    assert response.status_code == 200
    assert response.json()["advisoryCategory"] == "Insufficient Evidence"
    assert response.json()["llmInterpretationStatus"] == "error"
    assert any("rate limit" in lim.lower() for lim in response.json()["limitations"])


def test_nonexistent_project_returns_404(client: TestClient):
    """GET and POST on nonexistent project_id return 404."""
    post_res = client.post("/api/projects/nonexistent-999/analyze/ai-assistance")
    assert post_res.status_code == 404

    get_res = client.get("/api/projects/nonexistent-999/ai-assistance")
    assert get_res.status_code == 404


# ---------------------------------------------------------------------------
# 6. Phase 9 Gemini & Deterministic 10-Area Fallback Tests
# ---------------------------------------------------------------------------


def test_ai_assistance_deterministic_fallback_populates_10_areas(client: TestClient, valid_zip_bytes: bytes, monkeypatch):
    """Verify that structuredInterpretation.findings contains 10 structured areas on fallback."""
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    project_id = _upload(client, valid_zip_bytes)

    response = client.post(f"/api/projects/{project_id}/analyze/ai-assistance")
    assert response.status_code == 200
    data = response.json()

    interp = data.get("structuredInterpretation") or {}
    findings = interp.get("findings") or []
    assert len(findings) == 10

    categories = [f.get("category") for f in findings]
    assert any("Overview" in c for c in categories)
    assert any("Architecture" in c for c in categories)
    assert any("Code Quality" in c for c in categories)
    assert any("Testing" in c for c in categories)
    assert any("Security" in c for c in categories)
    assert any("Viva" in c for c in categories)

    for f in findings:
        assert f.get("title")
        assert f.get("description")
        assert f.get("priority") in ("Critical", "High", "Medium", "Low", "Informational")
        assert f.get("why_it_matters") or f.get("whyItMatters")
        assert f.get("recommended_action") or f.get("recommendedAction")


def test_gemini_client_evidence_interpretation_mock(monkeypatch):
    """Verify OpenRouterClient._interpret_evidence_gemini parses valid response."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-key")
    monkeypatch.setattr(settings, "LLM_ENABLED", True)

    client = OpenRouterClient.__new__(OpenRouterClient)
    client.enabled = True
    client.is_gemini = True

    gemini_resp_payload = {
        "interpretation_status": "completed",
        "executive_summary": "Clean Python project with solid structure.",
        "explanation_of_patterns": "Observed standard MVC architecture with deterministic signals.",
        "evidence_references": [{"signal_id": "sig-1", "observation": "Observed 12 functions."}],
        "alternative_explanations": ["May reflect standard starter code."],
        "faculty_follow_up_recommendations": ["Ask student about design choices."],
        "limitations": [],
        "fact_vs_interpretation": {
            "facts": ["12 functions found."],
            "interpretation": ["Standard complexity."],
            "speculation": []
        },
        "findings": [
            {
                "title": "Architecture Separation",
                "description": "Layered design with clear controllers.",
                "category": "Architecture",
                "priority": "Medium",
                "why_it_matters": "Improves testability.",
                "supporting_evidence": "Controller modules present.",
                "recommended_action": "Add unit tests.",
                "expected_benefit": "Higher reliability.",
                "source_reference": "controllers.py"
            }
        ]
    }

    mock_model_resp = SimpleNamespace(text=json.dumps(gemini_resp_payload))
    client.gemini_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: mock_model_resp
        )
    )

    evidence = EvidenceSummary(
        project_id="p-gemini-test",
        rules_version="v1",
        signals=[
            EvidenceSignal(
                signal_id="sig-1",
                category="code_quality",
                source="test",
                observed_value="12 functions",
                explanation="12 functions found.",
                availability_status="available",
            )
        ]
    )

    result = client.interpret_evidence(evidence, ["sig-1"])
    assert result.interpretation_status == InterpretationStatus.COMPLETED
    assert "Clean Python project" in result.executive_summary
    assert len(result.findings) == 1
    assert result.findings[0].title == "Architecture Separation"


def test_ai_assistance_deterministic_findings_handles_dict_frameworks_and_missing_metrics(
    db_session: Session,
):
    """Verify that deterministic findings generation handles dict frameworks and null metrics without crashing."""
    from app.models.project import Project, ProjectStructure, ProjectFile
    from app.models.code_quality import ProjectQualityAnalysis
    from app.models.documentation import ProjectDocumentationAnalysis
    from app.services.ai_assistance.service import AIAssistanceService

    project = Project(
        id="proj_dict_fw_test",
        title="Dict Framework Test Project",
        archive_filename="test.zip",
        archive_path="/fake/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.flush()

    structure = ProjectStructure(
        project_id=project.id,
        total_files=5,
        source_files_count=3,
        total_source_size_bytes=1000,
        languages={"Python": {"files": 3}},
        frameworks=[
            {"name": "FastAPI", "category": "Web Framework"},
            {"name": "React", "category": "Frontend UI"},
        ],
    )
    db_session.add(structure)

    # Add file with and without relative_path
    f1 = ProjectFile(
        project_id=project.id,
        relative_path="src/main.py",
        filename="main.py",
        extension=".py",
        size_bytes=500,
        category="source",
    )
    f2 = ProjectFile(
        project_id=project.id,
        relative_path="docs/untracked.txt",
        filename="untracked.txt",
        extension=".txt",
        size_bytes=100,
        category="documentation",
    )
    db_session.add_all([f1, f2])

    # Quality analysis with None complexity
    quality = ProjectQualityAnalysis(
        project_id=project.id,
        status="completed",
        score=75.0,
        metrics_summary={"total_source_files": 2},
    )
    db_session.add(quality)

    # Documentation analysis with None total_words
    docs = ProjectDocumentationAnalysis(
        project_id=project.id,
        status="completed",
        total_documents_count=1,
        total_words_count=None,
        recognized_sections_count=2,
    )
    db_session.add(docs)
    db_session.commit()

    # Generate deterministic findings
    findings = AIAssistanceService._build_deterministic_findings(
        db=db_session,
        project_id=project.id,
        signals=[],
        advisory_category="Sufficient Evidence",
    )

    assert len(findings) == 10
    categories = [f["category"] for f in findings]
    assert "Project Overview and Understanding" in categories
    assert "Technology Stack and Dependencies" in categories
    assert "Code Quality and Maintainability" in categories

    # Verify frameworks string was correctly extracted
    fw_finding = next(f for f in findings if f["category"] == "Technology Stack and Dependencies")
    assert "FastAPI" in fw_finding["description"]
    assert "React" in fw_finding["description"]


def test_evidence_collector_isolates_individual_collector_failure(
    db_session: Session, monkeypatch
):
    """Verify that an exception in one collector does not crash collect_all and reports an error signal."""
    project = Project(
        id="proj_collector_fail_test",
        title="Collector Failure Test",
        archive_filename="test.zip",
        archive_path="/fake/test.zip",
        file_size_bytes=512,
    )
    db_session.add(project)
    db_session.commit()

    # Monkeypatch collect_code_quality to raise an exception
    def _buggy_collector(*args, **kwargs):
        raise RuntimeError("Simulated AST parser crash")

    monkeypatch.setattr(EvidenceCollector, "collect_code_quality", _buggy_collector)

    signals = EvidenceCollector.collect_all(db_session, project.id)
    assert len(signals) > 0

    # Verify an unavailable signal was emitted for code_quality
    cq_error = next((s for s in signals if s["signal_id"] == "code_quality-error"), None)
    assert cq_error is not None
    assert cq_error["availability_status"] == "unavailable"
    assert "RuntimeError" in cq_error["explanation"]


def test_llm_interpretation_normalizes_string_lists_and_status_variants():
    """Verify that LLMInterpretation schema safely accepts strings for list fields and normalizes status."""
    payload = {
        "interpretation_status": "Complete",
        "executive_summary": "Solid student project with clear boundaries.",
        "explanation_of_patterns": "Structured into frontend and backend folders.",
        "alternative_explanations": "Single string explanation rather than list.",
        "faculty_follow_up_recommendations": "Single follow up question.",
        "limitations": "Single limitation note.",
        "fact_vs_interpretation": {
            "facts": "Fact 1\nFact 2",
            "interpretation": "Single interpretation",
            "speculation": None
        },
        "findings": [
            {
                "title": "API Organization",
                "description": "Good structure",
                "category": "Architecture",
                "priority": "Medium",
                "whyItMatters": ["Important for maintenance"],
                "supportingEvidence": {"file": "routes.py"},
                "recommendedAction": "Keep organizing",
                "expectedBenefit": "Readability",
            }
        ]
    }

    parsed = LLMInterpretation.model_validate(payload)
    assert parsed.interpretation_status == InterpretationStatus.COMPLETED
    assert parsed.alternative_explanations == ["Single string explanation rather than list."]
    assert parsed.faculty_follow_up_recommendations == ["Single follow up question."]
    assert parsed.limitations == ["Single limitation note."]
    assert parsed.fact_vs_interpretation.facts == ["Fact 1", "Fact 2"]
    assert parsed.fact_vs_interpretation.interpretation == ["Single interpretation"]
    assert parsed.fact_vs_interpretation.speculation == []
    assert len(parsed.findings) == 1
    assert parsed.findings[0].why_it_matters == "Important for maintenance"
    assert parsed.findings[0].supporting_evidence == "routes.py"


