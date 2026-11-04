import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any, Set, Tuple

from app.models.project import ProjectStructure, ProjectFile
from app.services.documentation.extractor import ExtractedDocument


KNOWN_TECH_SPECS: Dict[str, Dict[str, Any]] = {
    "fastapi": {"display": "FastAPI", "category": "Backend Framework", "keywords": ["fastapi"]},
    "flask": {"display": "Flask", "category": "Backend Framework", "keywords": ["flask"]},
    "django": {"display": "Django", "category": "Backend Framework", "keywords": ["django"]},
    "express": {"display": "Express.js", "category": "Backend Framework", "keywords": ["express"]},
    "nestjs": {"display": "NestJS", "category": "Backend Framework", "keywords": ["nestjs", "@nestjs"]},
    "spring": {"display": "Spring Boot", "category": "Backend Framework", "keywords": ["spring", "springboot"]},
    "react": {"display": "React", "category": "Frontend Framework", "keywords": ["react", "reactjs"]},
    "vue": {"display": "Vue.js", "category": "Frontend Framework", "keywords": ["vue", "vuejs"]},
    "angular": {"display": "Angular", "category": "Frontend Framework", "keywords": ["angular"]},
    "next": {"display": "Next.js", "category": "Full-Stack Framework", "keywords": ["nextjs", "next.js"]},
    "nuxt": {"display": "Nuxt", "category": "Frontend Framework", "keywords": ["nuxt", "nuxtjs"]},
    "svelte": {"display": "Svelte", "category": "Frontend Framework", "keywords": ["svelte"]},
    "pytorch": {"display": "PyTorch", "category": "Machine Learning", "keywords": ["pytorch", "torch"]},
    "tensorflow": {"display": "TensorFlow", "category": "Machine Learning", "keywords": ["tensorflow"]},
    "keras": {"display": "Keras", "category": "Deep Learning", "keywords": ["keras"]},
    "scikit-learn": {"display": "Scikit-Learn", "category": "Machine Learning", "keywords": ["scikit-learn", "sklearn"]},
    "pandas": {"display": "Pandas", "category": "Data Analysis", "keywords": ["pandas"]},
    "numpy": {"display": "NumPy", "category": "Scientific Computing", "keywords": ["numpy"]},
    "tailwindcss": {"display": "Tailwind CSS", "category": "Styling", "keywords": ["tailwindcss", "tailwind"]},
    "postgresql": {"display": "PostgreSQL", "category": "Database", "keywords": ["postgres", "postgresql", "psycopg"]},
    "mysql": {"display": "MySQL", "category": "Database", "keywords": ["mysql"]},
    "mongodb": {"display": "MongoDB", "category": "Database", "keywords": ["mongodb", "mongoose", "pymongo"]},
    "sqlite": {"display": "SQLite", "category": "Database", "keywords": ["sqlite", "sqlite3"]},
    "redis": {"display": "Redis", "category": "In-Memory Store", "keywords": ["redis"]},
}


