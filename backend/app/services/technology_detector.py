import os
import re
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from app.services.language_detector import calculate_language_distribution

def parse_imports_from_source_files(scanned_files: List[Dict[str, Any]]) -> Tuple[Set[str], Dict[str, int]]:
    """
    Extract imported modules across all source files.
    Returns:
      - Set of all lowercased imported module names
      - Dict mapping module name -> file count where imported
    """
    imported_modules: Dict[str, int] = {}

    # Regex patterns for imports in Python, JS/TS, Java, Go, C#
    python_import_re = re.compile(r'^\s*(?:import|from)\s+([a-zA-Z0-9_\.]+)', re.MULTILINE)
    jsts_import_re = re.compile(r'(?:import\s+.*?from\s+[\'"]([^\'"]+)[\'"]|require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\))')
    
    for sf in scanned_files:
        if sf.get("file_type") not in {"source", "test"}:
            continue

        abs_path = sf.get("abs_path")
        if not abs_path or not isinstance(abs_path, Path) or not abs_path.exists():
            continue

        # Skip large files (> 2MB)
        if abs_path.stat().st_size > 2_000_000:
            continue

        try:
            with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            file_modules: Set[str] = set()
            lang = sf.get("language", "")

            if lang == "Python":
                matches = python_import_re.findall(content)
                for m in matches:
                    top_mod = m.split(".")[0].lower()
                    if top_mod:
                        file_modules.add(top_mod)

            elif lang in {"JavaScript", "TypeScript", "JavaScript React", "TypeScript React"}:
                matches = jsts_import_re.findall(content)
                for m_from, m_req in matches:
                    raw_pkg = m_from or m_req
                    if raw_pkg and not raw_pkg.startswith("."):
                        # Extract top-level package or scoped package (@org/pkg)
                        parts = raw_pkg.split("/")
                        if raw_pkg.startswith("@") and len(parts) >= 2:
                            pkg = f"{parts[0]}/{parts[1]}".lower()
                        else:
                            pkg = parts[0].lower()
                        file_modules.add(pkg)

            for mod in file_modules:
                imported_modules[mod] = imported_modules.get(mod, 0) + 1

        except Exception:
            pass

    return set(imported_modules.keys()), imported_modules

