from pathlib import Path
from typing import List, Dict, Any
from app.config.analysis_thresholds import SOURCE_EXTENSIONS

def calculate_language_distribution(scanned_files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculate language breakdown based on source file counts.
    Returns list of dicts: [{"language": "Python", "file_count": 18, "percentage": 72.0}]
    """
    source_files = [f for f in scanned_files if f["file_type"] in {"source", "test"}]
    total_source_count = len(source_files)
    
    if total_source_count == 0:
        return []
        
    counts: Dict[str, int] = {}
    for sf in source_files:
        lang = sf["language"]
        if lang != "Unknown":
            counts[lang] = counts.get(lang, 0) + 1

    distribution = []
    for lang, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        pct = round((count / total_source_count) * 100.0, 1)
        distribution.append({
            "language": lang,
            "file_count": count,
            "percentage": pct
        })
        
    return distribution

def detect_technologies_from_evidence(
    project_dir: Path, scanned_files: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Detect technologies (languages, frameworks, databases, tools) ONLY when concrete evidence exists.
    Categories: 'language', 'framework', 'database', 'tool'
    """
    technologies: List[Dict[str, Any]] = []
    
    # 1. Languages from scanned files
    lang_dist = calculate_language_distribution(scanned_files)
    for ld in lang_dist:
        technologies.append({
            "name": ld["language"],
            "category": "language",
            "evidence": f"Detected in {ld['file_count']} source file(s) ({ld['percentage']}%)"
        })
        
    # Read manifest contents safely for framework evidence
    manifest_contents: Dict[str, str] = {}
    for sf in scanned_files:
        fn_lower = sf["filename"].lower()
        if fn_lower in {"requirements.txt", "package.json", "pyproject.toml", "pom.xml", "build.gradle", "dockerfile"}:
            try:
                abs_path = sf["abs_path"]
                if abs_path.exists() and abs_path.stat().st_size < 1_000_000:
                    with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                        manifest_contents[fn_lower] = f.read().lower()
            except Exception:
                pass
                
    reqs_content = manifest_contents.get("requirements.txt", "") + manifest_contents.get("pyproject.toml", "")
    pkg_content = manifest_contents.get("package.json", "")
    
    # 2. Python Framework Detection
    if "flask" in reqs_content:
        technologies.append({"name": "Flask", "category": "framework", "evidence": "Flask dependency detected in Python requirements"})
    if "fastapi" in reqs_content:
        technologies.append({"name": "FastAPI", "category": "framework", "evidence": "FastAPI dependency detected in Python requirements"})
    if "django" in reqs_content:
        technologies.append({"name": "Django", "category": "framework", "evidence": "Django dependency detected in Python requirements"})
    if "pytest" in reqs_content:
        technologies.append({"name": "Pytest", "category": "tool", "evidence": "Pytest test framework detected in requirements"})

    # 3. JavaScript / TypeScript Framework Detection
    if "react" in pkg_content:
        technologies.append({"name": "React", "category": "framework", "evidence": "React dependency detected in package.json"})
    if "next" in pkg_content:
        technologies.append({"name": "Next.js", "category": "framework", "evidence": "Next.js framework detected in package.json"})
    if "express" in pkg_content:
        technologies.append({"name": "Express", "category": "framework", "evidence": "Express.js framework detected in package.json"})
    if "vue" in pkg_content:
        technologies.append({"name": "Vue.js", "category": "framework", "evidence": "Vue.js framework detected in package.json"})
    if "vite" in pkg_content:
        technologies.append({"name": "Vite", "category": "tool", "evidence": "Vite build tool detected in package.json"})
    if "tailwindcss" in pkg_content or "tailwind" in pkg_content:
        technologies.append({"name": "Tailwind CSS", "category": "framework", "evidence": "Tailwind CSS detected in dependencies"})

    # 4. Database Evidence Detection
    if "psycopg2" in reqs_content or "asyncpg" in reqs_content or "pg" in pkg_content or "postgresql" in reqs_content:
        technologies.append({"name": "PostgreSQL", "category": "database", "evidence": "PostgreSQL database driver detected in dependencies"})
    elif "pymysql" in reqs_content or "mysql" in reqs_content or "mysql2" in pkg_content:
        technologies.append({"name": "MySQL", "category": "database", "evidence": "MySQL database driver detected in dependencies"})
    elif "sqlite" in reqs_content or "sqlite3" in reqs_content:
        technologies.append({"name": "SQLite", "category": "database", "evidence": "SQLite database detected in configurations"})

    # 5. Infrastructure / Tools Evidence
    has_docker = any(sf["filename"].lower() == "dockerfile" or sf["filename"].lower() == "docker-compose.yml" for sf in scanned_files)
    if has_docker:
        technologies.append({"name": "Docker", "category": "tool", "evidence": "Dockerfile / docker-compose config detected"})

    return technologies
