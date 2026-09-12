from pathlib import Path
from app.services.language_detector import (
    calculate_language_distribution,
    detect_technologies_from_evidence,
)

def test_language_distribution():
    scanned_files = [
        {"filename": "app.py", "language": "Python", "file_type": "source"},
        {"filename": "utils.py", "language": "Python", "file_type": "source"},
        {"filename": "index.js", "language": "JavaScript", "file_type": "source"},
        {"filename": "README.md", "language": "Unknown", "file_type": "documentation"},
    ]
    
    dist = calculate_language_distribution(scanned_files)
    
    assert len(dist) == 2
    assert dist[0]["language"] == "Python"
    assert dist[0]["file_count"] == 2
    assert dist[0]["percentage"] == 66.7
    assert dist[1]["language"] == "JavaScript"
    assert dist[1]["file_count"] == 1
    assert dist[1]["percentage"] == 33.3

def test_detect_technologies_evidence(tmp_path: Path):
    project_dir = tmp_path / "proj"
    project_dir.mkdir()
    
    reqs_file = project_dir / "requirements.txt"
    reqs_file.write_text("flask==3.0.2\npytest==8.0.0\npsycopg2-binary==2.9.9\n")
    
    scanned_files = [
        {"filename": "requirements.txt", "language": "Unknown", "file_type": "config", "abs_path": reqs_file},
        {"filename": "app.py", "language": "Python", "file_type": "source", "abs_path": project_dir / "app.py"},
    ]
    
    techs = detect_technologies_from_evidence(project_dir, scanned_files)
    names = [t["name"] for t in techs]
    
    assert "Flask" in names
    assert "Pytest" in names
    assert "PostgreSQL" in names
