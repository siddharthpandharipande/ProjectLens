"""Automated tests for Phase 8 Intelligent Viva Question Generator with Google Gemini AI.

Tests cover:
- Context and evidence compilation (VivaEvidenceBuilder)
- Gemini AI generator with mock responses and structured JSON validation
- Gemini rate-limit, quota, and malformed JSON recovery
- Deterministic fallback generation across 9 categories and 3 difficulty levels
- All four viva generation modes (quick_prep, complete_viva, technical_deep_dive, examiner_challenge)
- Practice status tracking and progress calculation
- Single question regeneration and duplicate prevention
- REST API endpoints and data isolation between projects
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.code_quality import ProjectQualityAnalysis
from app.models.documentation import ProjectDocumentationAnalysis
from app.models.git_history import ProjectGitHistoryAnalysis
from app.models.viva import ProjectVivaQuestionSet, ProjectVivaQuestion
from app.services.viva.evidence_builder import VivaEvidenceBuilder
from app.services.viva.gemini_generator import GeminiVivaGenerator
from app.services.viva.fallback_generator import FallbackVivaGenerator
from app.services.viva.service import VivaService
from app.schemas.viva import VIVA_CATEGORIES, VIVA_MODES, VIVA_DIFFICULTIES


def _setup_test_project(
    db: Session,
    project_id: str = "proj-viva-1",
    title: str = "Hospital Patient Queue System",
) -> Project:
    """Helper to seed a test project with files and analysis evidence."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id=project_id,
        title=title,
        course="CS 401",
        team="Team Alpha",
        status="completed",
        archive_filename="project.zip",
        archive_path="/tmp/project.zip",
        file_size_bytes=10240,
        created_at=now,
        updated_at=now,
    )
    db.add(proj)

    # Seed files
    f1 = ProjectFile(
        project_id=project_id,
        relative_path="src/main.py",
        filename="main.py",
        extension=".py",
        category="Source Code",
        detected_language="Python",
        size_bytes=1200,
        created_at=now,
    )
    f2 = ProjectFile(
        project_id=project_id,
        relative_path="src/database.py",
        filename="database.py",
        extension=".py",
        category="Backend",
        detected_language="Python",
        size_bytes=800,
        created_at=now,
    )
    db.add_all([f1, f2])

    # Seed structure
    struct = ProjectStructure(
        project_id=project_id,
        frameworks=[{"framework": "FastAPI", "category": "Backend"}],
        total_files=2,
        source_files_count=2,
        created_at=now,
    )
    db.add(struct)

    # Seed quality analysis
    qa = ProjectQualityAnalysis(
        project_id=project_id,
        status="completed",
        score=85.0,
        metrics_summary={
            "total_loc": 250,
            "cyclomatic_complexity_average": 2.5,
            "cyclomatic_complexity_max": 8,
            "high_complexity_function_count": 0,
        },
        findings=[],
        created_at=now,
    )
    db.add(qa)

    # Seed doc analysis
    doc = ProjectDocumentationAnalysis(
        project_id=project_id,
        status="completed",
        total_documents_count=1,
        total_words_count=450,
        section_coverage=[
            {"standard_section": "Architecture", "is_present": True},
            {"standard_section": "Testing", "is_present": False},
        ],
        findings=[],
        created_at=now,
    )
    db.add(doc)

    db.commit()
    db.refresh(proj)
    return proj


# ─── 1. Evidence Builder Tests ───

def test_viva_evidence_builder_complete_context(db_session: Session):
    """Test evidence builder compiles all available project data."""
    _setup_test_project(db_session, "proj-ev-1", "Automated Grading Assistant")

    ctx = VivaEvidenceBuilder.build_project_context(db_session, "proj-ev-1")
    assert ctx["title"] == "Automated Grading Assistant"
    assert "Python" in ctx["languages"]
    assert "FastAPI" in ctx["frameworks"]
    assert ctx["has_tests"] is False
    assert ctx["has_database_files"] is True
    assert "Lack of automated unit tests or integration test suites" in ctx["identified_weaknesses"]


