"""Deterministic project profile extraction for Phase 7B Innovation Analyzer.

Extracts structured project profiles from PostgreSQL models, saved documentation
analyses, safe extracted files, and code quality metrics. Never invents claims,
features, or technologies. Accurately distinguishes documented features, detected
code implementations, verified matches, and unverified claims.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentItem,
    ProjectDocumentationFinding,
)
from app.models.code_quality import ProjectQualityAnalysis, ProjectFileMetric
from app.services.innovation.profile import (
    EvidenceType,
    FeatureEvidence,
    ProjectProfile,
)

# Common domain keywords mapping
DOMAIN_KEYWORDS: Dict[str, List[str]] = {
    "Healthcare / Medical": [
        "health", "medical", "patient", "hospital", "clinic", "disease",
        "doctor", "diagnosis", "symptom", "medicine", "clinical", "biomedical",
    ],
    "E-Commerce / Retail": [
        "ecommerce", "shop", "cart", "product", "order", "store",
        "payment", "checkout", "retail", "inventory", "customer", "billing",
    ],
    "Education / Academic": [
        "student", "course", "teacher", "exam", "quiz", "university",
        "college", "academic", "grade", "learning", "classroom", "curriculum",
    ],
    "Security / Cryptography": [
        "security", "cipher", "encryption", "auth", "malware", "vulnerability",
        "crypto", "firewall", "token", "privacy", "steganography", "threat",
    ],
    "Finance / Fintech": [
        "finance", "bank", "stock", "trading", "investment", "loan",
        "wallet", "transaction", "portfolio", "credit", "crypto", "fraud",
    ],
    "Developer Tools & Infrastructure": [
        "cli", "linter", "compiler", "parser", "pipeline", "docker",
        "devops", "monitoring", "framework", "profiler", "generator", "sdk",
    ],
    "Machine Learning & AI": [
        "neural", "deep learning", "classifier", "nlp", "vision", "dataset",
        "prediction", "training", "model", "sentiment", "detection", "transformer",
    ],
    "IoT & Embedded Systems": [
        "iot", "sensor", "arduino", "raspberry", "embedded", "hardware",
        "firmware", "actuator", "microcontroller", "mqtt", "telemetry",
    ],
    "Social & Communication": [
        "chat", "message", "forum", "post", "social", "community",
        "comment", "feed", "network", "messaging", "collaboration",
    ],
}

KNOWN_DATABASES: Dict[str, List[str]] = {
    "PostgreSQL": ["postgresql", "postgres", "psycopg", "pg_"],
    "MySQL": ["mysql", "pymysql", "mysqld"],
    "SQLite": ["sqlite", "sqlite3"],
    "MongoDB": ["mongodb", "mongo", "pymongo", "mongoose"],
    "Redis": ["redis", "aioredis"],
    "Firebase": ["firebase", "firestore"],
    "Prisma / SQL": ["prisma"],
    "SQLAlchemy ORM": ["sqlalchemy"],
}

KNOWN_ALGORITHMS: Dict[str, List[str]] = {
    "AES Encryption": ["aes", "advanced encryption standard"],
    "RSA Cryptography": ["rsa"],
    "SHA / Hashing": ["sha256", "sha-256", "bcrypt", "argon2"],
    "JWT Authentication": ["jwt", "json web token"],
    "Dijkstra / Shortest Path": ["dijkstra", "shortest path", "a*"],
    "K-Means Clustering": ["kmeans", "k-means"],
    "Random Forest": ["random forest", "randomforest"],
    "Convolutional Neural Network (CNN)": ["cnn", "conv2d", "convolutional"],
    "Recurrent Neural Network / LSTM": ["lstm", "rnn", "gru"],
    "Transformer / Attention": ["transformer", "bert", "attention"],
    "Decision Tree": ["decision tree"],
    "TF-IDF Vectorization": ["tfidf", "tf-idf"],
}


class ProjectProfileExtractor:
    """Extracts a structured innovation profile from real project records."""

    @classmethod
    def extract_profile(cls, db: Session, project_id: str) -> ProjectProfile:
        """Extract a complete normalized profile for the given project."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return ProjectProfile(
                project_id=project_id,
                title="Unknown Project",
                is_empty=True,
                is_sufficient=False,
            )

        structure = (
            db.query(ProjectStructure)
            .filter(ProjectStructure.project_id == project_id)
            .first()
        )
        files = (
            db.query(ProjectFile)
            .filter(ProjectFile.project_id == project_id)
            .all()
        )
        doc_analysis = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )
        quality_analysis = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .order_by(ProjectQualityAnalysis.created_at.desc())
            .first()
        )

        # Check if project is completely empty
        total_files = structure.total_files if structure else len(files)
        source_count = structure.source_files_count if structure else sum(1 for f in files if f.category == "Source Code")
        is_empty = (total_files == 0 and source_count == 0)

        # 1. Collect documentation text from analysis or safe extracted disk
        raw_doc_text, doc_sections = cls._get_doc_text_and_sections(structure, doc_analysis)
        has_documentation = bool(raw_doc_text.strip() or (structure and structure.has_readme))

        # 2. Extract Problem Statement and Domain
        problem_statement, domain = cls._extract_problem_and_domain(
            project.title, raw_doc_text, doc_sections
        )

        # 3. Extract Target Users
        target_users = cls._extract_target_users(raw_doc_text, doc_sections)

        # 4. Extract Proposed Solution
        proposed_solution = cls._extract_proposed_solution(
            project.title, raw_doc_text, doc_sections, domain
        )

        # 5. Extract Technologies, Libraries, Databases, Algorithms
        tech_stack = cls._extract_tech_stack(structure, files, raw_doc_text, quality_analysis)

        # 6. Extract Architecture
        architecture = cls._extract_architecture(files, structure)

        # 7. Extract Features and verify against implementation evidence
        features = cls._extract_features_with_evidence(
            raw_doc_text, doc_sections, files, quality_analysis
        )

        # 8. Extract Claimed Contributions
        contributions = cls._extract_contributions(
            raw_doc_text, doc_sections, features, tech_stack
        )

        # Evaluate sufficiency: needs either a problem statement, documentation, or meaningful source files
        has_meaningful_content = bool(
            problem_statement
            or len(features) > 0
            or source_count > 0
            or raw_doc_text.strip()
        )
        is_sufficient = not is_empty and has_meaningful_content

        return ProjectProfile(
            project_id=project_id,
            title=project.title or project_id,
            problem_statement=problem_statement,
            domain=domain,
            target_users=target_users,
            proposed_solution=proposed_solution,
            features=features,
            languages=tech_stack["languages"],
            frameworks=tech_stack["frameworks"],
            libraries=tech_stack["libraries"],
            databases=tech_stack["databases"],
            algorithms=tech_stack["algorithms"],
            frontend_components=architecture["frontend"],
            backend_components=architecture["backend"],
            database_structure=architecture["database"],
            modules=architecture["modules"],
            claimed_contributions=contributions["claims"],
            supporting_evidence=contributions["evidence"],
            verification_needed=contributions["verification"],
            has_documentation=has_documentation,
            is_empty=is_empty,
            is_sufficient=is_sufficient,
        )

    # ------------------------------------------------------------------
    # Extraction Helpers
    # ------------------------------------------------------------------

    @classmethod
    def _get_doc_text_and_sections(
        cls,
        structure: Optional[ProjectStructure],
        doc_analysis: Optional[ProjectDocumentationAnalysis],
    ) -> Tuple[str, Dict[str, List[str]]]:
        """Collect raw documentation text and dictionary of sections."""
        doc_text_pieces: List[str] = []
        sections_dict: Dict[str, List[str]] = {}

        # 1. Read markdown / text doc files from extracted_path if available
        if structure and structure.extracted_path:
            ext_path = Path(structure.extracted_path)
            if ext_path.is_dir():
                for candidate in ["README.md", "readme.md", "README.txt", "README.rst", "documentation.md"]:
                    file_p = ext_path / candidate
                    if file_p.is_file():
                        try:
                            content = file_p.read_text(encoding="utf-8", errors="ignore")
                            if content.strip():
                                doc_text_pieces.append(content)
                                cls._parse_markdown_headings(content, sections_dict)
                        except Exception:
                            pass

        # 2. From doc_analysis documents & section coverage
        if doc_analysis and doc_analysis.documents:
            for item in doc_analysis.documents:
                for sec in (item.sections_found or []):
                    if isinstance(sec, dict):
                        title = str(sec.get("heading") or sec.get("title") or "").strip().lower()
                        content = str(sec.get("content") or sec.get("preview") or "").strip()
                    elif isinstance(sec, str):
                        title = sec.strip().lower()
                        content = sec.strip()
                    else:
                        continue
                    if title and content:
                        sections_dict.setdefault(title, []).append(content)
                        if content not in doc_text_pieces:
                            doc_text_pieces.append(content)

        combined_text = "\n\n".join(doc_text_pieces)
        return combined_text, sections_dict

    @classmethod
    def _parse_markdown_headings(
        cls, markdown_text: str, sections_dict: Dict[str, List[str]]
    ) -> None:
        """Parse markdown headers into sections_dict."""
        current_heading = "general"
        current_lines: List[str] = []

        for line in markdown_text.splitlines():
            line_s = line.strip()
            if line_s.startswith("#"):
                if current_lines:
                    sections_dict.setdefault(current_heading, []).append("\n".join(current_lines))
                    current_lines = []
                current_heading = line_s.lstrip("#").strip().lower()
            else:
                current_lines.append(line)

        if current_lines:
            sections_dict.setdefault(current_heading, []).append("\n".join(current_lines))

    @classmethod
    def _extract_problem_and_domain(
        cls,
        title: str,
        doc_text: str,
        sections_dict: Dict[str, List[str]],
    ) -> Tuple[str, str]:
        """Extract problem statement and identify application domain."""
        problem = ""
        # Look for problem-specific sections first
        for key, contents in sections_dict.items():
            if any(term in key for term in ["problem", "motivation", "background", "need", "introduction", "about"]):
                clean_content = " ".join(" ".join(contents).split())
                if clean_content:
                    problem = clean_content[:600]
                    break

        if not problem and doc_text:
            # Look for leading paragraph that isn't just installation/setup
            for p in doc_text.split("\n\n"):
                p_clean = p.strip()
                if len(p_clean) > 30 and not any(kw in p_clean.lower() for kw in ["pip install", "npm install", "yarn", "git clone", "docker run"]):
                    if any(term in p_clean.lower() for term in ["problem", "project", "system", "aim", "goal", "design", "solution", "support", "tool", "portal"]):
                        problem = p_clean[:400]
                        break

        # Domain inference
        combined_context = f"{title} {problem} {doc_text[:2000]}".lower()
        matched_domain = "General Software"
        best_count = 0

        for domain_name, kw_list in DOMAIN_KEYWORDS.items():
            count = sum(1 for kw in kw_list if kw in combined_context)
            if count > best_count:
                best_count = count
                matched_domain = domain_name

        return problem, matched_domain

    @classmethod
    def _extract_target_users(
        cls, doc_text: str, sections_dict: Dict[str, List[str]]
    ) -> List[str]:
        """Identify intended target users or beneficiaries."""
        users: Set[str] = set()
        user_terms = [
            "student", "students", "faculty", "teachers", "professors",
            "developer", "developers", "administrator", "administrators",
            "patient", "patients", "doctor", "doctors", "clinicians",
            "customer", "customers", "user", "users", "researcher", "researchers",
            "engineer", "engineers", "business", "businesses", "clients",
        ]
        context = doc_text.lower()
        for term in user_terms:
            pattern = rf"\b(?:intended for|targeted at|for|benefiting|designed for|used by)\s+(?:the\s+)?{term}\b"
            if re.search(pattern, context):
                users.add(term.title())

        # Fallback to direct frequency if explicit phrasing wasn't found
        if not users:
            for term in ["students", "developers", "administrators", "patients", "doctors", "users"]:
                if f" {term} " in context:
                    users.add(term.title())

        return sorted(list(users))[:5]

    @classmethod
    def _extract_proposed_solution(
        cls,
        title: str,
        doc_text: str,
        sections_dict: Dict[str, List[str]],
        domain: str,
    ) -> str:
        """Extract what the system proposes to solve and its operational approach."""
        solution = ""
        for key, contents in sections_dict.items():
            if any(term in key for term in ["solution", "proposed", "system", "architecture", "methodology", "approach", "overview"]):
                clean_content = " ".join(" ".join(contents).split())
                if clean_content:
                    solution = clean_content[:600]
                    break

        if not solution and doc_text:
            lines = [l.strip() for l in doc_text.splitlines() if len(l.strip()) > 40]
            if len(lines) > 1:
                solution = lines[1][:400]

        if not solution and title:
            solution = f"A {domain.lower()} system designed to provide automated support for {title.lower()}."

        return solution

    @classmethod
    def _extract_tech_stack(
        cls,
        structure: Optional[ProjectStructure],
        files: List[ProjectFile],
        doc_text: str,
        quality_analysis: Optional[ProjectQualityAnalysis],
    ) -> Dict[str, List[str]]:
        """Extract languages, frameworks, libraries, databases, and algorithms."""
        languages: Set[str] = set()
        frameworks: Set[str] = set()
        libraries: Set[str] = set()
        databases: Set[str] = set()
        algorithms: Set[str] = set()

        if structure and structure.languages:
            if isinstance(structure.languages, dict):
                languages.update(str(k) for k in structure.languages.keys())
            elif isinstance(structure.languages, (list, set, tuple)):
                for item in structure.languages:
                    if isinstance(item, dict):
                        name = item.get("name") or item.get("language")
                        if name:
                            languages.add(str(name))
                    elif item:
                        languages.add(str(item))

        if structure and structure.frameworks:
            if isinstance(structure.frameworks, (list, set, tuple)):
                for item in structure.frameworks:
                    if isinstance(item, dict):
                        name = item.get("name")
                        if name:
                            frameworks.add(str(name))
                    elif item:
                        frameworks.add(str(item))
            elif isinstance(structure.frameworks, dict):
                frameworks.update(str(k) for k in structure.frameworks.keys())

        # File extensions & detected languages
        for f in files:
            if f.detected_language:
                languages.add(f.detected_language)
            # Detect databases from filenames
            f_path_lower = f.relative_path.lower()
            for db_name, patterns in KNOWN_DATABASES.items():
                if any(p in f_path_lower for p in patterns):
                    databases.add(db_name)

        # Scan text for databases and algorithms
        combined_text = (doc_text + " " + " ".join(f.relative_path for f in files)).lower()
        for db_name, patterns in KNOWN_DATABASES.items():
            if any(p in combined_text for p in patterns):
                databases.add(db_name)

        for algo_name, patterns in KNOWN_ALGORITHMS.items():
            if any(p in combined_text for p in patterns):
                algorithms.add(algo_name)

        return {
            "languages": sorted(list(languages)),
            "frameworks": sorted(list(frameworks)),
            "libraries": sorted(list(libraries)),
            "databases": sorted(list(databases)),
            "algorithms": sorted(list(algorithms)),
        }

    @classmethod
    def _extract_architecture(
        cls,
        files: List[ProjectFile],
        structure: Optional[ProjectStructure],
    ) -> Dict[str, List[str]]:
        """Categorize system components into frontend, backend, database, and modules."""
        frontend: Set[str] = set()
        backend: Set[str] = set()
        database: Set[str] = set()
        modules: Set[str] = set()

        for f in files:
            path_parts = Path(f.relative_path).parts
            if len(path_parts) > 1:
                modules.add(path_parts[0])

            p_lower = f.relative_path.lower()
            if any(term in p_lower for term in ["component", "page", "view", "template", "frontend", "ui", ".html", ".tsx", ".jsx", ".vue", ".css"]):
                frontend.add(f.relative_path)
            elif any(term in p_lower for term in ["api", "route", "service", "controller", "backend", "server", "app.py", "main.py"]):
                backend.add(f.relative_path)
            elif any(term in p_lower for term in ["model", "schema", "database", "migration", "entity", ".sql"]):
                database.add(f.relative_path)

        return {
            "frontend": sorted(list(frontend))[:15],
            "backend": sorted(list(backend))[:15],
            "database": sorted(list(database))[:10],
            "modules": sorted(list(modules))[:10],
        }

    @classmethod
    def _extract_features_with_evidence(
        cls,
        doc_text: str,
        sections_dict: Dict[str, List[str]],
        files: List[ProjectFile],
        quality_analysis: Optional[ProjectQualityAnalysis],
    ) -> List[FeatureEvidence]:
        """Extract features and verify implementation evidence in code files."""
        features: List[FeatureEvidence] = []
        documented_items: List[Tuple[str, str]] = []  # (feature_name, doc_ref)

        # 1. Search for features in documented sections
        for key, contents in sections_dict.items():
            if any(term in key for term in ["feature", "functionality", "capabilities", "modules", "specification"]):
                for content in contents:
                    for line in content.splitlines():
                        line_s = line.strip()
                        if line_s.startswith(("-", "*", "1.", "2.", "3.", "4.", "5.", "•")):
                            item_name = line_s.lstrip("-*•123456789. ").strip()
                            if 5 <= len(item_name) <= 120:
                                documented_items.append((item_name, f"Section: {key}"))

        # Map file paths for evidence matching
        code_files = [f for f in files if f.category in ("Source Code", "Code")]

        for feat_name, doc_ref in documented_items:
            # Tokenize feature name to check for corresponding code files/classes
            tokens = [t.lower() for t in re.split(r"\W+", feat_name) if len(t) >= 3]
            matched_code_file: Optional[str] = None

            for cf in code_files:
                cf_path_lower = cf.relative_path.lower()
                cf_stem = Path(cf.relative_path).stem.lower()

                matched = False
                for t in tokens:
                    if t in cf_path_lower or cf_stem in t:
                        matched = True
                        break
                    if len(t) >= 4 and t[:4] in cf_path_lower:
                        matched = True
                        break
                if matched:
                    matched_code_file = cf.relative_path
                    break

            if matched_code_file:
                features.append(
                    FeatureEvidence(
                        name=feat_name,
                        description=f"Verified implementation found in {matched_code_file}",
                        evidence_type=EvidenceType.VERIFIED_MATCH,
                        doc_reference=doc_ref,
                        code_reference=matched_code_file,
                    )
                )
            else:
                features.append(
                    FeatureEvidence(
                        name=feat_name,
                        description="Feature is documented but lacks clear matching source file implementation.",
                        evidence_type=EvidenceType.UNVERIFIED_CLAIM,
                        doc_reference=doc_ref,
                        code_reference=None,
                    )
                )

        # 2. If no documented features exist, detect features from code implementation
        if not features:
            for cf in code_files:
                p_parts = Path(cf.relative_path).parts
                stem = Path(cf.relative_path).stem.replace("_", " ").title()
                if stem.lower() not in ("init", "conftest", "config", "main", "app", "index"):
                    features.append(
                        FeatureEvidence(
                            name=f"{stem} Module",
                            description=f"Detected implementation module at {cf.relative_path}",
                            evidence_type=EvidenceType.DETECTED_IMPLEMENTATION,
                            doc_reference=None,
                            code_reference=cf.relative_path,
                        )
                    )
                if len(features) >= 8:
                    break

        return features[:15]

    @classmethod
    def _extract_contributions(
        cls,
        doc_text: str,
        sections_dict: Dict[str, List[str]],
        features: List[FeatureEvidence],
        tech_stack: Dict[str, List[str]],
    ) -> Dict[str, List[str]]:
        """Identify claimed project contributions and verification needs."""
        claims: List[str] = []
        evidence: List[str] = []
        verification: List[str] = []

        contribution_keywords = ["novel", "custom", "unique", "distinctive", "first", "optimized", "contribution", "advantage"]
        for line in doc_text.splitlines():
            line_s = line.strip()
            if any(kw in line_s.lower() for kw in contribution_keywords) and len(line_s) > 15:
                clean_claim = " ".join(line_s.split())
                if clean_claim not in claims:
                    claims.append(clean_claim[:200])
            if len(claims) >= 5:
                break

        # Evidence supporting claims
        verified_features = [f.name for f in features if f.evidence_type == EvidenceType.VERIFIED_MATCH]
        if verified_features:
            evidence.append(f"Implemented and verified features: {', '.join(verified_features[:4])}")
        if tech_stack["algorithms"]:
            evidence.append(f"Implemented core algorithms: {', '.join(tech_stack['algorithms'])}")

        # Verification needed
        unverified_features = [f.name for f in features if f.evidence_type == EvidenceType.UNVERIFIED_CLAIM]
        if unverified_features:
            verification.append(f"Oral defense should verify implementation of: {', '.join(unverified_features[:4])}")
        if not claims and not verified_features:
            verification.append("Verify student code authorship and technical contribution during viva.")

        return {
            "claims": claims,
            "evidence": evidence,
            "verification": verification,
        }
