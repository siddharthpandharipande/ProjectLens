from pathlib import Path
from app.services.technology_detector import (
    detect_technologies,
    build_technology_stack,
    parse_imports_from_source_files
)

def test_detect_technologies_categorization(tmp_path: Path):
    proj_dir = tmp_path / "test_project"
    proj_dir.mkdir()

    # Create dummy requirements.txt
    reqs = proj_dir / "requirements.txt"
    reqs.write_text("fastapi==0.110.0\ntorch==2.2.0\nsqlalchemy==2.0.25\npytest==8.0.0\n")

    # Create dummy package.json
    pkg = proj_dir / "package.json"
    pkg.write_text('{"dependencies": {"react": "^18.2.0", "next": "^14.1.0", "tailwindcss": "^3.4.1"}}')

    # Create dummy Dockerfile
    dockerfile = proj_dir / "Dockerfile"
    dockerfile.write_text("FROM python:3.11-slim\nCMD ['python', 'app.py']")

    # Create dummy python source file
    py_src = proj_dir / "main.py"
    py_src.write_text("import fastapi\nimport torch\nfrom sqlalchemy import create_engine\n")

    scanned_files = [
        {"filename": "requirements.txt", "rel_path": "requirements.txt", "language": "Unknown", "file_type": "config", "abs_path": reqs},
        {"filename": "package.json", "rel_path": "package.json", "language": "Unknown", "file_type": "config", "abs_path": pkg},
        {"filename": "Dockerfile", "rel_path": "Dockerfile", "language": "Unknown", "file_type": "config", "abs_path": dockerfile},
        {"filename": "main.py", "rel_path": "main.py", "language": "Python", "file_type": "source", "abs_path": py_src},
    ]

    result = detect_technologies(scanned_files)
    tech_map = {t["name"]: t for t in result}

    # Verify Categories
    assert "Python" in tech_map
    assert tech_map["Python"]["category"] == "LANGUAGE"

    assert "FastAPI" in tech_map
    assert tech_map["FastAPI"]["category"] == "BACKEND"
    assert tech_map["FastAPI"]["confidence"] == "HIGH"

    assert "PyTorch" in tech_map
    assert tech_map["PyTorch"]["category"] == "AI / ML"
    assert tech_map["PyTorch"]["confidence"] == "HIGH"

    assert "SQLAlchemy" in tech_map
    assert tech_map["SQLAlchemy"]["category"] == "DATABASE"

    assert "React" in tech_map
    assert tech_map["React"]["category"] == "FRONTEND"

    assert "Docker" in tech_map
    assert tech_map["Docker"]["category"] == "INFRASTRUCTURE"
    assert tech_map["Docker"]["confidence"] == "HIGH"

    assert "Pytest" in tech_map
    assert tech_map["Pytest"]["category"] == "TESTING"

def test_build_technology_stack_structure(tmp_path: Path):
    proj_dir = tmp_path / "proj"
    proj_dir.mkdir()

    reqs = proj_dir / "requirements.txt"
    reqs.write_text("flask==3.0.0\nredis==5.0.1\n")

    scanned_files = [
        {"filename": "requirements.txt", "rel_path": "requirements.txt", "language": "Unknown", "file_type": "config", "abs_path": reqs},
        {"filename": "app.py", "rel_path": "app.py", "language": "Python", "file_type": "source", "abs_path": proj_dir / "app.py"},
    ]

    stack = build_technology_stack(scanned_files)

    assert "technologies" in stack
    assert "total_count" in stack
    assert "category_count" in stack
    assert stack["total_count"] == len(stack["technologies"])
    assert stack["category_count"] > 0