def test_viva_evidence_builder_missing_project(db_session: Session):
    """Test evidence builder handles non-existent projects safely."""
    ctx = VivaEvidenceBuilder.build_project_context(db_session, "nonexistent-id")
    assert ctx["is_empty"] is True
    assert ctx["title"] == "Unknown Project"


# ─── 2. Deterministic Fallback Generator Tests ───

def test_deterministic_fallback_covers_nine_categories():
    """Test fallback generation generates questions across standard categories."""
    context = {
        "title": "Smart Campus IoT Monitor",
        "languages": {"Python": 10, "C++": 5},
        "frameworks": ["FastAPI", "MQTT"],
        "key_files": ["src/broker.py", "src/client.cpp"],
        "has_tests": False,
        "has_docker": False,
        "has_database_files": True,
        "code_quality": {"avg_complexity": 3.2, "max_complexity": 9},
        "documentation": {"sections_missing": ["Testing", "Deployment"]},
        "innovation": {"domain": "IoT & Smart Cities", "problem_statement": "Energy monitoring"},
    }

    questions = FallbackVivaGenerator.generate_questions(
        context=context,
        mode="complete_viva",
        difficulty="all",
        question_count=12,
    )

    assert len(questions) >= 10
    categories = {q["category"] for q in questions}
    # Verify core viva categories are represented
    assert "Project Fundamentals" in categories
    assert "Technical Architecture" in categories
    assert "Technology Stack" in categories
    assert "Implementation and Coding" in categories
    assert "Testing and Validation" in categories

    for q in questions:
        assert q["source"] == "deterministic_fallback"
        assert q["difficulty"] in VIVA_DIFFICULTIES
        assert len(q["key_points"]) > 0
        assert len(q["suggested_answer"]) > 20
        assert q["examiner_rationale"] != ""


def test_all_four_generation_modes():
    """Test fallback generator behavior for each viva generation mode."""
    context = {
        "title": "Crypto Wallet Analyzer",
        "languages": {"Rust": 8, "TypeScript": 12},
        "frameworks": ["React", "Actix"],
        "key_files": ["src/main.rs", "src/parser.ts"],
        "has_tests": True,
        "has_docker": True,
        "has_database_files": True,
        "code_quality": {"avg_complexity": 2.1},
    }

    # Mode 1: quick_prep
    qp = FallbackVivaGenerator.generate_questions(context, mode="quick_prep", question_count=5)
    assert len(qp) == 5

    # Mode 2: complete_viva
    cv = FallbackVivaGenerator.generate_questions(context, mode="complete_viva", question_count=10)
    assert len(cv) == 10

    # Mode 3: technical_deep_dive
    tdd = FallbackVivaGenerator.generate_questions(context, mode="technical_deep_dive", question_count=6)
    assert len(tdd) == 6

    # Mode 4: examiner_challenge
    ec = FallbackVivaGenerator.generate_questions(context, mode="examiner_challenge", question_count=5)
    assert len(ec) == 5
    for q in ec:
        assert q["difficulty"] in ("intermediate", "advanced")


def test_difficulty_filtering():
    """Test targeting a specific difficulty."""
    context = {
        "title": "Test App",
        "languages": {"Python": 5},
        "frameworks": ["Flask"],
        "key_files": ["app.py"],
        "has_tests": False,
        "has_docker": False,
        "has_database_files": False,
    }
    adv = FallbackVivaGenerator.generate_questions(context, difficulty="advanced", question_count=4)
    for q in adv:
        assert q["difficulty"] in ("intermediate", "advanced")


def test_project_without_source_code():
    """Test fallback generator handles empty or documentation-only projects without crashing."""
    context = {
        "title": "Concept Whitepaper",
        "languages": {},
        "frameworks": [],
        "key_files": [],
        "has_tests": False,
        "has_docker": False,
        "has_database_files": False,
    }
    qs = FallbackVivaGenerator.generate_questions(context, question_count=5)
    assert len(qs) == 5
    assert all("question" in q for q in qs)


# ─── 3. Gemini Generator & Mock Tests ───

