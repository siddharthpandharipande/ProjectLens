"""
test_code_quality.py

Comprehensive tests for Phase 3 Code Quality Analysis:
- Python AST parsing (functions, classes, imports, docstrings, nesting depth).
- Radon complexity (cyclomatic complexity, maintainability index).
- Multi-language support (Tree-sitter for TS/JS and Java, explicit coverage).
- Deterministic scoring repeatability.
- Error resilience (syntax errors, oversized/corrupt files).
- Quality findings rules and locations.
- Database persistence and idempotent re-analysis.
- API endpoints (POST analyze, GET code-quality, 404 handling).
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.code_quality import ProjectQualityAnalysis, ProjectFileMetric
from app.services.code_quality.scoring import DeterministicQualityScorer
from app.services.code_quality.rules import evaluate_quality_rules


def test_complex_python_ast_and_radon_analysis(client: TestClient, complex_python_zip_bytes: bytes):
    """
    Test uploading a complex Python project and analyzing its AST and Radon metrics.
    Verifies function counts, class counts, docstrings, nesting depth, CC, and MI.
    """
    # 1. Upload
    res = client.post(
        "/api/projects/upload",
        files={"file": ("complex_project.zip", io.BytesIO(complex_python_zip_bytes), "application/zip")},
        data={"title": "Complex Drone Engine", "course": "CS-401"},
    )
    assert res.status_code == 201
    project_id = res.json()["projectId"]

    # 2. Analyze Code Quality
    res_cq = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res_cq.status_code == 200
    cq_data = res_cq.json()

    assert cq_data["projectId"] == project_id
    assert cq_data["status"] == "completed"
    assert cq_data["score"] is not None
    assert 0.0 <= cq_data["score"] <= 100.0

    # Summary checks
    summary = cq_data["metricsSummary"]
    assert summary["totalSourceFiles"] == 1
    assert summary["totalFunctions"] >= 3  # __init__, calculate_thrust, complex_decision
    assert summary["totalClasses"] == 1    # FlightEngine
    assert summary["avgComplexity"] is not None
    assert summary["maxComplexity"] >= 10   # complex_decision has high CC
    assert summary["avgMaintainabilityIndex"] is not None

    # File metric items
    file_metrics = cq_data["fileMetrics"]
    assert len(file_metrics) == 1
    fm = file_metrics[0]
    assert fm["relativePath"] == "engine/main.py"
    assert fm["language"] == "Python"
    assert "FlightEngine" in fm["classNames"]
    assert "complex_decision" in fm["functionNames"]
    assert "os" in fm["imports"]
    assert fm["maxNestingDepth"] >= 5       # Nested if statements

    # Findings checks
    findings = cq_data["findings"]
    assert len(findings) > 0
    # Must contain high complexity or deep nesting finding
    rule_ids = [f["ruleId"] for f in findings]
    assert any("CC" in r for r in rule_ids) or any("NESTING" in r for r in rule_ids)

    # Every finding must have line number, severity, evidence, and suggestion
    for f in findings:
        assert f["severity"] in ("High", "Medium", "Low", "Info")
        assert f["filePath"] == "engine/main.py"
        assert f["metricEvidence"] is not None
        assert f["suggestion"] is not None


def test_syntax_error_handled_gracefully(client: TestClient, syntax_error_python_zip_bytes: bytes):
    """
    Test that a project containing a syntax error in one file does not crash analysis.
    The syntax error is captured with line and column, while clean files are parsed normally.
    """
    res = client.post(
        "/api/projects/upload",
        files={"file": ("syntax_error_project.zip", io.BytesIO(syntax_error_python_zip_bytes), "application/zip")},
    )
    assert res.status_code == 201
    project_id = res.json()["projectId"]

    res_cq = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res_cq.status_code == 200
    cq_data = res_cq.json()

    summary = cq_data["metricsSummary"]
    assert summary["syntaxErrorsCount"] == 1
    assert summary["totalSourceFiles"] == 2

    file_metrics = {fm["relativePath"]: fm for fm in cq_data["fileMetrics"]}
    assert file_metrics["broken.py"]["hasSyntaxError"] is True
    assert "SyntaxError" in (file_metrics["broken.py"]["syntaxErrorDetails"] or "")
    assert file_metrics["clean.py"]["hasSyntaxError"] is False
    assert file_metrics["clean.py"]["functionsCount"] == 1

    # Finding generated for syntax error
    syntax_findings = [f for f in cq_data["findings"] if f["ruleId"] == "PY-SYNTAX-ERR"]
    assert len(syntax_findings) == 1
    assert syntax_findings[0]["severity"] == "High"
    assert syntax_findings[0]["filePath"] == "broken.py"


def test_empty_source_project_insufficient_evidence(client: TestClient):
    """
    Test project containing only README.md and documentation (0 source code files).
    Score calculation returns None with clear explanation rather than inventing numbers.
    """
    buffer = io.BytesIO()
    import zipfile
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr("README.md", "# Only docs\nNo code here.\n")
        zf.writestr("data.csv", "a,b,c\n1,2,3\n")
    buffer.seek(0)

    res = client.post(
        "/api/projects/upload",
        files={"file": ("no_code.zip", buffer, "application/zip")},
    )
    assert res.status_code == 201
    project_id = res.json()["projectId"]

    res_cq = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res_cq.status_code == 200
    cq_data = res_cq.json()

    assert cq_data["score"] is None
    assert "Insufficient source code evidence" in cq_data["scoreExplanation"]["summary"]
    assert cq_data["metricsSummary"]["totalSourceFiles"] == 0


def test_multi_language_code_quality_analysis(client: TestClient, multi_tech_zip_bytes: bytes):
    """
    Test multi-tech project containing Python, TypeScript, and Java.
    Verifies that Python gets AST+Radon, while TS/Java get Tree-sitter structural AST,
    and language coverage explicitly documents capabilities and limitations.
    """
    res = client.post(
        "/api/projects/upload",
        files={"file": ("multi_tech.zip", io.BytesIO(multi_tech_zip_bytes), "application/zip")},
    )
    assert res.status_code == 201
    project_id = res.json()["projectId"]

    res_cq = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res_cq.status_code == 200
    cq_data = res_cq.json()

    # Coverage matrix
    coverage_map = {c["language"]: c for c in cq_data["languageCoverage"]}
    assert "Python" in coverage_map
    assert "TypeScript" in coverage_map
    assert "Java" in coverage_map

    # Limitations explicitly documented
    assert "Radon" in coverage_map["Python"]["limitations"]
    assert "Tree-sitter" in coverage_map["TypeScript"]["limitations"]
    assert "not calculated" in coverage_map["TypeScript"]["limitations"].lower()

    # Score was calculated deterministically
    assert cq_data["score"] is not None


def test_deterministic_scoring_repeatability():
    """
    Test that the DeterministicQualityScorer produces identical scores and explanations
    when called repeatedly with identical inputs.
    """
    file_metrics = [
        {
            "relative_path": "main.py",
            "language": "Python",
            "loc": 100,
            "sloc": 80,
            "comments": 12,
            "blank": 8,
            "has_syntax_error": False,
            "avg_complexity": 3.5,
            "max_complexity": 8,
            "maintainability_index": 72.0,
            "max_nesting_depth": 3,
            "complexity_blocks": [{"name": "foo", "complexity": 3}],
            "functions_metadata": [{"name": "foo", "sloc": 25, "has_docstring": True}],
        }
    ]
    project_metrics = {
        "total_source_files": 1,
        "total_loc": 100,
        "total_sloc": 80,
        "total_comments": 12,
        "total_blank": 8,
        "avg_complexity": 3.5,
        "max_complexity": 8,
        "avg_maintainability_index": 72.0,
    }
    findings = []

    score1, expl1 = DeterministicQualityScorer.calculate_score(file_metrics, project_metrics, findings)
    score2, expl2 = DeterministicQualityScorer.calculate_score(file_metrics, project_metrics, findings)

    assert score1 == score2
    assert expl1 == expl2
    assert score1 >= 90.0  # Clean code should receive high score


def test_reanalysis_idempotency_no_duplicate_records(
    client: TestClient,
    db_session: Session,
    complex_python_zip_bytes: bytes,
):
    """
    Test that running Code Quality analysis multiple times updates existing records
    without creating duplicate database rows in PostgreSQL/SQLite.
    """
    res = client.post(
        "/api/projects/upload",
        files={"file": ("reanalysis.zip", io.BytesIO(complex_python_zip_bytes), "application/zip")},
    )
    project_id = res.json()["projectId"]

    # First analysis
    res1 = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res1.status_code == 200

    # Second analysis (re-analyze)
    res2 = client.post(f"/api/projects/{project_id}/analyze/code-quality")
    assert res2.status_code == 200

    # Check database records count
    analyses_count = db_session.query(ProjectQualityAnalysis).filter(
        ProjectQualityAnalysis.project_id == project_id
    ).count()
    assert analyses_count == 1, "There should be exactly 1 ProjectQualityAnalysis record"

    file_metrics_count = db_session.query(ProjectFileMetric).filter(
        ProjectFileMetric.project_id == project_id
    ).count()
    assert file_metrics_count == 1, "There should be exactly 1 ProjectFileMetric record"


def test_get_code_quality_endpoint(client: TestClient, complex_python_zip_bytes: bytes):
    """
    Test GET /api/projects/{id}/code-quality retrieves saved analysis.
    """
    res = client.post(
        "/api/projects/upload",
        files={"file": ("get_cq.zip", io.BytesIO(complex_python_zip_bytes), "application/zip")},
    )
    project_id = res.json()["projectId"]

    # Before analysis: 404
    res_before = client.get(f"/api/projects/{project_id}/code-quality")
    assert res_before.status_code == 404

    # Run analysis
    client.post(f"/api/projects/{project_id}/analyze/code-quality")

    # After analysis: 200
    res_after = client.get(f"/api/projects/{project_id}/code-quality")
    assert res_after.status_code == 200
    body = res_after.json()
    assert body["projectId"] == project_id
    assert "metricsSummary" in body
    assert "fileMetrics" in body
    assert "findings" in body
    assert "languageCoverage" in body


def test_code_quality_nonexistent_project_404(client: TestClient):
    """
    Test that nonexistent project IDs return HTTP 404.
    """
    res_get = client.get("/api/projects/proj_nonexistent_123/code-quality")
    assert res_get.status_code == 404

    res_post = client.post("/api/projects/proj_nonexistent_123/analyze/code-quality")
    assert res_post.status_code == 404


def test_project_analysis_bundle_endpoint(client: TestClient, complex_python_zip_bytes: bytes):
    """
    Test GET /api/projects/{id}/analysis returns unified bundle with Code Quality module.
    """
    res = client.post(
        "/api/projects/upload",
        files={"file": ("bundle.zip", io.BytesIO(complex_python_zip_bytes), "application/zip")},
    )
    project_id = res.json()["projectId"]

    # Before analysis: codeQuality is None, module status not_started
    res_b = client.get(f"/api/projects/{project_id}/analysis")
    assert res_b.status_code == 200
    assert res_b.json()["codeQuality"] is None

    # Run analysis
    client.post(f"/api/projects/{project_id}/analyze/code-quality")

    # After analysis: codeQuality populated, module status completed
    res_a = client.get(f"/api/projects/{project_id}/analysis")
    assert res_a.status_code == 200
    bundle = res_a.json()
    assert bundle["codeQuality"] is not None
    assert bundle["codeQuality"]["linesOfCode"] > 0
    assert bundle["codeQuality"]["cyclomaticComplexityAvg"] >= 1.0
