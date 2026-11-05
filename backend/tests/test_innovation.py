"""Tests for Phase 7B Innovation Analyzer (profile extraction, cohort comparison, distinctiveness, LLM, API)."""

from datetime import datetime, timezone
import json
from types import SimpleNamespace
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentItem,
)
from app.models.innovation import (
    ProjectInnovationAnalysis,
    ProjectInnovationMatch,
)
from app.services.innovation.profile import EvidenceType, FeatureEvidence, ProjectProfile
from app.services.innovation.extractor import ProjectProfileExtractor
from app.services.innovation.cohort_comparison import (
    CohortComparisonService,
    SimpleTfidfVectorizer,
)
from app.services.innovation.scoring import (
    InnovationScoringEngine,
    CATEGORY_INSUFFICIENT_EVIDENCE,
    CATEGORY_LIMITED_DIFFERENTIATION,
    CATEGORY_SOME_DISTINCTIVE,
    CATEGORY_STRONG_DISTINCTIVE,
    CATEGORY_FACULTY_REVIEW,
)
from app.services.innovation.prompts import (
    LLMInnovationInterpretation,
    EvidenceReference,
    build_innovation_user_prompt,
)
from app.services.innovation.service import InnovationService
from app.services.llm.client import OpenRouterClient
from app.services.llm.exceptions import (
    LLMInvalidReferenceError,
    LLMInvalidResponseError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMDiagnosticMetadata,
)


