"""
test_documentation.py

Comprehensive test suite for Phase 5:
- Markdown, TXT, RST extraction with heading detection
- PDF text extraction and scanned image detection
- DOCX extraction with paragraphs and tables
- Corrupt, encrypted, and unsupported documents
- Empty or minimal documentation handling (insufficient evidence)
- Section recognition (Abstract, Intro, Setup, Testing, Architecture, etc.)
- Deterministic documentation quality scoring and issue findings
- Technology consistency checks (verified matches vs potential inconsistencies)
- Component and file reference checks
- Numerical performance claims detection
- Re-analysis idempotency (no duplicate database records)
- API endpoint contracts and 404 handling
"""

import io
import zipfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pymupdf
import docx

from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentItem,
    ProjectDocumentationFinding,
)
from app.services.documentation.extractor import DocumentExtractor, ExtractedDocument, DocumentSection
from app.services.documentation.analyzer import DocumentationAnalyzer
from app.services.documentation.consistency import ConsistencyAnalyzer
from app.services.documentation.service import DocumentationService


def test_markdown_extraction_and_heading_detection(tmp_path: Path):
    """Test markdown extraction with # and underline headings."""
    md_file = tmp_path / "README.md"
    md_file.write_text(
        "# ProjectLens Academic Platform\n\n"
        "This is the project overview and introduction.\n\n"
        "## Setup and Installation\n\n"
        "Run `npm install` and `npm run dev` to start.\n\n"
        "System Architecture\n"
        "-------------------\n\n"
        "React frontend communicating with FastAPI backend.\n\n"
        "## Testing and Evaluation\n\n"
        "Execute `pytest` for all backend unit tests.\n",
        encoding="utf-8",
    )

    doc = DocumentExtractor.extract(md_file, "README.md")
    assert doc.status == "success"
    assert doc.file_format == "markdown"
    assert doc.word_count > 20
    assert "ProjectLens Academic Platform" in doc.headings
    assert "Setup and Installation" in doc.headings
    assert "System Architecture" in doc.headings
    assert "Testing and Evaluation" in doc.headings
    assert len(doc.sections) >= 3


def test_plaintext_and_rst_extraction(tmp_path: Path):
    """Test plain text and reStructuredText heading detection."""
    txt_file = tmp_path / "REPORT.txt"
    txt_file.write_text(
        "1. INTRODUCTION\n\n"
        "This project solves academic evaluation challenges.\n\n"
        "2. SYSTEM ARCHITECTURE\n\n"
        "A modular microservice architecture.\n\n"
        "3. RESULTS\n\n"
        "Achieved strong performance across all test suites.\n",
        encoding="utf-8",
    )

    doc_txt = DocumentExtractor.extract(txt_file, "REPORT.txt")
    assert doc_txt.file_format == "text"
    assert doc_txt.status == "success"
    assert len(doc_txt.headings) >= 2

    rst_file = tmp_path / "docs.rst"
    rst_file.write_text(
        "Specification Document\n"
        "======================\n\n"
        "Methodology\n"
        "-----------\n\n"
        "Proposed approach and development workflow.\n",
        encoding="utf-8",
    )
    doc_rst = DocumentExtractor.extract(rst_file, "docs.rst")
    assert doc_rst.file_format == "rst"
    assert "Specification Document" in doc_rst.headings
    assert "Methodology" in doc_rst.headings


def test_pdf_text_extraction(tmp_path: Path):
    """Test extracting real text from a PDF generated using PyMuPDF."""
    pdf_path = tmp_path / "project_report.pdf"
    doc_pdf = pymupdf.open()
    page = doc_pdf.new_page()
    page.insert_text(
        pymupdf.Point(50, 72),
        "1. Introduction\nThis is a student project report on evaluation systems.\n\n"
        "2. System Architecture\nThe architecture consists of FastAPI and PostgreSQL.\n\n"
        "3. Testing and Results\nAll test cases passed with 95% test pass rate.\n",
    )
    doc_pdf.save(str(pdf_path))
    doc_pdf.close()

    extracted = DocumentExtractor.extract(pdf_path, "project_report.pdf")
    assert extracted.file_format == "pdf"
    assert extracted.status in ("success", "partial")
    assert extracted.page_count == 1
    assert extracted.word_count > 15
    assert "Introduction" in extracted.text
    assert "System Architecture" in extracted.text


