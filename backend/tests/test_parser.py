import io
import zipfile
import pytest
from pathlib import Path
from app.services.project_parser import (
    extract_project,
    scan_project_files,
    classify_file,
    ZipTraversalError,
    cleanup_project,
)

def test_classify_file():
    assert classify_file(Path("src/main.py"), "main.py", ".py") == "source"
    assert classify_file(Path("tests/test_main.py"), "test_main.py", ".py") == "test"
    assert classify_file(Path("README.md"), "README.md", ".md") == "documentation"
    assert classify_file(Path("package.json"), "package.json", ".json") == "config"

def test_zip_path_traversal_prevention(tmp_path: Path):
    # Create a malicious zip file with path traversal entry "../malicious.txt"
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("../malicious.txt", "evil payload")
        zf.writestr("valid.py", "print('hello')")
        
    zip_bytes.seek(0)
    zip_path = tmp_path / "test_malicious.zip"
    zip_path.write_bytes(zip_bytes.read())
    
    extract_dir = tmp_path / "extracted"
    
    with pytest.raises(ZipTraversalError):
        extract_project(zip_path, extract_dir)
        
    cleanup_project(extract_dir)

def test_scan_project_files_ignores_dependency_dirs(tmp_path: Path):
    # Create mock project structure
    project_dir = tmp_path / "sample_project"
    project_dir.mkdir()
    
    (project_dir / "src").mkdir()
    (project_dir / "src" / "app.py").write_text("print('app')")
    
    (project_dir / "node_modules").mkdir()
    (project_dir / "node_modules" / "express.js").write_text("module.exports = {}")
    
    (project_dir / ".venv").mkdir()
    (project_dir / ".venv" / "pip.py").write_text("# venv")
    
    files = scan_project_files(project_dir)
    
    rel_paths = [f["rel_path"] for f in files]
    assert "src/app.py" in rel_paths
    assert "node_modules/express.js" not in rel_paths
    assert ".venv/pip.py" not in rel_paths
