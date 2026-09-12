from pathlib import Path
from app.services.documentation_analyzer import analyze_documentation_integrity
from app.services.git_analyzer import analyze_development_process
from app.services.technical_execution_analyzer import analyze_technical_execution
from app.services.strength_detector import detect_strengths
from app.services.improvement_detector import detect_improvements
from app.services.score_engine import calculate_evaluation_scores
from app.models.code_metric import CodeMetric

def test_documentation_analyzer_with_readme(tmp_path: Path):
    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()

    readme = proj_dir / "README.md"
    readme.write_text(
        "# Project Overview\nAn academic evaluation platform.\n\n"
        "## Installation\n```bash\nnpm install\n```\n\n"
        "## Usage\n```bash\nnpm run dev\n```\n\n"
        "## Architecture\nFastAPI backend with React frontend.\n"
    )

    scanned_files = [
        {"filename": "README.md", "file_type": "documentation", "abs_path": readme}
    ]

    res = analyze_documentation_integrity(scanned_files)

    assert res["status"] == "completed"
    assert res["score"] > 60.0
    assert len(res["evidence"]) > 0

def test_git_analyzer_missing_git(tmp_path: Path):
    proj_dir = tmp_path / "proj_no_git"
    proj_dir.mkdir()

    res = analyze_development_process(proj_dir)

    assert res["status"] == "N/A"
    assert res["score"] is None
    assert "Git history was not included" in res["evidence"][0]

def test_technical_execution_analyzer():
    cm = CodeMetric(
        source_file_count=12,
        average_complexity=3.2,
        code_lines=1500,
        comment_lines=200,
        test_file_count=4
    )

    file_types = ["source", "config", "documentation"]
    res = analyze_technical_execution(cm, file_types)

    assert res["status"] == "completed"
    assert res["score"] > 70.0

def test_overall_score_calculation(tmp_path: Path):
    cm = CodeMetric(
        source_file_count=8,
        average_complexity=4.0,
        code_lines=800,
        comment_lines=100,
        test_file_count=2
    )

    scanned_files = [
        {"filename": "README.md", "file_type": "documentation", "abs_path": tmp_path / "README.md"}
    ]

    res = calculate_evaluation_scores(cm, scanned_files, tmp_path)

    assert res["overall_score"] is not None
    assert "Based on" in res["overall_status"]
    assert res["originality"] is None