def test_pdf_empty_scanned_image_detection(tmp_path: Path):
    """Test PDF with zero text is flagged as empty_scanned_image."""
    pdf_path = tmp_path / "scanned_doc.pdf"
    doc_pdf = pymupdf.open()
    doc_pdf.new_page()  # Blank page with no text
    doc_pdf.save(str(pdf_path))
    doc_pdf.close()

    extracted = DocumentExtractor.extract(pdf_path, "scanned_doc.pdf")
    assert extracted.file_format == "pdf"
    assert extracted.status == "empty_scanned_image"
    assert extracted.word_count == 0
    assert "scanned images" in extracted.warning.lower()


def test_docx_extraction(tmp_path: Path):
    """Test DOCX extraction including headings and tables."""
    docx_path = tmp_path / "srs.docx"
    doc = docx.Document()
    doc.add_heading("1. Software Requirements Specification", level=1)
    doc.add_paragraph("This document specifies functional and non-functional requirements.")
    doc.add_heading("2. System Design", level=2)
    doc.add_paragraph("Detailed system component specifications.")
    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Module"
    table.rows[0].cells[1].text = "Status"
    table.rows[1].cells[0].text = "Authentication"
    table.rows[1].cells[1].text = "Implemented"
    doc.save(str(docx_path))

    extracted = DocumentExtractor.extract(docx_path, "srs.docx")
    assert extracted.file_format == "docx"
    assert extracted.status == "success"
    assert extracted.word_count > 10
    assert "Software Requirements Specification" in extracted.text
    assert "Authentication" in extracted.text


def test_corrupt_or_unsupported_files(tmp_path: Path):
    """Test that corrupt PDF or unsupported files are handled safely without exceptions."""
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"%PDF-1.4 Not a valid PDF binary content")

    extracted = DocumentExtractor.extract(corrupt_pdf, "corrupt.pdf")
    assert extracted.status == "corrupt_or_encrypted"
    assert extracted.warning is not None

    unsupported = tmp_path / "data.xyz"
    unsupported.write_text("random data")
    extracted_unsupported = DocumentExtractor.extract(unsupported, "data.xyz")
    assert extracted_unsupported.status == "unsupported"


def test_empty_or_minimal_documentation():
    """Test that projects with < 50 words produce insufficient_evidence status and no fabricated score."""
    minimal_doc = ExtractedDocument(
        relative_path="README.md",
        filename="README.md",
        file_format="markdown",
        text="# Project\nJust a test project.",
        char_count=30,
        word_count=5,
        page_count=1,
        status="success",
        headings=["Project"],
        sections=[],
    )

    (
        metrics,
        coverage,
        prelim_score,
        score_expl,
        findings,
        warnings,
    ) = DocumentationAnalyzer.analyze_documents([minimal_doc])

    assert metrics.total_words == 5
    assert prelim_score is None
    assert score_expl["status"] == "insufficient_evidence"
    assert any(f["rule_id"] == "DOC_MINIMAL_CONTENT" for f in findings)


def test_missing_recommended_sections_findings():
    """Test that missing required sections generate diagnostic findings."""
    doc = ExtractedDocument(
        relative_path="README.md",
        filename="README.md",
        file_format="markdown",
        text=(
            "# Introduction\n"
            "This is an extensive description of the problem statement and background. " * 10 + "\n"
        ),
        char_count=800,
        word_count=90,
        page_count=1,
        status="success",
        headings=["Introduction"],
        sections=[],
    )

    (
        metrics,
        coverage,
        prelim_score,
        score_expl,
        findings,
        warnings,
    ) = DocumentationAnalyzer.analyze_documents([doc])

    assert prelim_score is not None
    rule_ids = {f["rule_id"] for f in findings}
    assert "DOC_SETUP_MISSING" in rule_ids
    assert "DOC_TESTING_MISSING" in rule_ids
    assert "DOC_ARCHITECTURE_MISSING" in rule_ids