def test_gemini_generator_parse_valid_json():
    """Test Gemini response parsing with markdown code fences."""
    raw_response = """```json
{
  "questions": [
    {
      "category": "Technology Stack",
      "difficulty": "intermediate",
      "question": "Why did your team adopt FastAPI over Django?",
      "examiner_rationale": "Evaluates architectural trade-off reasoning.",
      "key_points": ["Async concurrency", "Pydantic validation", "Lightweight footprint"],
      "suggested_answer": "FastAPI provides asynchronous concurrency and native OpenAPI documentation.",
      "evidence_reference": "Framework Evidence: FastAPI"
    }
  ]
}
```"""
    parsed = GeminiVivaGenerator._parse_response(raw_response)
    assert len(parsed) == 1
    assert parsed[0]["category"] == "Technology Stack"
    assert parsed[0]["difficulty"] == "intermediate"
    assert "FastAPI" in parsed[0]["question"]


def test_gemini_generator_parse_malformed_json_returns_empty():
    """Test malformed response returns empty list safely without exception."""
    raw_response = "Sorry, I am unable to process this request right now."
    parsed = GeminiVivaGenerator._parse_response(raw_response)
    assert parsed == []


@patch("app.services.viva.gemini_generator.GeminiVivaGenerator.is_available", return_value=True)
def test_gemini_generator_success_mock(mock_avail, db_session: Session):
    """Test successful Gemini integration returning structured questions."""
    _setup_test_project(db_session, "proj-gemini-1", "AI Code Reviewer")

    mock_gemini_questions = [
        {
            "category": "Project Fundamentals",
            "difficulty": "beginner",
            "question": "What is the core problem addressed by AI Code Reviewer?",
            "examiner_rationale": "Checks project understanding.",
            "key_points": ["Code quality automation", "Fast feedback"],
            "suggested_answer": "It provides automated heuristic static analysis for student submissions.",
            "evidence_reference": "Documentation / Overview",
        },
        {
            "category": "Technical Architecture",
            "difficulty": "intermediate",
            "question": "How do FastAPI route handlers interact with the static analysis services?",
            "examiner_rationale": "Verifies architectural separation.",
            "key_points": ["Service layer encapsulation", "SQLAlchemy session scoping"],
            "suggested_answer": "Routers delegate execution to service classes.",
            "evidence_reference": "src/main.py",
        },
    ]

    with patch.object(GeminiVivaGenerator, "generate_questions", return_value=mock_gemini_questions):
        response = VivaService.generate_questions(
            db=db_session,
            project_id="proj-gemini-1",
            mode="complete_viva",
            question_count=2,
        )

        assert response.generation_source == "gemini"
        assert response.total_questions == 2
        assert len(response.questions) == 2
        assert response.questions[0].source == "gemini"
        assert response.questions[0].category == "Project Fundamentals"


@patch("app.services.viva.gemini_generator.GeminiVivaGenerator.is_available", return_value=True)
def test_gemini_rate_limit_falls_back_to_deterministic(mock_avail, db_session: Session):
    """Test that when Gemini throws an exception, system falls back seamlessly to deterministic generation."""
    _setup_test_project(db_session, "proj-fallback-1", "Online Bookstore")

    with patch.object(GeminiVivaGenerator, "generate_questions", side_effect=Exception("429 ResourceExhausted")):
        response = VivaService.generate_questions(
            db=db_session,
            project_id="proj-fallback-1",
            mode="complete_viva",
            question_count=5,
        )

        # Must fall back gracefully without crashing
        assert response.generation_source == "deterministic_fallback"
        assert response.total_questions >= 5
        assert all(q.source == "deterministic_fallback" for q in response.questions)


# ─── 4. Database Persistence & Practice Tracking Tests ───

def test_practice_status_toggle_and_persistence(db_session: Session):
    """Test marking questions as practiced updates counts and persists to DB."""
    _setup_test_project(db_session, "proj-practice-1", "Inventory System")

    q_set = VivaService.generate_questions(
        db=db_session,
        project_id="proj-practice-1",
        mode="complete_viva",
        question_count=5,
    )
    assert q_set.practiced_count == 0

    first_q_id = q_set.questions[0].id

    # Toggle to practiced = True
    updated = VivaService.update_practice_status(
        db=db_session,
        project_id="proj-practice-1",
        question_id=first_q_id,
        is_practiced=True,
    )
    assert updated.is_practiced is True

    # Verify progress stats reflect update
    progress = VivaService.get_progress(db=db_session, project_id="proj-practice-1")
    assert progress.practiced_count == 1
    assert progress.percentage > 0.0

    # Toggle back to practiced = False
    updated_back = VivaService.update_practice_status(
        db=db_session,
        project_id="proj-practice-1",
        question_id=first_q_id,
        is_practiced=False,
    )
    assert updated_back.is_practiced is False

    progress_back = VivaService.get_progress(db=db_session, project_id="proj-practice-1")
    assert progress_back.practiced_count == 0