def read_manifest_files(scanned_files: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Read contents of manifest & configuration files into a dictionary.
    Keys are lowercased filenames or relative paths.
    """
    manifests: Dict[str, str] = {}

    target_files = {
        "package.json", "requirements.txt", "pyproject.toml", "pipfile",
        "pom.xml", "build.gradle", "go.mod", "cargo.toml", "dockerfile",
        "docker-compose.yml", "docker-compose.yaml", "vite.config.js",
        "vite.config.ts", "next.config.js", "next.config.ts", "tsconfig.json",
        "tailwind.config.js", "tailwind.config.ts", "vercel.json", "netlify.toml",
        "yarn.lock", "package-lock.json", "pnpm-lock.yaml", "uv.lock", "poetry.lock"
    }

    for sf in scanned_files:
        fn_lower = sf.get("filename", "").lower()
        rel_lower = sf.get("rel_path", "").lower()

        if fn_lower in target_files or any(rel_lower.endswith(tf) for tf in target_files):
            abs_path = sf.get("abs_path")
            if abs_path and isinstance(abs_path, Path) and abs_path.exists():
                try:
                    if abs_path.stat().st_size < 1_000_000:
                        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
                            manifests[fn_lower] = f.read().lower()
                except Exception:
                    pass

    return manifests

def detect_technologies(
    scanned_files: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Modular, deterministic technology detector.
    Categorizes technologies and assigns confidence levels (HIGH, MEDIUM, LOW)
    with explicit evidence list based on manifests, files, and source code imports.
    """
    technologies: List[Dict[str, Any]] = []
    seen_names: Set[str] = set()

    # 1. Parse imports and read manifests
    all_imports, import_counts = parse_imports_from_source_files(scanned_files)
    manifests = read_manifest_files(scanned_files)

    combined_manifest_str = " ".join(manifests.values())

    def add_tech(name: str, category: str, confidence: str, evidence: List[str], file_count: int = 0):
        name_key = name.lower()
        if name_key in seen_names:
            return
        seen_names.add(name_key)
        technologies.append({
            "name": name,
            "category": category,
            "confidence": confidence,
            "file_count": file_count,
            "evidence": evidence
        })

    # --- CATEGORY 1: LANGUAGES ---
    lang_dist = calculate_language_distribution(scanned_files)
    for ld in lang_dist:
        lang_name = ld["language"]
        count = ld["file_count"]
        pct = ld["percentage"]
        evidence_str = f"Detected in {count} source file(s) ({pct}% of project source code)"
        add_tech(lang_name, "LANGUAGE", "HIGH", [evidence_str], file_count=count)

    # --- CATEGORY 2: FRONTEND ---
    if "react" in combined_manifest_str or "react" in all_imports or "react-dom" in combined_manifest_str:
        file_cnt = import_counts.get("react", 0) or import_counts.get("react-dom", 0)
        conf = "HIGH" if file_cnt > 0 or "package.json" in manifests else "MEDIUM"
        ev = []
        if "package.json" in manifests and "react" in manifests["package.json"]:
            ev.append("Declared in package.json dependencies")
        if file_cnt > 0:
            ev.append(f"Imported in {file_cnt} JS/TS source file(s)")
        add_tech("React", "FRONTEND", conf, ev or ["React framework detected"], file_count=file_cnt)

    if "next" in combined_manifest_str or "next.config.js" in manifests or "next.config.ts" in manifests:
        file_cnt = import_counts.get("next", 0)
        conf = "HIGH" if "next.config.js" in manifests or "next.config.ts" in manifests or file_cnt > 0 else "MEDIUM"
        ev = []
        if "next.config.js" in manifests or "next.config.ts" in manifests:
            ev.append("Next.js configuration file present")
        if "package.json" in manifests and "next" in manifests["package.json"]:
            ev.append("Declared in package.json dependencies")
        add_tech("Next.js", "FRONTEND", conf, ev or ["Next.js framework detected"], file_count=file_cnt)

    if "vue" in combined_manifest_str or "vue" in all_imports:
        file_cnt = import_counts.get("vue", 0)
        conf = "HIGH" if file_cnt > 0 else "MEDIUM"
        add_tech("Vue.js", "FRONTEND", conf, ["Vue.js framework detected in dependencies/imports"], file_count=file_cnt)

    if "@angular/core" in combined_manifest_str or "angular" in combined_manifest_str:
        add_tech("Angular", "FRONTEND", "MEDIUM", ["Angular framework detected in dependencies"])

    if "svelte" in combined_manifest_str:
        add_tech("Svelte", "FRONTEND", "MEDIUM", ["Svelte framework detected in dependencies"])

    if "tailwindcss" in combined_manifest_str or "tailwind.config.js" in manifests or "tailwind.config.ts" in manifests:
        conf = "HIGH" if "tailwind.config.js" in manifests or "tailwind.config.ts" in manifests else "MEDIUM"
        add_tech("Tailwind CSS", "FRONTEND", conf, ["Tailwind CSS styling framework detected in project config/dependencies"])

    if "bootstrap" in combined_manifest_str:
        add_tech("Bootstrap", "FRONTEND", "MEDIUM", ["Bootstrap CSS library detected in dependencies"])

    if "@mui/material" in combined_manifest_str or "@material-ui/core" in combined_manifest_str:
        add_tech("Material UI", "FRONTEND", "MEDIUM", ["Material UI component library detected in package.json"])

    if "redux" in combined_manifest_str or "@reduxjs/toolkit" in combined_manifest_str:
        add_tech("Redux", "FRONTEND", "MEDIUM", ["Redux state management detected in project dependencies"])

    if "zustand" in combined_manifest_str or "zustand" in all_imports:
        add_tech("Zustand", "FRONTEND", "HIGH" if "zustand" in all_imports else "MEDIUM", ["Zustand state management detected"])

    # --- CATEGORY 3: BACKEND ---
    if "fastapi" in combined_manifest_str or "fastapi" in all_imports:
        file_cnt = import_counts.get("fastapi", 0)
        conf = "HIGH" if file_cnt > 0 or "requirements.txt" in manifests or "pyproject.toml" in manifests else "MEDIUM"
        ev = []
        if "requirements.txt" in manifests and "fastapi" in manifests["requirements.txt"]:
            ev.append("Declared in Python requirements.txt")
        if file_cnt > 0:
            ev.append(f"Imported in {file_cnt} Python source file(s)")
        add_tech("FastAPI", "BACKEND", conf, ev or ["FastAPI framework detected"], file_count=file_cnt)

    if "flask" in combined_manifest_str or "flask" in all_imports:
        file_cnt = import_counts.get("flask", 0)
        conf = "HIGH" if file_cnt > 0 else "MEDIUM"
        add_tech("Flask", "BACKEND", conf, [f"Flask framework detected (Imported in {file_cnt} files)"], file_count=file_cnt)

    if "django" in combined_manifest_str or "django" in all_imports:
        file_cnt = import_counts.get("django", 0)
        conf = "HIGH" if file_cnt > 0 else "MEDIUM"
        add_tech("Django", "BACKEND", conf, [f"Django web framework detected (Imported in {file_cnt} files)"], file_count=file_cnt)

    if "express" in combined_manifest_str or "express" in all_imports:
        file_cnt = import_counts.get("express", 0)
        conf = "HIGH" if file_cnt > 0 else "MEDIUM"
        add_tech("Express.js", "BACKEND", conf, ["Express.js backend framework detected in dependencies"], file_count=file_cnt)

    if "@nestjs/core" in combined_manifest_str:
        add_tech("NestJS", "BACKEND", "MEDIUM", ["NestJS framework detected in package.json"])

    if "spring-boot" in combined_manifest_str or "springframework" in combined_manifest_str:
        add_tech("Spring Boot", "BACKEND", "HIGH", ["Spring Boot Java framework detected in pom.xml/build.gradle"])

    if "uvicorn" in combined_manifest_str or "uvicorn" in all_imports:
        add_tech("Uvicorn", "BACKEND", "HIGH" if "uvicorn" in all_imports else "MEDIUM", ["Uvicorn ASGI server detected in requirements/imports"])

    # --- CATEGORY 4: AI / ML ---
    if "torch" in combined_manifest_str or "torch" in all_imports or "pytorch" in combined_manifest_str:
        file_cnt = import_counts.get("torch", 0)
        conf = "HIGH" if file_cnt > 0 or "torch" in combined_manifest_str else "MEDIUM"
        ev = []
        if "requirements.txt" in manifests and "torch" in manifests["requirements.txt"]:
            ev.append("Declared in requirements.txt")
        if file_cnt > 0:
            ev.append(f"Imported in {file_cnt} Python file(s)")
        add_tech("PyTorch", "AI / ML", conf, ev or ["PyTorch deep learning framework detected"], file_count=file_cnt)

    if "tensorflow" in combined_manifest_str or "tensorflow" in all_imports or "tf" in all_imports:
        file_cnt = import_counts.get("tensorflow", 0)
        add_tech("TensorFlow", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["TensorFlow machine learning library detected"], file_count=file_cnt)

    if "sklearn" in all_imports or "scikit-learn" in combined_manifest_str:
        file_cnt = import_counts.get("sklearn", 0)
        add_tech("Scikit-learn", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["Scikit-learn machine learning library detected"], file_count=file_cnt)

    if "cv2" in all_imports or "opencv-python" in combined_manifest_str:
        file_cnt = import_counts.get("cv2", 0)
        add_tech("OpenCV", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["OpenCV computer vision library detected"], file_count=file_cnt)

    if "pandas" in combined_manifest_str or "pandas" in all_imports:
        file_cnt = import_counts.get("pandas", 0)
        add_tech("Pandas", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["Pandas data manipulation library detected"], file_count=file_cnt)

    if "numpy" in combined_manifest_str or "numpy" in all_imports:
        file_cnt = import_counts.get("numpy", 0)
        add_tech("NumPy", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["NumPy numerical computing library detected"], file_count=file_cnt)

    if "transformers" in combined_manifest_str or "transformers" in all_imports:
        file_cnt = import_counts.get("transformers", 0)
        add_tech("Hugging Face Transformers", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["Hugging Face Transformers library detected"], file_count=file_cnt)

    if "langchain" in combined_manifest_str or "langchain" in all_imports:
        file_cnt = import_counts.get("langchain", 0)
        add_tech("LangChain", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["LangChain LLM framework detected"], file_count=file_cnt)

    if "llama-index" in combined_manifest_str or "llamaindex" in all_imports:
        file_cnt = import_counts.get("LlamaIndex", "AI / ML", "MEDIUM", ["LlamaIndex data framework detected"])

    if "mediapipe" in combined_manifest_str or "mediapipe" in all_imports:
        file_cnt = import_counts.get("mediapipe", 0)
        add_tech("MediaPipe", "AI / ML", "HIGH" if file_cnt > 0 else "MEDIUM", ["MediaPipe ML framework detected"], file_count=file_cnt)

    # --- CATEGORY 5: DATABASE ---
    if any(k in combined_manifest_str for k in ["psycopg2", "asyncpg", "postgresql", "pg"]) or "psycopg2" in all_imports or "asyncpg" in all_imports:
        file_cnt = import_counts.get("psycopg2", 0) or import_counts.get("asyncpg", 0)
        add_tech("PostgreSQL", "DATABASE", "HIGH" if file_cnt > 0 else "MEDIUM", ["PostgreSQL database driver detected in project dependencies/imports"], file_count=file_cnt)

    if any(k in combined_manifest_str for k in ["pymysql", "mysql", "mysql2"]):
        add_tech("MySQL", "DATABASE", "MEDIUM", ["MySQL database driver detected in dependencies"])

    if "sqlite" in combined_manifest_str or "sqlite3" in combined_manifest_str or "sqlite3" in all_imports:
        add_tech("SQLite", "DATABASE", "HIGH" if "sqlite3" in all_imports else "MEDIUM", ["SQLite relational database engine detected"])

    if "pymongo" in combined_manifest_str or "mongodb" in combined_manifest_str or "mongoose" in combined_manifest_str:
        add_tech("MongoDB", "DATABASE", "MEDIUM", ["MongoDB document database driver detected"])

    if "redis" in combined_manifest_str or "redis" in all_imports or "ioredis" in combined_manifest_str:
        file_cnt = import_counts.get("redis", 0)
        add_tech("Redis", "DATABASE", "HIGH" if file_cnt > 0 else "MEDIUM", ["Redis in-memory database / cache detected"], file_count=file_cnt)

    if "sqlalchemy" in combined_manifest_str or "sqlalchemy" in all_imports:
        file_cnt = import_counts.get("sqlalchemy", 0)
        conf = "HIGH" if file_cnt > 0 else "MEDIUM"
        add_tech("SQLAlchemy", "DATABASE", conf, [f"SQLAlchemy ORM detected (Imported in {file_cnt} file(s))"], file_count=file_cnt)

    if "prisma" in combined_manifest_str or "@prisma/client" in combined_manifest_str:
        add_tech("Prisma", "DATABASE", "MEDIUM", ["Prisma ORM detected in dependencies"])

    if "firebase" in combined_manifest_str or "firebase-admin" in combined_manifest_str:
        add_tech("Firebase", "DATABASE", "MEDIUM", ["Firebase / Firestore SDK detected in project dependencies"])

    # --- CATEGORY 6: STORAGE ---
    if "boto3" in combined_manifest_str or "boto3" in all_imports or "@aws-sdk/client-s3" in combined_manifest_str:
        file_cnt = import_counts.get("boto3", 0)
        add_tech("AWS S3 Storage", "STORAGE", "HIGH" if file_cnt > 0 else "MEDIUM", ["AWS S3 SDK detected in project dependencies/imports"], file_count=file_cnt)

    if "google-cloud-storage" in combined_manifest_str:
        add_tech("Google Cloud Storage", "STORAGE", "MEDIUM", ["GCS SDK detected in dependencies"])

    if "minio" in combined_manifest_str or "minio" in all_imports:
        add_tech("MinIO", "STORAGE", "MEDIUM", ["MinIO object storage client detected"])

    # --- CATEGORY 7: INFRASTRUCTURE ---
    has_dockerfile = "dockerfile" in manifests or any(sf.get("filename", "").lower() == "dockerfile" for sf in scanned_files)
    has_docker_compose = "docker-compose.yml" in manifests or "docker-compose.yaml" in manifests or any(sf.get("filename", "").lower() in {"docker-compose.yml", "docker-compose.yaml"} for sf in scanned_files)
    if has_dockerfile or has_docker_compose:
        ev = []
        if has_dockerfile:
            ev.append("Dockerfile present in project root")
        if has_docker_compose:
            ev.append("docker-compose config present")
        add_tech("Docker", "INFRASTRUCTURE", "HIGH", ev)

    if any(sf.get("rel_path", "").startswith(".github/workflows") for sf in scanned_files):
        add_tech("GitHub Actions", "INFRASTRUCTURE", "HIGH", ["GitHub Actions CI/CD workflows configuration present"])

    if "nginx.conf" in manifests or any(sf.get("filename", "").lower() == "nginx.conf" for sf in scanned_files):
        add_tech("Nginx", "INFRASTRUCTURE", "HIGH", ["Nginx web server configuration present"])

    if "vercel.json" in manifests:
        add_tech("Vercel", "INFRASTRUCTURE", "HIGH", ["Vercel deployment configuration present"])

    # --- CATEGORY 8: TESTING ---
    if "pytest" in combined_manifest_str or "pytest" in all_imports:
        file_cnt = import_counts.get("pytest", 0)
        add_tech("Pytest", "TESTING", "HIGH", ["Pytest testing framework detected in project dependencies/tests"], file_count=file_cnt)

    if "jest" in combined_manifest_str:
        add_tech("Jest", "TESTING", "MEDIUM", ["Jest testing framework detected in package.json"])

    if "vitest" in combined_manifest_str:
        add_tech("Vitest", "TESTING", "MEDIUM", ["Vitest testing framework detected in package.json"])

    if "cypress" in combined_manifest_str:
        add_tech("Cypress", "TESTING", "MEDIUM", ["Cypress end-to-end testing framework detected"])

    if "playwright" in combined_manifest_str:
        add_tech("Playwright", "TESTING", "MEDIUM", ["Playwright testing framework detected"])

    # --- CATEGORY 9: BUILD / PACKAGE MANAGEMENT ---
    if "package.json" in manifests or "package-lock.json" in manifests:
        add_tech("npm", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["npm package manifest present (package.json)"])

    if "yarn.lock" in manifests:
        add_tech("Yarn", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["Yarn lockfile present"])

    if "pnpm-lock.yaml" in manifests:
        add_tech("pnpm", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["pnpm lockfile present"])

    if "vite.config.js" in manifests or "vite.config.ts" in manifests or "vite" in combined_manifest_str:
        ev = ["Vite build tool configuration present"] if ("vite.config.js" in manifests or "vite.config.ts" in manifests) else ["Vite detected in package dependencies"]
        add_tech("Vite", "BUILD / PACKAGE MANAGEMENT", "HIGH", ev)

    if "requirements.txt" in manifests:
        add_tech("pip", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["Python pip requirements.txt manifest present"])

    if "poetry.lock" in manifests or ("[tool.poetry]" in combined_manifest_str):
        add_tech("Poetry", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["Poetry dependency manager configuration present"])

    if "uv.lock" in manifests:
        add_tech("uv", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["uv package manager lockfile present"])

    if "pom.xml" in manifests:
        add_tech("Maven", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["Apache Maven build file (pom.xml) present"])

    if "build.gradle" in manifests:
        add_tech("Gradle", "BUILD / PACKAGE MANAGEMENT", "HIGH", ["Gradle build script present"])

    # Sort technologies by category, then by confidence (HIGH before MEDIUM/LOW), then by name
    confidence_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    category_order = {
        "LANGUAGE": 0,
        "FRONTEND": 1,
        "BACKEND": 2,
        "AI / ML": 3,
        "DATABASE": 4,
        "STORAGE": 5,
        "INFRASTRUCTURE": 6,
        "TESTING": 7,
        "BUILD / PACKAGE MANAGEMENT": 8,
        "OTHER": 9,
    }

    technologies.sort(key=lambda x: (
        category_order.get(x["category"], 99),
        confidence_order.get(x["confidence"], 9),
        x["name"]
    ))

    return technologies

def build_technology_stack(scanned_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build technology stack data structure ready for API schemas and database persistence.
    """
    techs = detect_technologies(scanned_files)
    categories_found = set(t["category"] for t in techs)

    return {
        "technologies": techs,
        "total_count": len(techs),
        "category_count": len(categories_found)
    }