def test_repeated_sections_detection():
    """Test detection of repetitive/copied content across sections."""
    repeated_text = "This is a detailed paragraph explaining algorithm complexity and data processing pipelines. " * 3
    doc1 = ExtractedDocument(
        relative_path="README.md",
        filename="README.md",
        file_format="markdown",
        text=f"# Overview\n{repeated_text}\n# Details\n{repeated_text}",
        char_count=len(repeated_text) * 2,
        word_count=len(repeated_text.split()) * 2,
        page_count=1,
        status="success",
        headings=["Overview", "Details"],
        sections=[
            DocumentSection(heading="Overview", content=repeated_text),
            DocumentSection(heading="Details", content=repeated_text),
        ],
    )

    (
        metrics,
        coverage,
        prelim_score,
        score_expl,
        findings,
        warnings,
    ) = DocumentationAnalyzer.analyze_documents([doc1])

    assert len(metrics.repetition_warnings) > 0


def test_technology_consistency_claim_verified_and_mismatch(tmp_path: Path):
    """Test verified technology vs potential inconsistency finding."""
    src_file = tmp_path / "main.py"
    src_file.write_text("from fastapi import FastAPI\napp = FastAPI()\n", encoding="utf-8")

    manifest = tmp_path / "requirements.txt"
    manifest.write_text("fastapi>=0.115.0\nuvicorn\n", encoding="utf-8")

    doc = ExtractedDocument(
        relative_path="README.md",
        filename="README.md",
        file_format="markdown",
        text=(
            "# Project Stack\n\n"
            "The backend is built with FastAPI.\n\n"
            "We also use Flask for microservices.\n"
        ),
        char_count=120,
        word_count=18,
        page_count=1,
        status="success",
        headings=["Project Stack"],
        sections=[],
    )

    files = [
        ProjectFile(project_id="test_p", relative_path="main.py", filename="main.py", category="Source Code", detected_language="Python"),
        ProjectFile(project_id="test_p", relative_path="requirements.txt", filename="requirements.txt", category="Dependency or Environment", detected_language=None),
    ]

    findings = ConsistencyAnalyzer.analyze(
        documents=[doc],
        structure=None,
        files=files,
        project_dir=tmp_path,
    )

    tech_findings = [f for f in findings if f["category"] == "technology_consistency"]
    verified = [f for f in tech_findings if f["verification_status"] == "verified"]
    unverified = [f for f in tech_findings if f["verification_status"] == "potential_inconsistency"]

    assert any("FastAPI" in f["title"] for f in verified)
    assert any("Flask" in f["title"] for f in unverified)


def test_implementation_endpoint_and_numerical_claims(tmp_path: Path):
    """Test API route matching and numerical performance claim detection."""
    api_file = tmp_path / "routes.py"
    api_file.write_text(
        '@app.get("/api/students")\ndef get_students(): return []\n',
        encoding="utf-8",
    )

    doc = ExtractedDocument(
        relative_path="API.md",
        filename="API.md",
        file_format="markdown",
        text=(
            "# API Endpoints\n\n"
            "GET /api/students returns student records.\n\n"
            "POST /api/evaluations creates a new evaluation.\n\n"
            "## Benchmark Results\n\n"
            "Our model achieved 98.5% accuracy with 15ms latency.\n"
        ),
        char_count=200,
        word_count=28,
        page_count=1,
        status="success",
        headings=["API Endpoints", "Benchmark Results"],
        sections=[],
    )

    files = [
        ProjectFile(project_id="test_p", relative_path="routes.py", filename="routes.py", category="Source Code", detected_language="Python"),
    ]

    findings = ConsistencyAnalyzer.analyze(
        documents=[doc],
        structure=None,
        files=files,
        project_dir=tmp_path,
    )

    endpoint_verified = [f for f in findings if f["rule_id"] == "CLAIM_ENDPOINT_VERIFIED"]
    endpoint_unverified = [f for f in findings if f["rule_id"] == "CLAIM_ENDPOINT_UNVERIFIED"]
    num_claims = [f for f in findings if f["category"] == "numerical_claim"]

    assert any("/api/students" in f["title"] for f in endpoint_verified)
    assert any("/api/evaluations" in f["title"] for f in endpoint_unverified)
    assert len(num_claims) >= 2
    assert all(f["verification_status"] == "claim_not_verified" for f in num_claims)