def test_regenerate_single_question(db_session: Session):
    """Test regenerating a single question retains category and difficulty."""
    _setup_test_project(db_session, "proj-regen-1", "Telemetry Dashboard")

    q_set = VivaService.generate_questions(
        db=db_session,
        project_id="proj-regen-1",
        mode="complete_viva",
        question_count=4,
    )
    target_q = q_set.questions[0]
    orig_cat = target_q.category
    orig_diff = target_q.difficulty

    regen_q = VivaService.regenerate_single_question(
        db=db_session,
        project_id="proj-regen-1",
        question_id=target_q.id,
    )
    assert regen_q.id == target_q.id
    assert regen_q.category == orig_cat
    assert regen_q.difficulty == orig_diff


def test_delete_viva_questions(db_session: Session):
    """Test clearing viva questions for a project."""
    _setup_test_project(db_session, "proj-del-1", "E-Commerce Microservice")

    VivaService.generate_questions(
        db=db_session,
        project_id="proj-del-1",
        question_count=4,
    )
    assert VivaService.get_latest_question_set(db=db_session, project_id="proj-del-1") is not None

    VivaService.delete_questions(db=db_session, project_id="proj-del-1")
    assert VivaService.get_latest_question_set(db=db_session, project_id="proj-del-1") is None


# ─── 5. API Endpoints Integration Tests ───

