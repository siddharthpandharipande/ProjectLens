import json
import os
import re
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.config import settings
from app.models.project import Project, ProjectFile, ProjectStructure
from app.schemas.project import FileCategory


class ProjectParser:
    """
    ProjectParser service:
    1. Extracts uploaded ZIP archives safely into isolated directories.
    2. Enforces security checks (path traversal, symlinks, file count and size limits).
    3. Categorizes every extracted file.
    4. Detects programming languages based on file extensions.
    5. Detects frameworks/libraries from manifests without code execution.
    6. Persists file inventory and structure summary in PostgreSQL.
    """

    # ── Extension to Language Mapping ──────────────────────────────────────────
    EXTENSION_LANGUAGE_MAP: Dict[str, str] = {
        ".py": "Python",
        ".pyw": "Python",
        ".java": "Java",
        ".c": "C",
        ".h": "C",
        ".cpp": "C++",
        ".cxx": "C++",
        ".cc": "C++",
        ".hpp": "C++",
        ".hxx": "C++",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".mts": "TypeScript",
        ".cts": "TypeScript",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".php": "PHP",
        ".rb": "Ruby",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".swift": "Swift",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "CSS",
        ".sass": "CSS",
        ".less": "CSS",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".bat": "Batch",
        ".ps1": "PowerShell",
        ".r": "R",
        ".dart": "Dart",
        ".scala": "Scala",
    }

    # ── Known Manifests & Framework Patterns ──────────────────────────────────
    PYTHON_FRAMEWORKS: Dict[str, Tuple[str, str]] = {
        "fastapi": ("FastAPI", "Web Framework"),
        "flask": ("Flask", "Web Framework"),
        "django": ("Django", "Full-Stack Web Framework"),
        "sqlalchemy": ("SQLAlchemy", "Database ORM"),
        "tortoise-orm": ("Tortoise ORM", "Async ORM"),
        "torch": ("PyTorch", "Deep Learning Framework"),
        "pytorch": ("PyTorch", "Deep Learning Framework"),
        "tensorflow": ("TensorFlow", "Machine Learning Platform"),
        "keras": ("Keras", "Deep Learning Library"),
        "pandas": ("Pandas", "Data Analysis Library"),
        "numpy": ("NumPy", "Scientific Computing"),
        "scikit-learn": ("Scikit-Learn", "Machine Learning Library"),
        "sklearn": ("Scikit-Learn", "Machine Learning Library"),
        "pydantic": ("Pydantic", "Data Validation Library"),
        "pytest": ("PyTest", "Testing Framework"),
        "celery": ("Celery", "Distributed Task Queue"),
        "streamlit": ("Streamlit", "Data App Framework"),
        "gradio": ("Gradio", "UI / ML Demo Framework"),
    }

    JS_FRAMEWORKS: Dict[str, Tuple[str, str]] = {
        "react": ("React", "Frontend UI Library"),
        "react-dom": ("React DOM", "Frontend UI Renderer"),
        "next": ("Next.js", "Full-Stack React Framework"),
        "vue": ("Vue.js", "Frontend Framework"),
        "nuxt": ("Nuxt", "Full-Stack Vue Framework"),
        "@angular/core": ("Angular", "Frontend Framework"),
        "svelte": ("Svelte", "UI Compiler / Framework"),
        "@sveltejs/kit": ("SvelteKit", "Full-Stack Framework"),
        "express": ("Express.js", "Backend Web Framework"),
        "@nestjs/core": ("NestJS", "Enterprise Backend Framework"),
        "tailwindcss": ("Tailwind CSS", "Utility-First CSS Framework"),
        "vite": ("Vite", "Frontend Tooling & Bundler"),
        "redux": ("Redux", "State Management"),
        "@reduxjs/toolkit": ("Redux Toolkit", "State Management"),
        "axios": ("Axios", "HTTP Client"),
        "prisma": ("Prisma", "Database ORM"),
        "@prisma/client": ("Prisma Client", "Database ORM"),
        "mongoose": ("Mongoose", "MongoDB ODM"),
        "graphql": ("GraphQL", "API Query Language"),
    }

    # Directories that should not be classified as regular source code
    IGNORED_DIRS = {
        "node_modules",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        "out",
        "target",
        "bin",
        "obj",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".git",
        ".svn",
        ".hg",
        ".idea",
        ".vscode",
        ".next",
        ".nuxt",
        ".cache",
    }

    @classmethod
    def get_project_extract_dir(cls, project_id: str) -> Path:
        """Get unique destination extraction directory for project."""
        target = settings.resolved_extracted_dir / project_id
        return target

    @classmethod
    def extract_zip_archive(cls, archive_path: str, project_id: str) -> Path:
        """
        Safely extracts an uploaded zip archive into an isolated folder.
        Enforces:
        - Absolute path & path traversal prevention
        - Windows-style backslash traversal prevention
        - Max file count limit
        - Max single file size limit
        - Max total uncompressed size limit
        - Disallow symlinks & special files
        - Clean rollback on failure
        """
        zip_file_path = Path(archive_path).resolve()
        if not zip_file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archive file not found: {archive_path}",
            )

        extract_dir = cls.get_project_extract_dir(project_id)
        if extract_dir.exists():
            shutil.rmtree(extract_dir, ignore_errors=True)
        extract_dir.mkdir(parents=True, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_file_path, "r") as zf:
                # 1. Integrity check
                bad_file = zf.testzip()
                if bad_file:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Archive is corrupt. Checksum failed for: {bad_file}",
                    )

                infolist = zf.infolist()

                # 2. Limit: max entries
                if len(infolist) > settings.MAX_EXTRACTED_FILES:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Archive contains {len(infolist)} files, exceeding limit of {settings.MAX_EXTRACTED_FILES}.",
                    )

                total_uncompressed_bytes = 0

                # 3. Pre-scan & validate each entry before extracting anything
                for member in infolist:
                    filename = member.filename
                    normalized = filename.replace("\\", "/")

                    # Prevent path traversal
                    if normalized.startswith("/") or re.match(r"^[a-zA-Z]:", normalized):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Archive contains absolute path entry.",
                        )
                    if ".." in normalized.split("/"):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Archive contains relative path traversal (..) entry.",
                        )

                    # Disallow symlinks (POSIX attribute 0o120000)
                    is_symlink = (member.external_attr >> 16) & 0o170000 == 0o120000
                    if is_symlink:
                        # Skip or reject symlinks safely
                        continue

                    # Check single file uncompressed size limit
                    if member.file_size > settings.max_single_file_size_bytes:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"File '{filename}' uncompressed size exceeds limit of {settings.MAX_SINGLE_FILE_SIZE_MB}MB.",
                        )

                    total_uncompressed_bytes += member.file_size

                # 4. Limit: total extracted size
                if total_uncompressed_bytes > settings.max_extracted_size_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Total uncompressed size exceeds limit of {settings.MAX_EXTRACTED_SIZE_MB}MB.",
                    )

                # 5. Extract files safely
                for member in infolist:
                    # Skip symlinks
                    if (member.external_attr >> 16) & 0o170000 == 0o120000:
                        continue

                    # Skip directory-only entries from writing files, but allow mkdir
                    normalized = member.filename.replace("\\", "/").strip("/")
                    if not normalized:
                        continue

                    # Compute target destination and verify commonpath
                    dest_path = (extract_dir / normalized).resolve()
                    if not str(dest_path).startswith(str(extract_dir.resolve())):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Attempted path breakout in archive member '{member.filename}'.",
                        )

                    if member.is_dir():
                        dest_path.mkdir(parents=True, exist_ok=True)
                    else:
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as source, open(dest_path, "wb") as target:
                            shutil.copyfileobj(source, target)

            return extract_dir

        except HTTPException:
            # Clean up on validation failure
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            raise
        except Exception as e:
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to extract project archive: {str(e)}",
            )

    @classmethod
    def categorize_file(cls, rel_path: str, filename: str, ext: str) -> Tuple[str, Optional[str]]:
        """
        Classifies file into an understandable category and detects programming language.
        Returns:
            Tuple of (category_name, detected_language)
        """
        parts = [p.lower() for p in rel_path.replace("\\", "/").split("/")]
        filename_lower = filename.lower()
        ext_lower = ext.lower()

        # Check if inside dependency or virtualenv directories
        if any(p in {"node_modules", "vendor"} for p in parts[:-1]):
            return FileCategory.DEPENDENCY_OR_ENV.value, None
        if any(p in {"venv", ".venv", "env", ".env"} for p in parts[:-1]):
            return FileCategory.DEPENDENCY_OR_ENV.value, None

        # Check if inside build, generated, cache, or git directories
        if any(p in {"dist", "build", "out", "target", "bin", "obj", "__pycache__", ".pytest_cache", ".next", ".nuxt"} for p in parts[:-1]):
            return FileCategory.BUILD_OR_GENERATED.value, None
        if any(p == ".git" for p in parts[:-1]) or parts[0] == ".git":
            return FileCategory.BUILD_OR_GENERATED.value, None

        # 1. Dependency or Environment Manifests / Lockfiles
        if filename_lower in {
            "requirements.txt",
            "package-lock.json",
            "yarn.lock",
            "pnpm-lock.yaml",
            "pipfile",
            "pipfile.lock",
            "poetry.lock",
            "cargo.lock",
            "go.sum",
            ".env",
            ".env.example",
            ".env.local",
            ".env.development",
            ".env.production",
        }:
            return FileCategory.DEPENDENCY_OR_ENV.value, None

        # 2. Documentation
        doc_names = {"readme", "license", "licence", "contributing", "changelog", "authors", "srs", "report"}
        base_name_no_ext = Path(filename_lower).stem
        if base_name_no_ext in doc_names or ext_lower in {".md", ".markdown", ".rst", ".adoc", ".pdf", ".docx", ".doc"}:
            return FileCategory.DOCUMENTATION.value, None
        if ext_lower == ".txt" and base_name_no_ext in doc_names:
            return FileCategory.DOCUMENTATION.value, None

        # 3. Datasets & Data files
        if ext_lower in {".csv", ".tsv", ".parquet", ".jsonl", ".sqlite", ".sqlite3", ".db", ".h5", ".hdf5", ".xlsx", ".xls", ".arrow"}:
            return FileCategory.DATASET.value, None

        # 4. Images & Static Assets
        if ext_lower in {
            ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp", ".tiff",
            ".woff", ".woff2", ".ttf", ".eot", ".mp3", ".mp4", ".wav", ".webm"
        }:
            return FileCategory.IMAGE_OR_ASSET.value, None

        # 5. Configuration Files
        if (
            filename_lower in {"package.json", "tsconfig.json", "dockerfile", "docker-compose.yml", "docker-compose.yaml", "pyproject.toml", "cargo.toml", "pom.xml", "build.gradle", "build.gradle.kts", "go.mod"}
            or ext_lower in {".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".xml"}
            or filename_lower.startswith(".editorconfig")
            or filename_lower.startswith(".prettier")
            or filename_lower.startswith(".eslint")
        ):
            return FileCategory.CONFIGURATION.value, None

        # 6. Build / Generated artifacts by extension
        if ext_lower in {".class", ".o", ".obj", ".exe", ".dll", ".so", ".dylib", ".map", ".min.js", ".min.css", ".pyc", ".pyo"}:
            return FileCategory.BUILD_OR_GENERATED.value, None

        # 7. Source Code (only if matched to recognized programming language)
        if ext_lower in cls.EXTENSION_LANGUAGE_MAP:
            return FileCategory.SOURCE_CODE.value, cls.EXTENSION_LANGUAGE_MAP[ext_lower]

        # Plain text files that aren't doc names
        if ext_lower == ".txt":
            return FileCategory.DOCUMENTATION.value, None

        return FileCategory.OTHER.value, None

    @classmethod
    def detect_frameworks(cls, extract_dir: Path) -> List[Dict[str, Any]]:
        """
        Scan extracted manifest files and detect frameworks/libraries with evidence.
        Does NOT execute, compile, or install anything.
        """
        detected: List[Dict[str, Any]] = []
        seen_names = set()

        def add_framework(name: str, category: str, evidence: str):
            if name not in seen_names:
                detected.append({
                    "name": name,
                    "category": category,
                    "evidence": evidence,
                })
                seen_names.add(name)

        # 1. Python: requirements.txt
        req_files = list(extract_dir.glob("**/requirements*.txt"))
        for req_file in req_files:
            if any(p in cls.IGNORED_DIRS for p in req_file.parts):
                continue
            try:
                content = req_file.read_text(encoding="utf-8", errors="ignore")
                rel = str(req_file.relative_to(extract_dir)).replace("\\", "/")
                for line in content.splitlines():
                    clean = line.strip().split("#")[0].strip()
                    if not clean:
                        continue
                    # Match package name (before ==, >=, <=, ~=, <, >)
                    pkg_match = re.match(r"^([a-zA-Z0-9_\-\.]+)", clean)
                    if pkg_match:
                        pkg_name = pkg_match.group(1).lower()
                        if pkg_name in cls.PYTHON_FRAMEWORKS:
                            fw_name, fw_cat = cls.PYTHON_FRAMEWORKS[pkg_name]
                            add_framework(fw_name, fw_cat, f"{rel} ({clean})")
            except Exception:
                pass

        # 2. Python: pyproject.toml
        pyproject_files = list(extract_dir.glob("**/pyproject.toml"))
        for pyproj in pyproject_files:
            if any(p in cls.IGNORED_DIRS for p in pyproj.parts):
                continue
            try:
                content = pyproj.read_text(encoding="utf-8", errors="ignore")
                rel = str(pyproj.relative_to(extract_dir)).replace("\\", "/")
                for pkg_key, (fw_name, fw_cat) in cls.PYTHON_FRAMEWORKS.items():
                    if re.search(rf'["\']{pkg_key}["\']', content, re.IGNORECASE) or re.search(rf'\b{pkg_key}\s*=', content, re.IGNORECASE):
                        add_framework(fw_name, fw_cat, f"{rel} (dependency entry: {pkg_key})")
            except Exception:
                pass

        # 3. Node.js: package.json
        pkg_json_files = list(extract_dir.glob("**/package.json"))
        for pkg_json in pkg_json_files:
            if any(p in cls.IGNORED_DIRS for p in pkg_json.parts):
                continue
            try:
                rel = str(pkg_json.relative_to(extract_dir)).replace("\\", "/")
                data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                for dep_name, version in deps.items():
                    dep_lower = dep_name.lower()
                    if dep_lower in cls.JS_FRAMEWORKS:
                        fw_name, fw_cat = cls.JS_FRAMEWORKS[dep_lower]
                        add_framework(fw_name, fw_cat, f"{rel} ({dep_name}@{version})")
            except Exception:
                pass

        # 4. Java: pom.xml
        pom_files = list(extract_dir.glob("**/pom.xml"))
        for pom in pom_files:
            if any(p in cls.IGNORED_DIRS for p in pom.parts):
                continue
            try:
                rel = str(pom.relative_to(extract_dir)).replace("\\", "/")
                content = pom.read_text(encoding="utf-8", errors="ignore")
                if "spring-boot" in content or "org.springframework.boot" in content:
                    add_framework("Spring Boot", "Enterprise Web Framework", f"{rel} (<artifactId>spring-boot</artifactId>)")
                if "hibernate" in content:
                    add_framework("Hibernate", "Database ORM", f"{rel} (hibernate dependency)")
                if "quarkus" in content or "io.quarkus" in content:
                    add_framework("Quarkus", "Cloud-Native Java Framework", f"{rel} (quarkus dependency)")
                if "junit" in content:
                    add_framework("JUnit", "Testing Framework", f"{rel} (junit dependency)")
            except Exception:
                pass

        # 5. Java/Kotlin: build.gradle / build.gradle.kts
        gradle_files = list(extract_dir.glob("**/build.gradle*"))
        for gradle in gradle_files:
            if any(p in cls.IGNORED_DIRS for p in gradle.parts):
                continue
            try:
                rel = str(gradle.relative_to(extract_dir)).replace("\\", "/")
                content = gradle.read_text(encoding="utf-8", errors="ignore")
                if "org.springframework.boot" in content or "spring-boot" in content:
                    add_framework("Spring Boot", "Enterprise Web Framework", f"{rel} (spring-boot plugin/dependency)")
                if "io.quarkus" in content:
                    add_framework("Quarkus", "Cloud-Native Java Framework", f"{rel} (quarkus dependency)")
            except Exception:
                pass

        # 6. Rust: Cargo.toml
        cargo_files = list(extract_dir.glob("**/Cargo.toml"))
        for cargo in cargo_files:
            if any(p in cls.IGNORED_DIRS for p in cargo.parts):
                continue
            try:
                rel = str(cargo.relative_to(extract_dir)).replace("\\", "/")
                content = cargo.read_text(encoding="utf-8", errors="ignore")
                rust_deps = {
                    "actix-web": ("Actix Web", "Web Framework"),
                    "axum": ("Axum", "Web Framework"),
                    "tokio": ("Tokio", "Async Runtime"),
                    "rocket": ("Rocket", "Web Framework"),
                    "diesel": ("Diesel", "Database ORM"),
                }
                for crate_name, (fw_name, fw_cat) in rust_deps.items():
                    if re.search(rf'\b{crate_name}\b', content):
                        add_framework(fw_name, fw_cat, f"{rel} (dependency: {crate_name})")
            except Exception:
                pass

        # 7. Go: go.mod
        go_mod_files = list(extract_dir.glob("**/go.mod"))
        for gomod in go_mod_files:
            if any(p in cls.IGNORED_DIRS for p in gomod.parts):
                continue
            try:
                rel = str(gomod.relative_to(extract_dir)).replace("\\", "/")
                content = gomod.read_text(encoding="utf-8", errors="ignore")
                go_deps = {
                    "github.com/gin-gonic/gin": ("Gin", "Web Framework"),
                    "github.com/gofiber/fiber": ("Fiber", "Web Framework"),
                    "github.com/labstack/echo": ("Echo", "Web Framework"),
                    "gorm.io/gorm": ("GORM", "Database ORM"),
                }
                for mod_path, (fw_name, fw_cat) in go_deps.items():
                    if mod_path in content:
                        add_framework(fw_name, fw_cat, f"{rel} (require {mod_path})")
            except Exception:
                pass

        return detected

    @classmethod
    def extract_and_parse_project(cls, db: Session, project: Project) -> ProjectStructure:
        """
        Executes full extraction, file inventory cataloging, language detection,
        and framework scanning for a Project. Persists records in PostgreSQL.
        """
        # 1. Safe extraction
        extract_dir = cls.extract_zip_archive(project.archive_path, project.id)

        # 2. Scan and inventory regular files
        file_records: List[ProjectFile] = []
        languages_stats: Dict[str, Dict[str, int]] = {}
        categories_stats: Dict[str, int] = {}

        total_files = 0
        source_files_count = 0
        total_source_bytes = 0
        has_readme = False
        has_git = False

        # Check for Git metadata (directory or file)
        git_dir = extract_dir / ".git"
        if git_dir.exists():
            has_git = True
        else:
            try:
                candidate_gits = [p for p in extract_dir.rglob(".git") if p.is_dir() or p.is_file()]
                if candidate_gits:
                    has_git = True
            except Exception:
                pass

        for root, dirs, files in os.walk(extract_dir):
            for file_name in files:
                full_path = Path(root) / file_name
                # Avoid symlinks
                if full_path.is_symlink():
                    continue

                rel_path = str(full_path.relative_to(extract_dir)).replace("\\", "/")
                file_size = full_path.stat().st_size
                ext = full_path.suffix.lower()

                # Check if it's a README
                if Path(file_name.lower()).stem == "readme":
                    has_readme = True

                category, detected_lang = cls.categorize_file(rel_path, file_name, ext)

                # Skip raw git objects from being listed as source code or project inventory
                if rel_path.startswith(".git/") or "/.git/" in f"/{rel_path}":
                    continue

                total_files += 1
                categories_stats[category] = categories_stats.get(category, 0) + 1

                if category == FileCategory.SOURCE_CODE.value and detected_lang:
                    source_files_count += 1
                    total_source_bytes += file_size

                    if detected_lang not in languages_stats:
                        languages_stats[detected_lang] = {"files": 0, "sizeBytes": 0}
                    languages_stats[detected_lang]["files"] += 1
                    languages_stats[detected_lang]["sizeBytes"] += file_size

                file_records.append(
                    ProjectFile(
                        project_id=project.id,
                        relative_path=rel_path,
                        filename=file_name,
                        extension=ext,
                        size_bytes=file_size,
                        category=category,
                        detected_language=detected_lang,
                    )
                )

        # 3. Detect Frameworks from manifests
        frameworks = cls.detect_frameworks(extract_dir)

        # 4. Save to Database: Clean any existing files for idempotency
        db.query(ProjectFile).filter(ProjectFile.project_id == project.id).delete()

        db.add_all(file_records)

        # Upsert ProjectStructure
        structure = db.query(ProjectStructure).filter(ProjectStructure.project_id == project.id).first()
        if not structure:
            structure = ProjectStructure(project_id=project.id)
            db.add(structure)

        structure.total_files = total_files
        structure.source_files_count = source_files_count
        structure.total_source_size_bytes = total_source_bytes
        structure.languages = languages_stats
        structure.frameworks = frameworks
        structure.categories_summary = categories_stats
        structure.has_readme = has_readme
        structure.has_git = has_git
        structure.extracted_path = str(extract_dir)

        # Update Project stage without claiming full evaluation complete
        project.processing_stage = "Structure analyzed"

        db.commit()
        db.refresh(structure)
        db.refresh(project)

        return structure