def test_documentation_api_and_idempotent_reanalysis(client: TestClient, db_session: Session):
    """Test POST analyze endpoint, GET endpoint, and safe re-analysis idempotency."""
    # 1. Create a project zip in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "README.md",
            "# ProjectLens Test Project\n\n"
            "## Introduction\n"
            "An academic project evaluation system solving project tracking challenges.\n\n"
            "## Setup and Installation\n"
            "Run `pip install -r requirements.txt` and `python main.py` to start.\n\n"
            "## Architecture and System Design\n"
            "Built with FastAPI and React.\n\n"
            "## Implementation Details\n"
            "Core modules implemented in Python.\n\n"
            "## Testing and Results\n"
            "Achieved 96.2% accuracy in our tests.\n"
            "Endpoint GET /api/items is available.\n",
        )
        zf.writestr("requirements.txt", "fastapi>=0.115.0\nuvicorn\n")
        zf.writestr("main.py", "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/api/items')\ndef items(): return []\n")
    zip_bytes = zip_buf.getvalue()

    # 2. Upload project
    upload_res = client.post(
        "/api/projects/upload",
        files={"file": ("project_phase5.zip", zip_bytes, "application/zip")},
        data={"title": "Phase 5 Test Project"},
    )
    assert upload_res.status_code == 201
    project_id = upload_res.json()["projectId"]

    # 3. Initial GET documentation (before analysis)
    get_init = client.get(f"/api/projects/{project_id}/documentation")
    assert get_init.status_code == 200
    init_data = get_init.json()
    assert init_data["status"] == "not_started"

    # 4. Run documentation analysis
    post_res = client.post(f"/api/projects/{project_id}/analyze/documentation")
    assert post_res.status_code == 200
    doc_data = post_res.json()
    assert doc_data["status"] == "completed"
    assert doc_data["preliminaryScore"] is not None
    assert doc_data["preliminaryScore"] > 50.0
    assert doc_data["metricsSummary"]["hasReadme"] is True
    assert doc_data["metricsSummary"]["hasSetupInstructions"] is True
    assert doc_data["metricsSummary"]["hasTestingSection"] is True

    # Check verified technology
    findings = doc_data["findings"]
    assert any("FastAPI" in f["title"] and f["verificationStatus"] == "verified" for f in findings)
    assert any("accuracy" in f["title"].lower() and f["verificationStatus"] == "claim_not_verified" for f in findings)

    # 5. GET saved documentation endpoint
    get_saved = client.get(f"/api/projects/{project_id}/documentation")
    assert get_saved.status_code == 200
    assert get_saved.json()["projectId"] == project_id

    # 6. Re-run analysis (idempotency check: exactly 1 database record)
    post_reanalysis = client.post(f"/api/projects/{project_id}/analyze/documentation")
    assert post_reanalysis.status_code == 200

    db_records = (
        db_session.query(ProjectDocumentationAnalysis)
        .filter(ProjectDocumentationAnalysis.project_id == project_id)
        .all()
    )
    assert len(db_records) == 1

    # 7. Check unified analysis bundle
    bundle_res = client.get(f"/api/projects/{project_id}/analysis")
    assert bundle_res.status_code == 200
    bundle_data = bundle_res.json()
    doc_module = next((m for m in bundle_data["modules"] if m["name"] == "Documentation & Development"), None)
    assert doc_module is not None
    assert doc_module["status"] == "completed"
    assert bundle_data["documentation"] is not None
    assert len(bundle_data["documentation"]["docChecks"]) > 0


def test_documentation_nonexistent_project_404(client: TestClient):
    """Test 404 response for nonexistent project ID."""
    res_post = client.post("/api/projects/nonexistent_12345/analyze/documentation")
    assert res_post.status_code == 404

    res_get = client.get("/api/projects/nonexistent_12345/documentation")
    assert res_get.status_code == 404
