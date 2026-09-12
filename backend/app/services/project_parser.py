import os
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Any
from app.config.analysis_thresholds import (
    IGNORED_DIRECTORIES,
    SOURCE_EXTENSIONS,
    DOC_EXTENSIONS,
    CONFIG_EXTENSIONS,
)

class ZipTraversalError(ValueError):
    """Exception raised when a zip file contains path traversal attack entries."""
    pass

def is_safe_zip_path(target_dir: Path, path: Path) -> bool:
    """Validate that the target path remains inside target_dir to prevent Zip Slip attacks."""
    resolved_target = target_dir.resolve()
    resolved_path = path.resolve()
    return os.path.commonpath([resolved_target, resolved_path]) == str(resolved_target)

def extract_project(zip_path: Path, extract_dir: Path) -> Path:
    """
    Safely extract a ZIP archive into an isolated target directory with Zip Slip protection.
    Returns the root extraction directory.
    """
    os.makedirs(extract_dir, exist_ok=True)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for member in zip_ref.infolist():
            # Construct target path
            member_path = extract_dir / member.filename
            if not is_safe_zip_path(extract_dir, member_path):
                raise ZipTraversalError(f"Attempted path traversal entry in ZIP: {member.filename}")
            
            zip_ref.extract(member, extract_dir)
            
    return extract_dir

def classify_file(relative_path: Path, filename: str, extension: str) -> str:
    """
    Classify file type: 'source', 'test', 'documentation', 'config', 'asset', 'other'
    """
    rel_str = str(relative_path).lower()
    ext_lower = extension.lower()
    fn_lower = filename.lower()
    
    # Check if test file first
    is_test = (
        "test" in rel_str
        or "spec" in rel_str
        or fn_lower.startswith("test_")
        or fn_lower.endswith("_test.py")
        or fn_lower.endswith(".test.js")
        or fn_lower.endswith(".test.ts")
        or fn_lower.endswith(".spec.js")
        or fn_lower.endswith(".spec.ts")
    )
    if is_test and ext_lower in SOURCE_EXTENSIONS:
        return "test"
        
    if ext_lower in DOC_EXTENSIONS or fn_lower in {"readme", "readme.md", "readme.txt", "license", "changelog"}:
        return "documentation"
        
    if ext_lower in CONFIG_EXTENSIONS or fn_lower in {"package.json", "requirements.txt", "pyproject.toml", "pom.xml", "build.gradle", "dockerfile", "makefile"}:
        return "config"
        
    if ext_lower in SOURCE_EXTENSIONS:
        return "source"
        
    if ext_lower in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".mp4", ".mp3", ".woff", ".ttf"}:
        return "asset"
        
    return "other"

def scan_project_files(project_dir: Path) -> List[Dict[str, Any]]:
    """
    Recursively scan project directory, ignoring dependency and generated folders.
    Returns list of scanned file metadata dictionaries.
    """
    scanned_files = []
    
    for root, dirs, files in os.walk(project_dir):
        # Filter out ignored directories in-place
        dirs[:] = [
            d for d in dirs
            if d not in IGNORED_DIRECTORIES
            and not d.startswith(".")
            and d.lower() not in {"node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
        ]
        
        for file in files:
            if file.startswith(".DS_Store"):
                continue
                
            abs_path = Path(root) / file
            rel_path = abs_path.relative_to(project_dir)
            
            # Check if any parent folder in relative path is in ignored list
            if any(part in IGNORED_DIRECTORIES for part in rel_path.parts):
                continue
                
            extension = abs_path.suffix
            file_size = abs_path.stat().st_size if abs_path.exists() else 0
            file_type = classify_file(rel_path, file, extension)
            language = SOURCE_EXTENSIONS.get(extension.lower(), "Unknown")
            
            scanned_files.append({
                "abs_path": abs_path,
                "rel_path": str(rel_path).replace("\\", "/"),
                "filename": file,
                "extension": extension.lower(),
                "language": language,
                "file_type": file_type,
                "size_bytes": file_size,
            })
            
    return scanned_files

def cleanup_project(target_dir: Path):
    """Safely remove isolated temporary extraction directory."""
    if target_dir.exists() and target_dir.is_dir():
        shutil.rmtree(target_dir, ignore_errors=True)