class ConsistencyAnalyzer:
    """
    Evidence-based Code–Documentation Consistency service.
    Cross-checks documentation statements against:
    - Detected project frameworks and languages
    - Project file inventory
    - Manifest contents (package.json, requirements.txt, etc.)
    - Safe code inspection (routes, imports, functions)
    Produces advisory findings without fabricating evidence or executing code.
    """

    @classmethod
    def analyze(
        cls,
        documents: List[ExtractedDocument],
        structure: Optional[ProjectStructure],
        files: List[ProjectFile],
        project_dir: Path,
    ) -> List[Dict[str, Any]]:
        """
        Runs all consistency checks across documentation and project code.
        """
        findings: List[Dict[str, Any]] = []

        # 1. Gather codebase evidence
        detected_frameworks = cls._gather_framework_names(structure)
        detected_languages = cls._gather_language_names(structure, files)
        file_path_set = {f.relative_path.replace("\\", "/").lower(): f.relative_path for f in files}
        manifest_text = cls._gather_manifest_texts(project_dir)
        source_code_index = cls._index_source_symbols(project_dir, files)

        # 2. Technology consistency checks
        tech_findings = cls._check_technology_consistency(
            documents=documents,
            detected_frameworks=detected_frameworks,
            detected_languages=detected_languages,
            manifest_text=manifest_text,
            source_code_index=source_code_index,
        )
        findings.extend(tech_findings)

        # 3. File and component reference checks
        file_ref_findings = cls._check_file_references(
            documents=documents,
            file_path_set=file_path_set,
        )
        findings.extend(file_ref_findings)

        # 4. Implementation claims (API routes, algorithms, components)
        impl_findings = cls._check_implementation_claims(
            documents=documents,
            source_code_index=source_code_index,
        )
        findings.extend(impl_findings)

        # 5. Numerical performance claims
        num_findings = cls._check_numerical_claims(documents=documents)
        findings.extend(num_findings)

        return findings

    @classmethod
    def _gather_framework_names(cls, structure: Optional[ProjectStructure]) -> Set[str]:
        names: Set[str] = set()
        if not structure or not structure.frameworks:
            return names

        for item in structure.frameworks:
            if isinstance(item, dict):
                fw = item.get("framework") or item.get("name")
                if fw:
                    names.add(fw.lower())
            elif isinstance(item, str):
                names.add(item.lower())
        return names

    @classmethod
    def _gather_language_names(cls, structure: Optional[ProjectStructure], files: List[ProjectFile]) -> Set[str]:
        langs: Set[str] = set()
        if structure and structure.languages:
            for l_name in structure.languages.keys():
                langs.add(l_name.lower())
        for f in files:
            if f.detected_language:
                langs.add(f.detected_language.lower())
        return langs

    @classmethod
    def _gather_manifest_texts(cls, project_dir: Path) -> str:
        """Reads package.json, requirements.txt, pyproject.toml, pom.xml, etc. safely."""
        manifest_names = {
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "pom.xml",
            "build.gradle",
            "cargo.toml",
            "go.mod",
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
        }
        all_text = []
        if project_dir.exists():
            for root, _, files in os.walk(project_dir):
                for f in files:
                    if f.lower() in manifest_names:
                        full_p = Path(root) / f
                        try:
                            all_text.append(full_p.read_text(encoding="utf-8", errors="ignore").lower())
                        except Exception:
                            pass
        return "\n".join(all_text)

    @classmethod
    def _index_source_symbols(cls, project_dir: Path, files: List[ProjectFile]) -> Dict[str, Any]:
        """
        Safely scans source files for route declarations, class definitions,
        and algorithm identifiers without executing student code.
        """
        routes: Dict[str, List[str]] = {}  # "GET /api/users" -> ["app/api/users.py"]
        functions: Dict[str, List[str]] = {}
        classes: Dict[str, List[str]] = {}
        text_corpus: List[str] = []

        route_pattern = re.compile(
            r"""(?:@(?:app|router|api)\.(get|post|put|delete|patch)\s*\(\s*["']([^"']+)["'])|(?:app\.(get|post|put|delete|patch)\s*\(\s*["']([^"']+)["'])|(?:@(GetMapping|PostMapping|PutMapping|DeleteMapping)\s*\(\s*(?:value\s*=\s*)?["']([^"']+)["'])""",
            re.IGNORECASE,
        )
        fn_pattern = re.compile(r"""(?:def\s+([a-zA-Z0-9_]{3,})\b|function\s+([a-zA-Z0-9_]{3,})\b|const\s+([a-zA-Z0-9_]{3,})\s*=\s*(?:async\s*)?\()""")
        class_pattern = re.compile(r"""\bclass\s+([a-zA-Z0-9_]{3,})\b""")

        for pf in files:
            if pf.category != "Source Code":
                continue
            full_p = (project_dir / pf.relative_path.replace("\\", "/")).resolve()
            if not full_p.is_file():
                continue
            try:
                # Limit read size to 1MB per source file for safety
                content = full_p.read_text(encoding="utf-8", errors="ignore")[:1_000_000]
                text_corpus.append(content.lower())

                # Scan routes
                for m in route_pattern.finditer(content):
                    method = (m.group(1) or m.group(3) or m.group(5) or "").upper()
                    path = m.group(2) or m.group(4) or m.group(6) or ""
                    if method and path:
                        key = f"{method} {path}"
                        routes.setdefault(key, []).append(pf.relative_path)

                # Scan function names
                for m in fn_pattern.finditer(content):
                    name = m.group(1) or m.group(2) or m.group(3)
                    if name:
                        functions.setdefault(name.lower(), []).append(pf.relative_path)

                # Scan class names
                for m in class_pattern.finditer(content):
                    cname = m.group(1)
                    if cname:
                        classes.setdefault(cname.lower(), []).append(pf.relative_path)

            except Exception:
                continue

        return {
            "routes": routes,
            "functions": functions,
            "classes": classes,
            "corpus": " ".join(text_corpus),
        }

    @classmethod
    def _check_technology_consistency(
        cls,
        documents: List[ExtractedDocument],
        detected_frameworks: Set[str],
        detected_languages: Set[str],
        manifest_text: str,
        source_code_index: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        checked_techs: Set[str] = set()

        for doc in documents:
            doc_text_lower = doc.text.lower()

            for tech_key, info in KNOWN_TECH_SPECS.items():
                if tech_key in checked_techs:
                    continue

                # Check if documentation mentions this technology
                mentioned = False
                matched_kw = ""
                for kw in info["keywords"]:
                    # Word boundary search to avoid false positives (e.g. "go" in "good")
                    if re.search(rf"\b{re.escape(kw)}\b", doc_text_lower):
                        mentioned = True
                        matched_kw = kw
                        break

                if not mentioned:
                    continue

                checked_techs.add(tech_key)

                # Check codebase evidence
                has_fw_match = any(tech_key in fw or kw in fw for fw in detected_frameworks for kw in info["keywords"])
                has_manifest_match = any(kw in manifest_text for kw in info["keywords"])
                has_code_match = any(kw in source_code_index["corpus"] for kw in info["keywords"])

                # Find excerpt and location in document
                loc_ref, excerpt = cls._find_excerpt_in_doc(doc, matched_kw)

                if has_fw_match or has_manifest_match or has_code_match:
                    evidence_src = []
                    if has_fw_match:
                        evidence_src.append("project structure framework detector")
                    if has_manifest_match:
                        evidence_src.append("dependency manifest files")
                    if has_code_match:
                        evidence_src.append("source code imports/declarations")

                    findings.append({
                        "rule_id": "TECH_CONSISTENCY_VERIFIED",
                        "title": f"Verified Technology: {info['display']}",
                        "severity": "advisory",
                        "category": "technology_consistency",
                        "explanation": f"Documentation mentions {info['display']}, which is confirmed by {' and '.join(evidence_src)}.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": f"Found matching evidence in {', '.join(evidence_src)}.",
                        "verification_status": "verified",
                        "faculty_guidance": "Technology claim is verified against codebase evidence.",
                    })
                else:
                    findings.append({
                        "rule_id": "TECH_CONSISTENCY_MISMATCH",
                        "title": f"Unverified Technology: {info['display']}",
                        "severity": "medium",
                        "category": "technology_consistency",
                        "explanation": (
                            f"Documentation references {info['display']}, but no matching framework, "
                            f"dependency manifest, or source code import was detected in the project."
                        ),
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": None,
                        "verification_status": "potential_inconsistency",
                        "faculty_guidance": (
                            f"Ask students during project evaluation to clarify how {info['display']} "
                            f"is utilized or if it was replaced with an alternative."
                        ),
                    })

        # Check for major detected frameworks completely omitted in docs
        for fw in detected_frameworks:
            fw_key = fw.split()[0].lower()
            if fw_key in KNOWN_TECH_SPECS:
                disp = KNOWN_TECH_SPECS[fw_key]["display"]
                all_docs_text = " ".join(d.text.lower() for d in documents)
                if not any(re.search(rf"\b{re.escape(kw)}\b", all_docs_text) for kw in KNOWN_TECH_SPECS[fw_key]["keywords"]):
                    findings.append({
                        "rule_id": "TECH_UNDOCUMENTED",
                        "title": f"Undocumented Core Technology: {disp}",
                        "severity": "low",
                        "category": "technology_consistency",
                        "explanation": f"The codebase contains evidence of {disp}, but this technology is never mentioned in the documentation.",
                        "doc_path": None,
                        "location_ref": "Project Manifests",
                        "documented_claim": None,
                        "code_evidence": f"Detected in project manifest / structure analysis as {fw}.",
                        "verification_status": "potential_inconsistency",
                        "faculty_guidance": f"Ask team why {disp} was used without being documented in the project report or README.",
                    })

        return findings

    @classmethod
    def _check_file_references(
        cls,
        documents: List[ExtractedDocument],
        file_path_set: Dict[str, str],
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        checked_refs: Set[str] = set()

        file_ref_regex = re.compile(
            r"""(?:`([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]{1,5})`)|(?:\b((?:[a-zA-Z0-9_\-]+\/)+[a-zA-Z0-9_\-]+\.[a-zA-Z0-9]{1,5})\b)"""
        )

        for doc in documents:
            for match in file_ref_regex.finditer(doc.text):
                ref = match.group(1) or match.group(2)
                if not ref:
                    continue
                ref_norm = ref.replace("\\", "/").strip("./").lower()

                # Filter out obvious non-project file strings (URLs, versions, etc.)
                if (
                    ref_norm in checked_refs
                    or ref_norm.endswith(".com")
                    or ref_norm.endswith(".org")
                    or ref_norm.endswith(".net")
                    or "/" not in ref_norm and not any(ref_norm.endswith(ext) for ext in [".py", ".js", ".ts", ".tsx", ".java", ".html", ".css", ".json", ".sql", ".sh"])
                ):
                    continue

                checked_refs.add(ref_norm)
                loc_ref, excerpt = cls._find_excerpt_in_doc(doc, ref)

                # Check if file exists in project
                matched_actual_path = None
                if ref_norm in file_path_set:
                    matched_actual_path = file_path_set[ref_norm]
                else:
                    # Check basename match (file may be in subfolder)
                    base_name = ref_norm.split("/")[-1]
                    for f_lower, actual_p in file_path_set.items():
                        if f_lower.endswith("/" + base_name) or f_lower == base_name:
                            matched_actual_path = actual_p
                            break

                if matched_actual_path:
                    findings.append({
                        "rule_id": "REF_FILE_VERIFIED",
                        "title": f"Documented File Verified: {ref}",
                        "severity": "advisory",
                        "category": "file_reference",
                        "explanation": f"Documented file '{ref}' was located in the project file inventory as '{matched_actual_path}'.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": f"File exists on disk at '{matched_actual_path}'.",
                        "verification_status": "verified",
                        "faculty_guidance": "Documented component path confirmed.",
                    })
                else:
                    findings.append({
                        "rule_id": "REF_FILE_NOT_FOUND",
                        "title": f"Referenced File Not Found: {ref}",
                        "severity": "low",
                        "category": "file_reference",
                        "explanation": f"Documentation mentions file '{ref}', but it was not found in the submitted project directory.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": None,
                        "verification_status": "claim_not_verified",
                        "faculty_guidance": "Check if this file was renamed, relocated, or omitted from the archive submission.",
                    })

                if len(findings) >= 20:
                    break

        return findings

    @classmethod
    def _check_implementation_claims(
        cls,
        documents: List[ExtractedDocument],
        source_code_index: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []

        # 1. API Route endpoint claims
        endpoint_regex = re.compile(
            r"""\b(GET|POST|PUT|DELETE|PATCH)\s+([\/][a-zA-Z0-9_\-\/\{\}]+)""",
            re.IGNORECASE,
        )
        checked_endpoints: Set[str] = set()

        for doc in documents:
            for match in endpoint_regex.finditer(doc.text):
                method = match.group(1).upper()
                route = match.group(2)
                ep_key = f"{method} {route}"
                if ep_key in checked_endpoints:
                    continue
                checked_endpoints.add(ep_key)

                loc_ref, excerpt = cls._find_excerpt_in_doc(doc, match.group(0))

                # Check if route is in indexed routes
                matched_files = source_code_index["routes"].get(ep_key)
                if not matched_files:
                    # Try partial path match
                    route_path_only = route.rstrip("/")
                    for r_key, r_files in source_code_index["routes"].items():
                        if r_key.endswith(route_path_only) or route_path_only in r_key:
                            matched_files = r_files
                            break

                if matched_files:
                    findings.append({
                        "rule_id": "CLAIM_ENDPOINT_VERIFIED",
                        "title": f"Documented API Endpoint Verified: {ep_key}",
                        "severity": "advisory",
                        "category": "implementation_claim",
                        "explanation": f"Documentation specifies endpoint '{ep_key}', which is declared in source file(s): {', '.join(matched_files[:2])}.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": f"Route handler declared in {', '.join(matched_files)}.",
                        "verification_status": "verified",
                        "faculty_guidance": "API route implementation verified against codebase.",
                    })
                else:
                    findings.append({
                        "rule_id": "CLAIM_ENDPOINT_UNVERIFIED",
                        "title": f"API Endpoint Unverified: {ep_key}",
                        "severity": "medium",
                        "category": "implementation_claim",
                        "explanation": f"Documentation describes endpoint '{ep_key}', but no corresponding route handler was detected in source code.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": None,
                        "verification_status": "claim_not_verified",
                        "faculty_guidance": "Ask students to demonstrate where this endpoint is handled or if it is simulated/mocked.",
                    })

        # 2. Key algorithms and architecture components
        claims_to_check = [
            ("JWT Authentication", ["jwt", "jsonwebtoken", "pyjwt", "bearer token"]),
            ("OAuth2 Authentication", ["oauth", "oauth2"]),
            ("Bcrypt Password Hashing", ["bcrypt", "passlib"]),
            ("WebSocket Real-time Communication", ["websocket", "websockets", "socket.io"]),
            ("AES Encryption", ["aes", "pycryptodome", "cryptography"]),
            ("Random Forest Classifier", ["randomforest", "randomforestclassifier"]),
            ("Convolutional Neural Network (CNN)", ["conv2d", "convolutional", "cnn"]),
            ("Redis Caching", ["redis", "aioredis"]),
        ]

        for claim_name, keywords in claims_to_check:
            for doc in documents:
                doc_lower = doc.text.lower()
                matched_kw = None
                for kw in keywords:
                    if re.search(rf"\b{re.escape(kw)}\b", doc_lower):
                        matched_kw = kw
                        break
                if not matched_kw:
                    continue

                loc_ref, excerpt = cls._find_excerpt_in_doc(doc, matched_kw)
                code_matched = any(kw in source_code_index["corpus"] for kw in keywords)

                if code_matched:
                    findings.append({
                        "rule_id": "CLAIM_ALGORITHM_VERIFIED",
                        "title": f"Implementation Claim Verified: {claim_name}",
                        "severity": "advisory",
                        "category": "implementation_claim",
                        "explanation": f"Documentation claims use of {claim_name}, and related imports/identifiers were found in the codebase.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": f"Matching symbols for {claim_name} found in source text.",
                        "verification_status": "verified",
                        "faculty_guidance": "Implementation claim supported by codebase evidence.",
                    })
                else:
                    findings.append({
                        "rule_id": "CLAIM_ALGORITHM_UNVERIFIED",
                        "title": f"Unverified Implementation Claim: {claim_name}",
                        "severity": "medium",
                        "category": "implementation_claim",
                        "explanation": f"Documentation claims to implement {claim_name}, but no related imports or function calls were detected in source files.",
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": None,
                        "verification_status": "claim_not_verified",
                        "faculty_guidance": f"Ask students to walk through their implementation of {claim_name} during evaluation.",
                    })
                break

        return findings

    @classmethod
    def _check_numerical_claims(cls, documents: List[ExtractedDocument]) -> List[Dict[str, Any]]:
        findings: List[Dict[str, Any]] = []
        checked_claims: Set[str] = set()

        numerical_patterns = [
            # Accuracy / precision / recall
            re.compile(r"""(?:(?:accuracy|precision|recall|f1-?score|success\s+rate|test\s+pass\s+rate)\s*(?:of|is|was|reached|achieved|approximately|~)?\s*([0-9]{1,3}(?:\.[0-9]{1,3})?\s*(?:%|percent)))""", re.IGNORECASE),
            re.compile(r"""([0-9]{1,3}(?:\.[0-9]{1,3})?\s*(?:%|percent))\s+(?:accuracy|precision|recall|f1-?score|success\s+rate)""", re.IGNORECASE),
            # Latency / response time
            re.compile(r"""(?:(?:latency|response\s+time|execution\s+time|throughput)\s*(?:of|is|was|under|<|~)?\s*([0-9]+(?:\.[0-9]+)?\s*(?:ms|milliseconds|seconds|fps|req\/s)))""", re.IGNORECASE),
            re.compile(r"""([0-9]+(?:\.[0-9]+)?\s*(?:ms|milliseconds|seconds|fps))\s+(?:latency|response\s+time|execution\s+time)""", re.IGNORECASE),
        ]

        for doc in documents:
            for pattern in numerical_patterns:
                for match in pattern.finditer(doc.text):
                    full_str = match.group(0).strip()
                    val = match.group(1).strip()
                    claim_key = f"{doc.relative_path}:{val}"
                    if claim_key in checked_claims:
                        continue
                    checked_claims.add(claim_key)

                    loc_ref, excerpt = cls._find_excerpt_in_doc(doc, full_str)

                    findings.append({
                        "rule_id": "CLAIM_NUMERICAL_UNVERIFIED",
                        "title": f"Unverified Numerical Claim: {full_str}",
                        "severity": "advisory",
                        "category": "numerical_claim",
                        "explanation": (
                            f"Project documentation reports a performance metric of '{full_str}'. "
                            f"Student code is not executed during static analysis, so this claim cannot be automatically verified."
                        ),
                        "doc_path": doc.relative_path,
                        "location_ref": loc_ref,
                        "documented_claim": excerpt,
                        "code_evidence": None,
                        "verification_status": "claim_not_verified",
                        "faculty_guidance": "Ask the student team to show benchmark scripts, test logs, or live demonstrations verifying this numerical result.",
                    })

                    if len(findings) >= 15:
                        return findings

        return findings

    @classmethod
    def _find_excerpt_in_doc(cls, doc: ExtractedDocument, keyword: str) -> Tuple[str, str]:
        """
        Locates the keyword in the document, returns (location_ref, excerpt).
        """
        # Search in sections first
        for sec in doc.sections:
            if keyword.lower() in sec.content.lower() or keyword.lower() in sec.heading.lower():
                loc = f"Section '{sec.heading}'"
                if sec.page_number:
                    loc += f" (Page {sec.page_number})"
                elif sec.line_number:
                    loc += f" (Line ~{sec.line_number})"

                # Extract surrounding excerpt (approx 150 chars)
                idx = sec.content.lower().find(keyword.lower())
                if idx != -1:
                    start = max(0, idx - 40)
                    end = min(len(sec.content), idx + len(keyword) + 60)
                    snippet = sec.content[start:end].replace("\n", " ").strip()
                    return loc, f"...{snippet}..."
                return loc, f"Referenced under heading '{sec.heading}'"

        # Search in pages
        for page in doc.pages:
            p_text = page.get("text", "")
            if keyword.lower() in p_text.lower():
                loc = f"Page {page.get('page_number', 1)}"
                idx = p_text.lower().find(keyword.lower())
                start = max(0, idx - 40)
                end = min(len(p_text), idx + len(keyword) + 60)
                snippet = p_text[start:end].replace("\n", " ").strip()
                return loc, f"...{snippet}..."

        # Fallback to document body
        idx = doc.text.lower().find(keyword.lower())
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(doc.text), idx + len(keyword) + 60)
            snippet = doc.text[start:end].replace("\n", " ").strip()
            return f"File '{doc.filename}'", f"...{snippet}..."

        return f"File '{doc.filename}'", f"Contains mention of '{keyword}'"