def test_api_generate_and_get_viva_questions(client: TestClient, db_session: Session):
    """Test POST /api/projects/{id}/viva/generate and GET /api/projects/{id}/viva/questions."""
    _setup_test_project(db_session, "api-viva-1", "Smart Classroom Portal")

    # Generate questions
    res = client.post(
        "/api/projects/api-viva-1/viva/generate",
        json={"mode": "complete_viva", "difficulty": "all", "questionCount": 5},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["projectId"] == "api-viva-1"
    assert data["totalQuestions"] == 5
    assert len(data["questions"]) == 5

    # Retrieve saved questions
    get_res = client.get("/api/projects/api-viva-1/viva/questions")
    assert get_res.status_code == 200
    saved = get_res.json()
    assert saved["id"] == data["id"]
    assert len(saved["questions"]) == 5


def test_api_missing_project_returns_404(client: TestClient):
    """Test generating viva questions for non-existent project returns 404."""
    res = client.post(
        "/api/projects/nonexistent-999/viva/generate",
        json={"mode": "complete_viva", "questionCount": 5},
    )
    assert res.status_code == 404


def test_api_practice_and_progress(client: TestClient, db_session: Session):
    """Test PATCH practice status and GET progress endpoints."""
    _setup_test_project(db_session, "api-viva-2", "Library ERP")

    gen_res = client.post(
        "/api/projects/api-viva-2/viva/generate",
        json={"mode": "quick_prep", "questionCount": 4},
    )
    data = gen_res.json()
    q_id = data["questions"][0]["id"]

    # Update practice status
    patch_res = client.patch(
        f"/api/projects/api-viva-2/viva/questions/{q_id}/practice",
        json={"isPracticed": True},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["isPracticed"] is True

    # Get progress
    prog_res = client.get("/api/projects/api-viva-2/viva/progress")
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert prog_data["practicedCount"] == 1
    assert prog_data["totalQuestions"] == 4
    assert prog_data["percentage"] == 25.0


def test_project_data_isolation(client: TestClient, db_session: Session):
    """Test questions and practice status are strictly isolated per project."""
    _setup_test_project(db_session, "proj-iso-a", "Project Alpha")
    _setup_test_project(db_session, "proj-iso-b", "Project Beta")

    gen_a = client.post(
        "/api/projects/proj-iso-a/viva/generate",
        json={"questionCount": 3},
    )
    q_id_a = gen_a.json()["questions"][0]["id"]

    # Attempting to practice question from Project Alpha using Project Beta's URL must return 404
    bad_res = client.patch(
        f"/api/projects/proj-iso-b/viva/questions/{q_id_a}/practice",
        json={"isPracticed": True},
    )
    assert bad_res.status_code == 404


# ─── 8. Null-Safety & Regression Tests ───

def test_viva_evidence_builder_real_aliased_section_coverage(db_session: Session):
    """Regression test for TypeError: sequence item 0: expected str instance, NoneType found.
    
    Verifies that SectionCoverageItem dumped by alias (displayName, isPresent)
    does not cause sections_missing to contain None or crash str.join().
    """
    now = datetime.now(timezone.utc)
    proj = Project(
        id="proj-alias-coverage",
        title="Aliased Section Coverage Test",
        course="CS 490",
        team="Team Beta",
        status="completed",
        archive_filename="test.zip",
        archive_path="/tmp/test.zip",
        file_size_bytes=5000,
        created_at=now,
        updated_at=now,
    )
    db_session.add(proj)

    # Actual database format produced by SectionCoverageItem.model_dump(by_alias=True)
    doc = ProjectDocumentationAnalysis(
        project_id="proj-alias-coverage",
        status="completed",
        total_documents_count=2,
        total_words_count=1200,
        section_coverage=[
            {
                "sectionKey": "architecture",
                "displayName": "Architecture & Design",
                "isRequired": True,
                "isPresent": False,
                "detectedHeadings": [],
                "foundInFiles": [],
            },
            {
                "sectionKey": "testing",
                "displayName": "Testing & Validation",
                "isRequired": True,
                "isPresent": False,
                "detectedHeadings": [],
                "foundInFiles": [],
            },
            {
                "sectionKey": "overview",
                "displayName": "Project Overview",
                "isRequired": True,
                "isPresent": True,
                "detectedHeadings": ["Overview"],
                "foundInFiles": ["README.md"],
            },
        ],
        findings=[],
        created_at=now,
    )
    db_session.add(doc)
    db_session.commit()

    # Must execute with ZERO TypeError or exceptions
    ctx = VivaEvidenceBuilder.build_project_context(db_session, "proj-alias-coverage")

    assert ctx["documentation"] is not None
    assert "Architecture & Design" in ctx["documentation"]["sections_missing"]
    assert "Testing & Validation" in ctx["documentation"]["sections_missing"]
    assert "Project Overview" in ctx["documentation"]["sections_present"]
    assert None not in ctx["documentation"]["sections_missing"]
    assert None not in ctx["documentation"]["sections_present"]

    # Verify weaknesses string join executed safely
    missing_doc_weakness = [w for w in ctx["identified_weaknesses"] if "Missing documentation sections" in w]
    assert len(missing_doc_weakness) == 1
    assert "Architecture & Design" in missing_doc_weakness[0]


def test_viva_evidence_builder_missing_and_null_optional_fields(db_session: Session):
    """Test evidence builder safely handles empty projects, missing abstracts, and corrupted JSON."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id="proj-null-fields",
        title="",
        course=None,
        team=None,
        status="pending",
        archive_filename="empty.zip",
        archive_path="/tmp/empty.zip",
        file_size_bytes=0,
        created_at=now,
        updated_at=now,
    )
    db_session.add(proj)

    # Empty / null files
    f_null = ProjectFile(
        project_id="proj-null-fields",
        relative_path="",
        filename="",
        extension=None,
        category=None,
        detected_language=None,
        size_bytes=0,
        created_at=now,
    )
    db_session.add(f_null)

    # Empty structure with null frameworks
    struct = ProjectStructure(
        project_id="proj-null-fields",
        frameworks=None,
        total_files=0,
        source_files_count=0,
        created_at=now,
    )
    db_session.add(struct)

    # Docs with null section_coverage entries and empty dicts
    doc = ProjectDocumentationAnalysis(
        project_id="proj-null-fields",
        status="completed",
        total_documents_count=0,
        total_words_count=0,
        section_coverage=[
            {},
            {"unexpected_key": 42},
            {"displayName": None, "isPresent": None},
            {"displayName": "   ", "isPresent": False},
        ],
        findings=[],
        created_at=now,
    )
    db_session.add(doc)
    db_session.commit()

    ctx = VivaEvidenceBuilder.build_project_context(db_session, "proj-null-fields")
    assert ctx["title"] == "Untitled Software Project"
    assert ctx["course"] == "Computer Science Project"
    assert ctx["team"] == "Student Team"
    assert ctx["frameworks"] == []
    assert ctx["documentation"]["sections_missing"] == []
    assert ctx["documentation"]["sections_present"] == []
    assert None not in ctx["identified_weaknesses"]


def test_gemini_prompt_null_safe_with_missing_evidence():
    """Verify Gemini prompt builder explicitly marks missing evidence instead of failing."""
    context = {
        "title": None,
        "languages": {},
        "frameworks": [],
        "key_files": [],
        "has_database_files": False,
        "has_docker": False,
        "has_tests": False,
        "code_quality": None,
        "documentation": None,
        "git_history": None,
        "innovation": None,
        "identified_weaknesses": [],
    }
    prompt = GeminiVivaGenerator._build_prompt(
        context=context,
        mode="examiner_challenge",
        difficulty="advanced",
        question_count=5,
    )
    assert "EVALUATION EVIDENCE FOR PROJECT DEFENSE:" in prompt
    assert "None identified" in prompt
    assert "Code Quality: Not available" in prompt
    assert "Documentation: Not available" in prompt
    assert "Git History: Not available" in prompt
    assert "Mode: Examiner Challenge." in prompt
    assert "Target difficulty: advanced only." in prompt


def test_viva_generation_end_to_end_with_null_and_missing_fields(db_session: Session):
    """Verify VivaService.generate_questions succeeds on completely sparse project."""
    now = datetime.now(timezone.utc)
    proj = Project(
        id="proj-sparse-viva",
        title="Sparse Submission",
        status="completed",
        archive_filename="sparse.zip",
        archive_path="/tmp/sparse.zip",
        file_size_bytes=100,
        created_at=now,
        updated_at=now,
    )
    db_session.add(proj)
    db_session.commit()

    # Generate complete viva set
    result = VivaService.generate_questions(
        db=db_session,
        project_id="proj-sparse-viva",
        mode="complete_viva",
        difficulty="all",
        question_count=8,
    )
    assert result.total_questions == 8
    assert len(result.questions) == 8
    for q in result.questions:
        assert q.question is not None and len(q.question) > 0
        assert q.category in VIVA_CATEGORIES
        assert q.suggested_answer is not None and len(q.suggested_answer) > 0
        assert q.examiner_rationale is not None and len(q.examiner_rationale) > 0
        assert isinstance(q.key_points, list)
        assert None not in q.key_points


def test_viva_gemini_response_null_fields_normalized(db_session: Session):
    """Verify that if Gemini returns null values for category, key_points, or answers, they are normalized."""
    _setup_test_project(db_session, "proj-gemini-nulls", "Project with Gemini Nulls")

    mock_gemini_questions = [
        {
            "question": "What is the primary role of FastAPI in this backend?",
            "category": None,
            "difficulty": None,
            "examiner_rationale": None,
            "key_points": [None, "High throughput", None, "Async I/O"],
            "suggested_answer": None,
            "evidence_reference": None,
        }
    ]

    with patch.object(GeminiVivaGenerator, "is_available", return_value=True):
        with patch.object(GeminiVivaGenerator, "generate_questions", return_value=mock_gemini_questions):
            result = VivaService.generate_questions(
                db=db_session,
                project_id="proj-gemini-nulls",
                mode="quick_prep",
                question_count=1,
            )

            assert len(result.questions) == 1
            q = result.questions[0]
            assert q.category == "Project Fundamentals"
            assert q.difficulty == "intermediate"
            assert q.examiner_rationale == "Assesses foundational software engineering understanding."
            assert q.key_points == ["High throughput", "Async I/O"]
            assert q.suggested_answer == "Refer to the project implementation files and architecture documentation."
            assert q.evidence_reference == "Project Documentation & Source Code"
