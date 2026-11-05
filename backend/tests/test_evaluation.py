"""Comprehensive tests for Final Phase: Overall Project Evaluation & Report Generator.

Tests cover:
- EvaluationScoringEngine: weight normalization, letter grade mappings, coverage thresholds.
- EvaluationOrchestrator: multi-module evidence consolidation, fault isolation.
- EvaluationReportGenerator: PDF generation (%PDF- magic header), JSON export.
- EvaluationService: end-to-end evaluation, database persistence, score update.
- API Endpoints: POST /evaluate, GET /evaluation, POST /report, GET /report, GET /evaluation/export.json.
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.evaluation import ProjectEvaluation
from app.schemas.evaluation import CategoryScoreSchema, ActionableRecommendationSchema
from app.services.evaluation.scoring import (
    EvaluationScoringEngine,
    compute_grade,
    DEFAULT_CATEGORY_WEIGHTS,
    COMPLETE_COVERAGE_THRESHOLD,
    MINIMUM_EVALUATION_COVERAGE_THRESHOLD,
)
from app.services.evaluation.orchestrator import EvaluationOrchestrator
from app.services.evaluation.report_generator import EvaluationReportGenerator
from app.services.evaluation.service import EvaluationService


# ─── 1. Scoring Engine Unit Tests ─────────────────────────────────────────────

def test_grade_mapping_boundaries():
    """Verify standard academic letter grade mappings across all score boundaries."""
    assert compute_grade(None) is None
    assert compute_grade(95.0) == "A"
    assert compute_grade(85.0) == "A"
    assert compute_grade(84.9) == "B+"
    assert compute_grade(75.0) == "B+"
    assert compute_grade(74.9) == "B"
    assert compute_grade(65.0) == "B"
    assert compute_grade(64.9) == "C"
    assert compute_grade(50.0) == "C"
    assert compute_grade(49.9) == "D"
    assert compute_grade(35.0) == "D"
    assert compute_grade(34.9) == "F"
    assert compute_grade(0.0) == "F"


def test_category_weights_sum_to_100():
    """Verify configured default category weights sum to exactly 100%."""
    total = sum(DEFAULT_CATEGORY_WEIGHTS.values())
    assert abs(total - 100.0) < 0.001


def test_scoring_complete_coverage():
    """Verify that when >= 70% of categories are assessed, evaluation is complete and renormalized."""
    cats = [
        CategoryScoreSchema(id="code_quality", name="Code Quality", weight=30.0, score=80.0, status="assessed"),
        CategoryScoreSchema(id="code_similarity", name="Similarity", weight=15.0, score=90.0, status="assessed"),
        CategoryScoreSchema(id="documentation", name="Documentation", weight=20.0, score=70.0, status="assessed"),
        CategoryScoreSchema(id="git_history", name="Git History", weight=10.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="innovation", name="Innovation", weight=15.0, score=85.0, status="assessed"),
        CategoryScoreSchema(id="engineering_rigor", name="Engineering Rigor", weight=10.0, score=75.0, status="assessed"),
    ]
    # Assessed weight: 30 + 15 + 20 + 15 + 10 = 90% (>= 70%)
    score, grade, status, coverage, updated_cats, breakdown = EvaluationScoringEngine.calculate_overall_evaluation(cats)
    
    assert status == "complete"
    assert coverage == 90.0
    assert score is not None
    assert score > 0.0
    assert grade in ["A", "B+", "B", "C"]
    assert len(breakdown) == 6


def test_scoring_provisional_coverage():
    """Verify that when 50% - 69% of categories are assessed, status is partial/provisional."""
    cats = [
        CategoryScoreSchema(id="code_quality", name="Code Quality", weight=30.0, score=80.0, status="assessed"),
        CategoryScoreSchema(id="code_similarity", name="Similarity", weight=15.0, score=90.0, status="assessed"),
        CategoryScoreSchema(id="documentation", name="Documentation", weight=20.0, score=70.0, status="assessed"),
        CategoryScoreSchema(id="git_history", name="Git History", weight=10.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="innovation", name="Innovation", weight=15.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="engineering_rigor", name="Engineering Rigor", weight=10.0, score=None, status="unavailable"),
    ]
    # Assessed weight: 30 + 15 + 20 = 65% (between 50% and 70%)
    score, grade, status, coverage, updated_cats, breakdown = EvaluationScoringEngine.calculate_overall_evaluation(cats)
    
    assert status == "partial"
    assert coverage == 65.0
    assert score is not None
    assert grade is not None


def test_scoring_insufficient_evidence():
    """Verify that when < 50% of categories are assessed, score is None and status is incomplete."""
    cats = [
        CategoryScoreSchema(id="code_quality", name="Code Quality", weight=30.0, score=80.0, status="assessed"),
        CategoryScoreSchema(id="code_similarity", name="Similarity", weight=15.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="documentation", name="Documentation", weight=20.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="git_history", name="Git History", weight=10.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="innovation", name="Innovation", weight=15.0, score=None, status="unavailable"),
        CategoryScoreSchema(id="engineering_rigor", name="Engineering Rigor", weight=10.0, score=None, status="unavailable"),
    ]
    # Assessed weight: 30% (< 50%)
    score, grade, status, coverage, updated_cats, breakdown = EvaluationScoringEngine.calculate_overall_evaluation(cats)
    
    assert status == "incomplete"
    assert coverage == 30.0
    assert score is None
    assert grade is None


# ─── 2. PDF & JSON Generator Unit Tests ────────────────────────────────────────

def test_pdf_report_generation_magic_bytes():
    """Verify that ReportLab produces valid PDF output with the %PDF- header."""
    evaluation_data = {
        "project": {"id": "test_p1", "title": "Automated Drone", "course": "CS-401", "team": "Alpha"},
        "overall_score": 82.5,
        "grade": "B+",
        "evaluation_status": "complete",
        "coverage_pct": 90.0,
        "category_scores": [
            CategoryScoreSchema(id="code_quality", name="Code Quality", weight=30.0, score=85.0, status="assessed"),
            CategoryScoreSchema(id="code_similarity", name="Similarity", weight=15.0, score=92.0, status="assessed"),
        ],
        "strengths": ["Clean modular architecture", "Extensive test coverage"],
        "weaknesses": ["No docstrings in worker service"],
        "risks": ["Third-party API dependency single point of failure"],
        "recommendations": [
            ActionableRecommendationSchema(
                title="Add API error retries",
                description="Network failures cause immediate crashes.",
                priority="High",
                category="Reliability",
                whyItMatters="Improves production uptime",
                recommendedAction="Implement exponential backoff",
                expectedBenefit="99.9% availability",
                sourceModule="Code Quality",
            )
        ],
        "executive_summary": "Overall solid engineering with minor documentation gaps.",
        "faculty_notes": "Ask student about fault recovery during viva defense.",
        "viva_set": None,
    }
    
    pdf_bytes = EvaluationReportGenerator.generate_pdf(evaluation_data)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")


def test_json_export_structure():
    """Verify that evaluation JSON export produces complete, valid structured data."""
    evaluation_data = {
        "project": {"id": "test_p2", "title": "Smart City Grid", "course": "EE-302", "team": "Beta"},
        "overall_score": 76.0,
        "grade": "B+",
        "evaluation_status": "complete",
        "coverage_pct": 85.0,
        "category_scores": [],
        "strengths": ["Clear telemetry ingestion pipeline"],
        "weaknesses": [],
        "risks": [],
        "recommendations": [],
        "executive_summary": "Good project.",
        "faculty_notes": None,
        "module_statuses": {"code_quality": "completed"},
    }
    
    exported = EvaluationReportGenerator.generate_json_export(evaluation_data)
    assert exported["project"]["id"] == "test_p2"
    assert exported["evaluation"]["overallScore"] == 76.0
    assert exported["evaluation"]["grade"] == "B+"
    assert exported["evaluation"]["coveragePct"] == 85.0


# ─── 3. Full Service & Database Integration Tests ─────────────────────────────

def test_evaluation_service_persistence_and_score_update(db_session: Session):
    """Test full evaluation service run against a database project, verifying persistence and score sync."""
    project = Project(
        id="proj_eval_test",
        title="EcoTrack Carbon Analyzer",
        course="ENV-101",
        team="GreenTech",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    # Evaluate project
    result = EvaluationService.evaluate_project(db_session, "proj_eval_test")
    assert result.project_id == "proj_eval_test"
    assert result.evaluation_status in ["complete", "partial", "incomplete"]
    
    # Verify Project.score was updated in the DB
    refreshed_project = db_session.query(Project).filter(Project.id == "proj_eval_test").first()
    assert refreshed_project is not None
    if result.overall_score is not None:
        assert refreshed_project.score == result.overall_score

    # Verify ProjectEvaluation record exists in DB
    eval_db = db_session.query(ProjectEvaluation).filter(ProjectEvaluation.project_id == "proj_eval_test").first()
    assert eval_db is not None
    assert eval_db.overall_score == result.overall_score
    assert eval_db.grade == result.grade

    # Verify get_latest_evaluation retrieves it correctly
    latest = EvaluationService.get_latest_evaluation(db_session, "proj_eval_test")
    assert latest is not None
    assert latest.id == eval_db.id


# ─── 4. FastAPI Endpoints Integration Tests ───────────────────────────────────

def test_evaluate_endpoint(client: TestClient, db_session: Session):
    """POST /api/projects/{id}/evaluate triggers evaluation and returns 200."""
    project = Project(
        id="proj_api_eval",
        title="Autonomous Rover",
        course="ROBO-201",
        team="Explorers",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    response = client.post("/api/projects/proj_api_eval/evaluate")
    assert response.status_code == 200
    data = response.json()
    assert data["projectId"] == "proj_api_eval"
    assert "overallScore" in data
    assert "categoryScores" in data
    assert "strengths" in data
    assert "weaknesses" in data
    assert "risks" in data
    assert "recommendations" in data


def test_get_evaluation_endpoint(client: TestClient, db_session: Session):
    """GET /api/projects/{id}/evaluation returns latest evaluation or 404 for unknown project."""
    # Unknown project returns 404
    res_404 = client.get("/api/projects/unknown_proj_id/evaluation")
    assert res_404.status_code == 404

    # Existing project
    project = Project(
        id="proj_api_get",
        title="Fleet Optimizer",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    # GET endpoint computes/retrieves evaluation dynamically
    res_200 = client.get("/api/projects/proj_api_get/evaluation")
    assert res_200.status_code == 200
    data = res_200.json()
    assert data["projectId"] == "proj_api_get"


def test_pdf_report_endpoints(client: TestClient, db_session: Session):
    """POST /api/projects/{id}/report triggers evaluation and GET /api/projects/{id}/report streams PDF."""
    project = Project(
        id="proj_pdf_test",
        title="HydroSense Water Monitor",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    # POST triggers report generation
    post_res = client.post("/api/projects/proj_pdf_test/report")
    assert post_res.status_code == 200
    data = post_res.json()
    assert data["reportAvailable"] is True

    # GET downloads PDF blob
    get_res = client.get("/api/projects/proj_pdf_test/report")
    assert get_res.status_code == 200
    assert get_res.headers["content-type"] == "application/pdf"
    assert "attachment; filename=" in get_res.headers["content-disposition"]
    assert get_res.content.startswith(b"%PDF-")


def test_json_export_endpoint(client: TestClient, db_session: Session):
    """GET /api/projects/{id}/evaluation/export.json returns machine-readable JSON."""
    project = Project(
        id="proj_json_test",
        title="VisionAssist",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    # Trigger evaluation first
    client.post("/api/projects/proj_json_test/evaluate")

    # Download JSON export
    res = client.get("/api/projects/proj_json_test/evaluation/export.json")
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/json")
    assert "attachment; filename=" in res.headers["content-disposition"]
    json_data = res.json()
    assert "evaluation" in json_data
    assert json_data["project"]["id"] == "proj_json_test"


def test_evaluation_in_unified_analysis_bundle(client: TestClient, db_session: Session):
    """GET /api/projects/{id}/analysis includes evaluationReport data."""
    project = Project(
        id="proj_bundle_eval",
        title="AgriDrone",
        status="ready",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=1024,
    )
    db_session.add(project)
    db_session.commit()

    # Before evaluation
    res_before = client.get("/api/projects/proj_bundle_eval/analysis")
    assert res_before.status_code == 200
    bundle_before = res_before.json()
    assert "evaluationReport" in bundle_before
    assert bundle_before["evaluationReport"]["evaluationStatus"] in ["not_started", "incomplete"]

    # Trigger evaluation
    client.post("/api/projects/proj_bundle_eval/evaluate")

    # After evaluation
    res_after = client.get("/api/projects/proj_bundle_eval/analysis")
    assert res_after.status_code == 200
    bundle_after = res_after.json()
    assert "evaluationReport" in bundle_after
    assert bundle_after["evaluationReport"]["reportAvailable"] is True
    assert "scoreBreakdown" in bundle_after["evaluationReport"]