def _create_test_project(
    db: Session,
    project_id: str,
    title: str = "Test Project",
    status: str = "completed",
    languages: Dict[str, Any] = None,
    frameworks: List[str] = None,
    has_readme: bool = True,
    file_names: List[str] = None,
    sections: List[Dict[str, str]] = None,
) -> Project:
    """Helper to seed a project with structure, files, and documentation analysis."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id=project_id,
        title=title,
        status=status,
        archive_filename=f"{project_id}.zip",
        archive_path=f"/fake/{project_id}.zip",
        file_size_bytes=1024,
    )
    db.add(proj)

    struct = ProjectStructure(
        project_id=project_id,
        total_files=len(file_names or ["main.py"]),
        source_files_count=len(file_names or ["main.py"]),
        languages=languages or {"Python": {"files": 1}},
        frameworks=frameworks or ["FastAPI"],
        has_readme=has_readme,
    )
    db.add(struct)

    for fn in (file_names or ["main.py"]):
        pf = ProjectFile(
            project_id=project_id,
            relative_path=fn,
            filename=fn.split("/")[-1],
            category="Source Code" if not fn.endswith(".md") else "Documentation",
            detected_language="Python" if fn.endswith(".py") else None,
        )
        db.add(pf)

    if sections:
        doc_anal = ProjectDocumentationAnalysis(
            project_id=project_id,
            status="completed",
            preliminary_score=85.0,
            total_documents_count=1,
            total_words_count=500,
        )
        db.add(doc_anal)
        db.flush()

        doc_item = ProjectDocumentItem(
            analysis_id=doc_anal.id,
            project_id=project_id,
            relative_path="README.md",
            filename="README.md",
            file_format="markdown",
            sections_found=sections,
        )
        db.add(doc_item)

    db.commit()
    db.refresh(proj)
    return proj


# =====================================================================
# 1. Profile Extraction from Documentation
# =====================================================================

def test_profile_extraction_from_documentation(db_session: Session):
    sections = [
        {
            "heading": "Introduction & Problem Statement",
            "content": "Patient scheduling in rural clinics suffers from extreme waiting times and lack of medical records.",
        },
        {
            "heading": "Proposed Solution",
            "content": "A telemedicine consultation portal that optimizes appointment slots using predictive queuing.",
        },
        {
            "heading": "Features",
            "content": "- Patient Authentication\n- Doctor Appointment Queuing\n- Medical Record Export",
        },
    ]
    _create_test_project(
        db_session,
        "proj-health-1",
        title="TeleHealth Rural Clinic Portal",
        file_names=["auth.py", "scheduling.py", "export.py", "models.py"],
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-health-1")

    assert profile.project_id == "proj-health-1"
    assert profile.has_documentation is True
    assert profile.domain == "Healthcare / Medical"
    assert "rural clinics" in profile.problem_statement.lower()
    assert "telemedicine" in profile.proposed_solution.lower()
    assert len(profile.features) >= 3
    assert profile.is_sufficient is True


# =====================================================================
# 2. Profile Extraction when README is Absent
# =====================================================================

def test_profile_extraction_readme_absent(db_session: Session):
    _create_test_project(
        db_session,
        "proj-no-readme",
        title="Inventory Tracker CLI",
        has_readme=False,
        file_names=["inventory_manager.py", "db.py"],
        sections=None,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-no-readme")

    assert profile.has_documentation is False
    assert profile.is_empty is False
    # Features inferred directly from code modules
    assert len(profile.features) >= 1
    assert any(f.evidence_type == EvidenceType.DETECTED_IMPLEMENTATION for f in profile.features)


# =====================================================================
# 3. Missing Problem Statement
# =====================================================================

def test_missing_problem_statement(db_session: Session):
    sections = [
        {"heading": "Installation", "content": "Run pip install -r requirements.txt and start uvicorn main:app."}
    ]
    _create_test_project(
        db_session,
        "proj-no-problem",
        title="Data Converter Tool",
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-no-problem")
    # Problem statement handles missing problem gracefully without crashing
    assert profile.problem_statement in ("", "Not identified from the available project documents.") or "data converter" in profile.problem_statement.lower()


# =====================================================================
# 4. Missing Feature Descriptions
# =====================================================================

def test_missing_feature_descriptions(db_session: Session):
    sections = [
        {"heading": "Background", "content": "Educational tool for high school physics experiments."}
    ]
    _create_test_project(
        db_session,
        "proj-no-feat-doc",
        title="Physics Simulator",
        file_names=["simulation_engine.py", "renderer.py"],
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-no-feat-doc")
    # Features should be discovered from code modules
    assert len(profile.features) >= 1
    assert any("Simulation" in f.name or "Renderer" in f.name for f in profile.features)


# =====================================================================
# 5. Technology Detection using Existing Structure Results
# =====================================================================

def test_technology_detection_from_structure(db_session: Session):
    _create_test_project(
        db_session,
        "proj-tech-stack",
        languages={"Python": {"files": 4}, "TypeScript": {"files": 2}},
        frameworks=["FastAPI", "React"],
        file_names=["api/main.py", "db/postgres_client.py", "frontend/App.tsx"],
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-tech-stack")

    assert "Python" in profile.languages
    assert "FastAPI" in profile.frameworks
    assert "PostgreSQL" in profile.databases


# =====================================================================
# 6. Distinguishing Documented Features from Implementation Evidence
# =====================================================================

def test_distinguishing_documented_features_from_implementation(db_session: Session):
    sections = [
        {
            "heading": "Features",
            "content": (
                "- Authentication Service\n"
                "- Blockchain Smart Contract Audit\n"
            ),
        }
    ]
    # auth.py exists in code, but blockchain does NOT exist in code
    _create_test_project(
        db_session,
        "proj-feature-diff",
        file_names=["auth.py", "billing_worker.py"],
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-feature-diff")

    # Auth feature matches auth.py -> VERIFIED_MATCH
    auth_feat = next((f for f in profile.features if "Authentication" in f.name), None)
    assert auth_feat is not None
    assert auth_feat.evidence_type == EvidenceType.VERIFIED_MATCH
    assert auth_feat.code_reference is not None

    # Blockchain feature has no matching code -> UNVERIFIED_CLAIM
    bc_feat = next((f for f in profile.features if "Blockchain" in f.name), None)
    assert bc_feat is not None
    assert bc_feat.evidence_type == EvidenceType.UNVERIFIED_CLAIM
    assert bc_feat.code_reference is None


# =====================================================================
# 7. Projects with Insufficient Profile Information
# =====================================================================

def test_projects_with_insufficient_profile_information(db_session: Session):
    # Empty project with no files and no structure
    proj = Project(
        id="proj-empty-1",
        title="Empty Project",
        status="completed",
        archive_filename="empty.zip",
        archive_path="/fake/empty.zip",
        file_size_bytes=0,
    )
    db_session.add(proj)
    db_session.commit()

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-empty-1")
    assert profile.is_empty is True
    assert profile.is_sufficient is False

    cat, scores, limitations = InnovationScoringEngine.evaluate(profile, cohort_size=0, matches=[])
    assert cat == CATEGORY_INSUFFICIENT_EVIDENCE


# =====================================================================
# 8. No Comparable Cohort Projects (Empty Cohort)
# =====================================================================

def test_no_comparable_cohort_projects(db_session: Session):
    # Only 1 project exists
    _create_test_project(
        db_session,
        "proj-solo",
        title="Solo System",
        sections=[{"heading": "Overview", "content": "Standalone library for graph parsing."}],
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-solo")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, profile)

    assert cohort_size == 0
    assert matches == []
    assert method == "unavailable"


# =====================================================================
# 9. One Comparable Cohort Project
# =====================================================================

def test_one_comparable_cohort_project(db_session: Session):
    _create_test_project(
        db_session,
        "proj-a",
        title="E-Commerce Storefront",
        sections=[{"heading": "Overview", "content": "Online retail cart and checkout."}],
    )
    _create_test_project(
        db_session,
        "proj-b",
        title="Grocery Mart Online",
        sections=[{"heading": "Overview", "content": "Online supermarket catalog and order cart."}],
    )

    profile_a = ProjectProfileExtractor.extract_profile(db_session, "proj-a")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, profile_a)

    assert cohort_size == 1
    assert len(matches) == 1
    assert matches[0]["compared_project_id"] == "proj-b"
    assert matches[0]["overall_similarity"] > 0.0


# =====================================================================
# 10. Multiple Comparable Cohort Projects
# =====================================================================

def test_multiple_comparable_cohort_projects(db_session: Session):
    for pid, title, domain_text in [
        ("p1", "E-Commerce App", "Online shopping cart and payment."),
        ("p2", "Hospital ERP", "Patient admission and medical records."),
        ("p3", "School Management", "Student grades and attendance tracking."),
    ]:
        _create_test_project(
            db_session,
            pid,
            title=title,
            sections=[{"heading": "Overview", "content": domain_text}],
        )

    profile_1 = ProjectProfileExtractor.extract_profile(db_session, "p1")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, profile_1)

    assert cohort_size == 2
    assert len(matches) == 2
    # Ensure p1 is not compared against itself
    assert all(m["compared_project_id"] != "p1" for m in matches)


# =====================================================================
# 11. Self-Comparison Exclusion
# =====================================================================

def test_self_comparison_exclusion(db_session: Session):
    _create_test_project(db_session, "self-proj", title="Self Project")
    _create_test_project(db_session, "other-proj", title="Other Project")

    profile = ProjectProfileExtractor.extract_profile(db_session, "self-proj")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, profile)

    for m in matches:
        assert m["compared_project_id"] != "self-proj"


# =====================================================================
# 12. TF-IDF Similarity Calculation
# =====================================================================

def test_tfidf_similarity_calculation():
    vectorizer = SimpleTfidfVectorizer()
    doc1 = "telemedicine patient appointment doctor scheduling system"
    doc2 = "telemedicine doctor consultation patient record system"
    doc3 = "quantum cryptography lattice based encryption network"

    vectors = vectorizer.fit_transform([doc1, doc2, doc3])
    sim_1_2 = SimpleTfidfVectorizer.cosine_similarity(vectors[0], vectors[1])
    sim_1_3 = SimpleTfidfVectorizer.cosine_similarity(vectors[0], vectors[2])

    assert 0.3 < sim_1_2 <= 1.0  # Shared medical/telemedicine terms
    assert sim_1_3 == 0.0  # Zero overlapping vocabulary


# =====================================================================
# 13. Embedding Availability and Unavailable Handling
# =====================================================================

def test_embedding_availability_and_unavailable_handling(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "SIMILARITY_ENABLE_SEMANTIC", False)
    _create_test_project(db_session, "emb-1", title="System One")
    _create_test_project(db_session, "emb-2", title="System Two")

    profile = ProjectProfileExtractor.extract_profile(db_session, "emb-1")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, profile)

    # Falls back transparently to tfidf_cosine
    assert method == "tfidf_cosine"
    assert len(matches) == 1


# =====================================================================
# 14. Dimension-Wise Distinctiveness Assessment
# =====================================================================

def test_dimension_wise_distinctiveness_assessment(db_session: Session):
    _create_test_project(
        db_session,
        "eval-1",
        title="Blockchain Voting",
        sections=[
            {"heading": "Problem Statement", "content": "Centralized voting systems suffer from single points of failure and lack of auditability."},
            {"heading": "Overview", "content": "Cryptographic decentralized voting system with verifiable tallying."},
        ],
    )
    profile = ProjectProfileExtractor.extract_profile(db_session, "eval-1")

    # Mock cohort match with low similarity
    mock_matches = [
        {
            "compared_project_id": "eval-2",
            "problem_similarity": 0.1,
            "solution_similarity": 0.1,
            "feature_similarity": 0.1,
            "technology_overlap": 0.2,
            "overall_similarity": 0.15,
        }
    ]
    cat, scores, limitations = InnovationScoringEngine.evaluate(profile, cohort_size=1, matches=mock_matches)

    assert "problem_distinctiveness" in scores
    assert "solution_distinctiveness" in scores
    assert "feature_differentiation" in scores
    assert "technical_contribution" in scores
    assert "evidence_supporting_claim" in scores
    assert scores["problem_distinctiveness"] == 0.9


# =====================================================================
# 15. Empty Cohort Not Receiving an Invented High Score
# =====================================================================

def test_empty_cohort_not_receiving_invented_high_score(db_session: Session):
    _create_test_project(db_session, "lone-wolf", title="Lone Project")
    profile = ProjectProfileExtractor.extract_profile(db_session, "lone-wolf")

    cat, scores, limitations = InnovationScoringEngine.evaluate(profile, cohort_size=0, matches=[])

    assert cat == CATEGORY_INSUFFICIENT_EVIDENCE
    assert scores["problem_distinctiveness"] in (0.0, None)
    assert scores["feature_differentiation"] in (0.0, None)
    assert any("No comparable cohort" in lim for lim in limitations)


# =====================================================================
# 16. LLM Disabled
# =====================================================================

def test_llm_disabled(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    _create_test_project(db_session, "p-llm-dis", title="LLM Disabled Project")

    res = InnovationService.analyze_project(db_session, "p-llm-dis", call_llm=True)

    assert res.llm_interpretation_status == "disabled"
    assert res.structured_interpretation == {}
    assert res.advisory_category is not None


# =====================================================================
# 17. Valid Mocked LLM Output
# =====================================================================

def test_valid_mocked_llm_output(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_API_KEY", "sk-mock-key")

    mock_interp = LLMInnovationInterpretation(
        interpretation_status="completed",
        innovation_summary="The project implements a distinctive queuing approach.",
        problem_understanding="Addresses wait times in clinics.",
        proposed_solution_understanding="Uses predictive scheduling.",
        potential_contributions=["Lowers patient waiting time"],
        distinctive_elements=["Real-time triage queue"],
        cohort_comparison_interpretation="Distinct from standard appointment books.",
        evidence_references=[
            EvidenceReference(evidence_id="FEAT-1", observation="Directly implemented in scheduling.py")
        ],
        alternative_explanations=["Could use standard FIFO queue"],
        faculty_follow_up_recommendations=["Ask how queue priority handles emergency patients"],
        limitations=["Limited to rural connectivity scenario"],
    )

    class MockClient(OpenRouterClient):
        def is_available(self) -> bool:
            return True

        def interpret_innovation(self, *args, **kwargs):
            return mock_interp

    _create_test_project(
        db_session,
        "p-mock-llm",
        title="TeleHealth Queue",
        sections=[{"heading": "Features", "content": "- Queuing Engine"}],
        file_names=["queuing_engine.py"],
    )

    res = InnovationService.analyze_project(
        db_session, "p-mock-llm", client=MockClient(), call_llm=True
    )

    assert res.llm_interpretation_status == "completed"
    assert res.structured_interpretation["innovation_summary"] == mock_interp.innovation_summary
    assert len(res.structured_interpretation["faculty_follow_up_recommendations"]) >= 1


# =====================================================================
# 18. Invalid JSON Handling
# =====================================================================

def test_invalid_json_handling(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_API_KEY", "sk-mock-key")

    class MockInvalidClient(OpenRouterClient):
        def is_available(self) -> bool:
            return True

        def interpret_innovation(self, *args, **kwargs):
            raise LLMInvalidResponseError("LLM returned malformed JSON.")

    _create_test_project(db_session, "p-inv-json", title="Bad JSON Proj")

    res = InnovationService.analyze_project(
        db_session, "p-inv-json", client=MockInvalidClient(), call_llm=True
    )

    assert res.llm_interpretation_status == "error"
    assert any("LLM interpretation failed" in lim for lim in res.limitations)
    # Deterministic analysis is NOT broken
    assert res.analysis_status in ("completed", "insufficient_evidence")


# =====================================================================
# 19. Invalid Evidence References
# =====================================================================

def test_invalid_evidence_references():
    mock_interp = LLMInnovationInterpretation(
        interpretation_status="completed",
        innovation_summary="Summary",
        problem_understanding="Problem",
        proposed_solution_understanding="Solution",
        cohort_comparison_interpretation="Comparison",
        evidence_references=[
            EvidenceReference(evidence_id="UNKNOWN-FEAT-99", observation="Invented reference")
        ],
    )

    # Discard invalid should remove it
    OpenRouterClient._validate_innovation_references(
        mock_interp, valid_ids={"FEAT-1", "FEAT-2"}, discard_invalid=True
    )
    assert len(mock_interp.evidence_references) == 0
    assert any("Discarded invalid" in lim for lim in mock_interp.limitations)

    # Without discard should raise
    mock_interp.evidence_references = [
        EvidenceReference(evidence_id="UNKNOWN-FEAT-99", observation="Invented reference")
    ]
    with pytest.raises(LLMInvalidReferenceError):
        OpenRouterClient._validate_innovation_references(
            mock_interp, valid_ids={"FEAT-1", "FEAT-2"}, discard_invalid=False
        )


# =====================================================================
# 20. HTTP 429 Handling without Retries
# =====================================================================

def test_http_429_handling_without_retries(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_API_KEY", "sk-mock-key")

    call_count = 0

    class Mock429Client(OpenRouterClient):
        def is_available(self) -> bool:
            return True

        def interpret_innovation(self, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            diag = LLMDiagnosticMetadata(status_code=429, error_message="Rate limit exceeded")
            raise LLMRateLimitError("Rate limited (HTTP 429)", diagnostic=diag)

    _create_test_project(db_session, "p-429", title="Rate Limited Proj")

    res = InnovationService.analyze_project(
        db_session, "p-429", client=Mock429Client(), call_llm=True
    )

    # Only called once — no automatic retry loops
    assert call_count == 1
    assert res.llm_interpretation_status == "error"
    assert any("429" in lim for lim in res.limitations)
    # Deterministic results preserved
    assert res.analysis_status in ("completed", "insufficient_evidence")


# =====================================================================
# 21. Provider Timeout
# =====================================================================

def test_provider_timeout(db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", True)
    monkeypatch.setattr(settings, "LLM_API_KEY", "sk-mock-key")

    class MockTimeoutClient(OpenRouterClient):
        def is_available(self) -> bool:
            return True

        def interpret_innovation(self, *args, **kwargs):
            raise LLMTimeoutError("Request timed out.")

    _create_test_project(db_session, "p-timeout", title="Timeout Proj")

    res = InnovationService.analyze_project(
        db_session, "p-timeout", client=MockTimeoutClient(), call_llm=True
    )

    assert res.llm_interpretation_status == "error"
    assert any("timed out" in lim for lim in res.limitations)


# =====================================================================
# 22. API GET and POST Endpoints
# =====================================================================

def test_api_endpoints_get_and_post(client: TestClient, db_session: Session, monkeypatch):
    monkeypatch.setattr(settings, "LLM_ENABLED", False)
    _create_test_project(db_session, "api-proj", title="API Proj")

    # 1. GET before analysis returns not_started
    get_res = client.get("/api/projects/api-proj/innovation")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["analysisStatus"] == "not_started"
    assert data["projectId"] == "api-proj"

    # 2. POST triggers analysis
    post_res = client.post("/api/projects/api-proj/analyze/innovation")
    assert post_res.status_code == 200
    post_data = post_res.json()
    assert post_data["analysisStatus"] in ("completed", "insufficient_evidence")
    assert "profile" in post_data
    assert "matches" in post_data

    # 3. GET after analysis returns saved record without calling LLM
    get_res_after = client.get("/api/projects/api-proj/innovation")
    assert get_res_after.status_code == 200
    assert get_res_after.json()["id"] == post_data["id"]

    # 4. Nonexistent project returns 404
    err_res = client.get("/api/projects/nonexistent-xyz/innovation")
    assert err_res.status_code == 404

    # 5. Unified analysis endpoint contains innovation section
    unified_res = client.get("/api/projects/api-proj/analysis")
    assert unified_res.status_code == 200
    u_data = unified_res.json()
    assert "innovation" in u_data
    assert u_data["innovation"] is not None


# =====================================================================
# 23. Idempotent Database Persistence
# =====================================================================

def test_idempotent_database_persistence(db_session: Session):
    _create_test_project(db_session, "idem-proj", title="Idempotent Project")
    _create_test_project(db_session, "peer-proj", title="Peer Project")

    # Run 1
    res1 = InnovationService.analyze_project(db_session, "idem-proj", call_llm=False)
    # Run 2 (re-analysis)
    res2 = InnovationService.analyze_project(db_session, "idem-proj", call_llm=False)

    analyses = (
        db_session.query(ProjectInnovationAnalysis)
        .filter(ProjectInnovationAnalysis.project_id == "idem-proj")
        .all()
    )
    # Previous analysis was replaced cleanly, no orphaned records
    assert len(analyses) == 1

    matches = (
        db_session.query(ProjectInnovationMatch)
        .filter(ProjectInnovationMatch.project_id == "idem-proj")
        .all()
    )
    # Match count matches cohort size exactly (no duplicate matches)
    assert len(matches) == res2.cohort_size


# =====================================================================
# 24. Heading-Only Documentation Rejection
# =====================================================================

def test_heading_only_documentation_rejected(db_session: Session):
    sections = [
        {"heading": "About", "content": "About"},
        {"heading": "Overview", "content": "Overview"},
        {"heading": "Introduction", "content": "Introduction"},
    ]
    _create_test_project(
        db_session,
        "proj-heading-only",
        title="Heading Only Project",
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-heading-only")
    assert profile.problem_statement == "Not identified from the available project documents."
    assert profile.proposed_solution == "Not identified from the available project documents."


# =====================================================================
# 25. Insufficient Descriptions Not Invented
# =====================================================================

def test_insufficient_project_descriptions_not_invented(db_session: Session):
    sections = [
        {"heading": "Problem", "content": "Short."},
        {"heading": "Solution", "content": "pip install test"},
    ]
    _create_test_project(
        db_session,
        "proj-short-stub",
        title="Stub Project",
        sections=sections,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-short-stub")
    assert profile.problem_statement == "Not identified from the available project documents."
    assert profile.proposed_solution == "Not identified from the available project documents."
    assert "automated support for" not in profile.proposed_solution


# =====================================================================
# 26. Feature Classification for Code Components
# =====================================================================

def test_feature_classification_code_components(db_session: Session):
    _create_test_project(
        db_session,
        "proj-code-modules",
        title="Pipeline System",
        has_readme=False,
        file_names=["generate_data.py", "test_gx.py", "drift.py"],
        sections=None,
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "proj-code-modules")
    assert len(profile.features) >= 3
    for f in profile.features:
        assert f.evidence_type == EvidenceType.DETECTED_IMPLEMENTATION
        assert f.name.startswith("Code Component: ")
        assert "Internal technical component inferred from source file" in f.description
        assert f.code_reference is not None


# =====================================================================
# 27. Cohort Display Names and Duplicate Disambiguation
# =====================================================================

def test_cohort_display_names_and_duplicate_disambiguation(db_session: Session):
    _create_test_project(
        db_session,
        "target-proj",
        title="Target Project",
        file_names=["app.py", "service.py"],
        sections=[{"heading": "Problem", "content": "High latency in medical triage systems causes dangerous bottlenecks."}],
    )
    # Peer with UUID / hash title
    _create_test_project(
        db_session,
        "c74384b6-412e-4b68-809b-734f59346f08",
        title="c74384b6-412e-4b68-809b-734f59346f08",
        file_names=["triage.py"],
        sections=[{"heading": "Problem", "content": "Triage bottlenecks in hospital admissions reduce patient throughput."}],
    )
    # Two peers sharing duplicate title "Shared Portal"
    _create_test_project(
        db_session,
        "peer-dup-1111",
        title="Shared Portal",
        file_names=["portal1.py"],
        sections=[{"heading": "Problem", "content": "Healthcare portal scheduling issues in remote clinical practices."}],
    )
    _create_test_project(
        db_session,
        "peer-dup-2222",
        title="Shared Portal",
        file_names=["portal2.py"],
        sections=[{"heading": "Problem", "content": "Clinic portal scheduling issues in regional health network centers."}],
    )

    target_profile = ProjectProfileExtractor.extract_profile(db_session, "target-proj")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, target_profile)

    assert cohort_size == 3
    titles = [m["compared_project_title"] for m in matches]
    # Internal hash title should be cleaned to Project (short_id)
    assert any("Project (c74384b6)" in t for t in titles)
    # Duplicate titles should be disambiguated with short_id
    assert any("Shared Portal (peer-dup" in t for t in titles)


# =====================================================================
# 28. Duplicate Submission Detection and Screening Advisory
# =====================================================================

def test_duplicate_submission_detection(db_session: Session):
    common_sections = [
        {"heading": "Problem Statement", "content": "Clinical documentation workflow inefficiencies leading to burnout."},
        {"heading": "Solution", "content": "Automated voice transcription pipeline for physician progress notes."},
    ]
    _create_test_project(
        db_session,
        "orig-submission",
        title="Doctor Voice Notes",
        file_names=["transcribe.py", "notes.py"],
        sections=common_sections,
    )
    _create_test_project(
        db_session,
        "copy-submission",
        title="Doctor Voice Notes",
        file_names=["transcribe.py", "notes.py"],
        sections=common_sections,
    )

    orig_profile = ProjectProfileExtractor.extract_profile(db_session, "orig-submission")
    cohort_size, method, matches = CohortComparisonService.compare_project_to_cohort(db_session, orig_profile)

    assert cohort_size >= 1
    copy_match = next(m for m in matches if m["compared_project_id"] == "copy-submission")
    assert copy_match["overall_similarity"] >= 0.85
    assert "Potential exact duplicate submission detected" in copy_match["difference_summary"]
    assert any(ref.get("observation") == "Screening signal only; not a plagiarism verdict." for ref in copy_match["evidence_references"])


# =====================================================================
# 29. Insufficient Evidence Scoring on Missing Problem Statement
# =====================================================================

def test_insufficient_evidence_scoring_on_missing_problem(db_session: Session):
    _create_test_project(
        db_session,
        "no-prob-proj",
        title="Generic Project",
        has_readme=False,
        file_names=["test.py"],
        sections=None,
    )
    profile = ProjectProfileExtractor.extract_profile(db_session, "no-prob-proj")
    mock_matches = [
        {
            "compared_project_id": "other-proj",
            "problem_similarity": 0.0,
            "solution_similarity": 0.0,
            "feature_similarity": 0.2,
            "overall_similarity": 0.1,
        }
    ]

    cat, scores, limitations = InnovationScoringEngine.evaluate(profile, cohort_size=1, matches=mock_matches)
    # Problem distinctiveness must be None (Insufficient Evidence), not a false 100% (1.0 - 0.0)
    assert scores["problem_distinctiveness"] is None
    assert scores["solution_distinctiveness"] is None


# =====================================================================
# 30. Phase 9: Five Feature Classes & Confidence Classifications
# =====================================================================

def test_innovation_five_feature_classes(db_session: Session):
    """Verify all 5 feature classes: verified_match, documented_feature, detected_implementation, unverified_claim, proposed_future."""
    from app.services.innovation.profile import EvidenceType, FeatureEvidence

    # Setup project with documented features and future roadmap section
    _create_test_project(
        db_session,
        "p-feat-classes",
        title="Multi Feature Project",
        has_readme=True,
        file_names=["drone_controller.py", "auth_service.py", "telemetry_hub.py"],
        sections=[
            {
                "heading": "Features & Capabilities",
                "content": "- Drone Controller Engine\n- User Authentication System\n- Blockchain Ledger",
            },
            {
                "heading": "Future Scope & Roadmap",
                "content": "- Autonomous Swarm Navigation",
            }
        ]
    )

    profile = ProjectProfileExtractor.extract_profile(db_session, "p-feat-classes")
    types = {f.evidence_type for f in profile.features}

    # Should have verified match (drone controller in drone_controller.py)
    assert EvidenceType.VERIFIED_MATCH in types or "verified_match" in types
    # Should have proposed future (from Future Scope section)
    assert EvidenceType.PROPOSED_FUTURE in types or "proposed_future" in types
    # Should have unverified claim (Blockchain Ledger has no code)
    assert EvidenceType.UNVERIFIED_CLAIM in types or "unverified_claim" in types


def test_innovation_confidence_classification_and_rationale(db_session: Session):
    """Verify confidence classification calculation and persistence in API schema."""
    _create_test_project(
        db_session,
        "p-conf-test",
        title="Confidence Test Project",
        has_readme=True,
        file_names=["main.py", "auth.py"],
        sections=[
            {
                "heading": "Core Features",
                "content": "- User Authentication Module",
            }
        ]
    )

    res = InnovationService.analyze_project(db_session, "p-conf-test", call_llm=False)
    assert res.confidence_classification in (
        "Directly Verified",
        "Strong Evidence",
        "Moderate Evidence",
        "Indirect Evidence",
        "Insufficient Evidence",
    )
    assert res.confidence_rationale is not None
    assert len(res.confidence_rationale) > 10


def test_gemini_client_innovation_interpretation_mock(monkeypatch):
    """Verify OpenRouterClient._interpret_innovation_gemini validates schema."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-gemini-key")
    monkeypatch.setattr(settings, "LLM_ENABLED", True)

    client = OpenRouterClient.__new__(OpenRouterClient)
    client.enabled = True
    client.is_gemini = True

    mock_payload = {
        "interpretation_status": "completed",
        "innovation_summary": "Distinctive approach to telemetry handling.",
        "problem_understanding": "Addresses real-time IoT drone communication.",
        "proposed_solution_understanding": "Uses event-driven Python pipeline.",
        "potential_contributions": ["Low latency queue."],
        "distinctive_elements": ["Custom CRC checksum routing."],
        "cohort_comparison_interpretation": "More granular than typical cohort projects.",
        "evidence_references": [{"evidence_id": "FEAT-1", "observation": "Custom CRC check."}],
        "alternative_explanations": ["May use standard pyserial logic."],
        "faculty_follow_up_recommendations": ["Ask candidate how packet drops are handled."],
        "innovation_strengths": ["Robust serialization."],
        "missing_evidence": ["No load testing documentation found."],
        "improvement_recommendations": ["Add automated load simulation benchmarks."],
        "confidence_classification": "Directly Verified",
        "confidence_rationale": "Code implementation directly matches documentation.",
        "limitations": []
    }

    mock_resp = SimpleNamespace(text=json.dumps(mock_payload))
    client.gemini_client = SimpleNamespace(
        models=SimpleNamespace(
            generate_content=lambda **kwargs: mock_resp
        )
    )

    interp = client.interpret_innovation(
        user_prompt="Sample prompt",
        valid_evidence_ids=["FEAT-1"],
        discard_invalid_references=True
    )

    assert interp.interpretation_status == "completed"
    assert "Distinctive approach" in interp.innovation_summary
    assert len(interp.innovation_strengths) == 1
    assert interp.confidence_classification == "Directly Verified"


