"""Viva Evidence Builder (Phase 8).

Collects and compiles factual, PII-safe project evidence from all completed
ProjectLens analysis modules (Parser, Code Quality, Documentation, Git History,
and Innovation) to build a contextual profile for personalized viva question generation.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.code_quality import ProjectQualityAnalysis
from app.models.documentation import ProjectDocumentationAnalysis
from app.models.git_history import ProjectGitHistoryAnalysis
from app.models.innovation import ProjectInnovationAnalysis


class VivaEvidenceBuilder:
    """Extracts compact, high-signal project evidence for viva question generation."""

    @classmethod
    def build_project_context(cls, db: Session, project_id: str) -> Dict[str, Any]:
        """Aggregate evidence across all analysis modules for project_id."""
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return {"project_id": project_id, "title": "Unknown Project", "is_empty": True}

        # 1. Project Basic Metadata (null-safe)
        context: Dict[str, Any] = {
            "project_id": project.id,
            "title": (project.title or "").strip() or "Untitled Software Project",
            "course": (project.course or "").strip() or "Computer Science Project",
            "team": (project.team or "").strip() or "Student Team",
            "file_size_bytes": getattr(project, "file_size_bytes", 0) or 0,
        }

        # 2. File & Technology Inventory
        files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()
        structure = db.query(ProjectStructure).filter(ProjectStructure.project_id == project_id).first()

        languages: Dict[str, int] = {}
        key_files: List[str] = []
        has_tests: bool = False
        has_docker: bool = False
        has_ci: bool = False
        has_database_files: bool = False

        for f in files:
            rel_path = (getattr(f, "relative_path", "") or "").strip()
            if not rel_path:
                continue

            lang = (getattr(f, "detected_language", "") or "").strip()
            if not lang:
                ext = (getattr(f, "extension", "") or "").lstrip(".")
                lang = ext if ext else "unknown"
            if lang and lang.lower() != "unknown":
                languages[lang] = languages.get(lang, 0) + 1

            path_lower = rel_path.lower()
            if any(term in path_lower for term in ("test", "spec", "tests")):
                has_tests = True
            if "docker" in path_lower or "container" in path_lower:
                has_docker = True
            if any(term in path_lower for term in (".github", "jenkins", "gitlab", ".circleci")):
                has_ci = True
            if any(term in path_lower for term in ("schema", "migration", "sql", "model", "database", "repo")):
                has_database_files = True

            # Collect representative implementation files
            cat = (getattr(f, "category", "") or "").strip()
            if len(key_files) < 15 and cat in ("Source Code", "Backend", "Frontend", "Code"):
                key_files.append(rel_path)

        context["total_files"] = len(files)
        context["languages"] = languages
        context["key_files"] = key_files[:12]
        context["has_tests"] = has_tests
        context["has_docker"] = has_docker
        context["has_ci"] = has_ci
        context["has_database_files"] = has_database_files

        # Frameworks detected in Phase 2 (clean string list)
        detected_frameworks: List[str] = []
        fw_ev = getattr(structure, "frameworks", None) or getattr(structure, "framework_evidence", None)
        if fw_ev:
            if isinstance(fw_ev, list):
                for item in fw_ev:
                    if isinstance(item, dict):
                        fw_name = item.get("framework") or item.get("name")
                        if fw_name and isinstance(fw_name, str) and fw_name.strip():
                            detected_frameworks.append(fw_name.strip())
                    elif isinstance(item, str) and item.strip():
                        detected_frameworks.append(item.strip())
            elif isinstance(fw_ev, dict):
                for k in fw_ev.keys():
                    if isinstance(k, str) and k.strip():
                        detected_frameworks.append(k.strip())
        context["frameworks"] = detected_frameworks

        # 3. Code Quality Metrics (Phase 3)
        quality = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .order_by(ProjectQualityAnalysis.created_at.desc())
            .first()
        )
        if quality:
            metrics = getattr(quality, "metrics_summary", {}) or {}
            raw_findings = getattr(quality, "findings", []) or []
            smells = []
            for f in raw_findings:
                if isinstance(f, dict):
                    msg = f.get("message") or f.get("description")
                    if msg and isinstance(msg, str) and msg.strip():
                        smells.append(msg.strip())
                elif isinstance(f, str) and f.strip():
                    smells.append(f.strip())

            try:
                avg_comp = float(metrics.get("cyclomatic_complexity_average", 0.0) or 0.0)
            except (ValueError, TypeError):
                avg_comp = 0.0
            try:
                max_comp = int(metrics.get("cyclomatic_complexity_max", 0) or 0)
            except (ValueError, TypeError):
                max_comp = 0
            try:
                tot_loc = int(metrics.get("total_loc", 0) or 0)
            except (ValueError, TypeError):
                tot_loc = 0
            try:
                high_comp = int(metrics.get("high_complexity_function_count", 0) or 0)
            except (ValueError, TypeError):
                high_comp = 0

            context["code_quality"] = {
                "total_loc": tot_loc,
                "avg_complexity": avg_comp,
                "max_complexity": max_comp,
                "high_complexity_functions": high_comp,
                "quality_score": getattr(quality, "score", None),
                "smells_detected": smells[:5],
            }
        else:
            context["code_quality"] = None

        # 4. Documentation Metrics (Phase 5) - Null-safe section extraction
        docs = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )
        if docs:
            raw_findings = getattr(docs, "findings", []) or []
            doc_findings = []
            for f in raw_findings:
                if isinstance(f, dict):
                    msg = f.get("explanation") or f.get("title") or f.get("message") or f.get("description")
                    if msg and isinstance(msg, str) and msg.strip():
                        doc_findings.append(msg.strip())
                elif hasattr(f, "explanation") or hasattr(f, "title") or hasattr(f, "message"):
                    msg = getattr(f, "explanation", None) or getattr(f, "title", None) or getattr(f, "message", None)
                    if msg and isinstance(msg, str) and msg.strip():
                        doc_findings.append(msg.strip())
                elif isinstance(f, str) and f.strip():
                    doc_findings.append(f.strip())

            coverage = getattr(docs, "section_coverage", []) or []
            sections_present: List[str] = []
            sections_missing: List[str] = []

            for c in coverage:
                if not isinstance(c, dict):
                    continue

                # Safely resolve section display name across schema formats:
                # 1. displayName (Pydantic by_alias serialized from SectionCoverageItem)
                # 2. display_name (standard snake_case)
                # 3. standard_section (legacy/heuristic format)
                # 4. sectionKey / section_key
                sec_name = (
                    c.get("displayName")
                    or c.get("display_name")
                    or c.get("standard_section")
                    or c.get("sectionKey")
                    or c.get("section_key")
                )
                if not sec_name or not isinstance(sec_name, str) or not sec_name.strip():
                    continue
                sec_name = sec_name.strip()

                # Determine if present (handles isPresent and is_present)
                is_pres = c.get("isPresent") if "isPresent" in c else c.get("is_present")
                is_pres_bool = bool(is_pres) if is_pres is not None else False

                if is_pres_bool:
                    sections_present.append(sec_name)
                else:
                    sections_missing.append(sec_name)

            context["documentation"] = {
                "total_documents": int(getattr(docs, "total_documents_count", 0) or 0),
                "total_words": int(getattr(docs, "total_words_count", 0) or 0),
                "sections_present": sections_present[:6],
                "sections_missing": sections_missing[:6],
                "findings": doc_findings[:4],
            }
        else:
            context["documentation"] = None

        # 5. Git Development History (Phase 6)
        git = (
            db.query(ProjectGitHistoryAnalysis)
            .filter(ProjectGitHistoryAnalysis.project_id == project_id)
            .order_by(ProjectGitHistoryAnalysis.created_at.desc())
            .first()
        )
        if git:
            metrics = getattr(git, "metrics_summary", {}) or {}
            context["git_history"] = {
                "total_commits": int(metrics.get("total_commits", 0) or 0),
                "total_authors": int(metrics.get("total_authors", 0) or 0),
                "has_velocity_anomaly": bool(metrics.get("has_velocity_anomaly", False)),
                "is_single_day": bool(metrics.get("is_single_day_development", False)),
                "is_shallow": bool(metrics.get("is_shallow_history", False)),
            }
        else:
            context["git_history"] = None

        # 6. Innovation & Profile (Phase 7B / 7C)
        inno = (
            db.query(ProjectInnovationAnalysis)
            .filter(ProjectInnovationAnalysis.project_id == project_id)
            .order_by(ProjectInnovationAnalysis.created_at.desc())
            .first()
        )
        if inno and getattr(inno, "project_profile", None):
            prof = inno.project_profile or {}

            features: List[str] = []
            for f in prof.get("features_extracted", []) or []:
                if isinstance(f, dict):
                    fname = f.get("name") or f.get("title") or f.get("feature")
                    if fname and isinstance(fname, str) and fname.strip():
                        features.append(fname.strip())
                elif isinstance(f, str) and f.strip():
                    features.append(f.strip())

            tech_used: List[str] = []
            for t in prof.get("technologies_used", []) or []:
                if isinstance(t, str) and t.strip():
                    tech_used.append(t.strip())

            domain_val = prof.get("domain")
            domain_str = domain_val.strip() if isinstance(domain_val, str) and domain_val.strip() else "Software Engineering"

            prob_val = prof.get("problem_statement")
            prob_str = prob_val.strip() if isinstance(prob_val, str) and prob_val.strip() else None

            sol_val = prof.get("proposed_solution")
            sol_str = sol_val.strip() if isinstance(sol_val, str) and sol_val.strip() else None

            abs_val = prof.get("abstract") or prof.get("project_abstract")
            abs_str = abs_val.strip() if isinstance(abs_val, str) and abs_val.strip() else None

            desc_val = prof.get("description") or prof.get("project_description")
            desc_str = desc_val.strip() if isinstance(desc_val, str) and desc_val.strip() else None

            context["innovation"] = {
                "domain": domain_str,
                "problem_statement": prob_str,
                "proposed_solution": sol_str,
                "abstract": abs_str,
                "description": desc_str,
                "technologies_used": tech_used,
                "distinctive_features": features[:6],
            }
        else:
            context["innovation"] = None

        # 7. Synthesized Weaknesses / Potential Viva Blind Spots (100% null-safe)
        weaknesses: List[str] = []
        if not has_tests:
            weaknesses.append("Lack of automated unit tests or integration test suites")
        if not has_docker:
            weaknesses.append("No containerization (Dockerfile) for environment reproducibility")
        if context.get("code_quality"):
            high_comp = context["code_quality"].get("high_complexity_functions", 0)
            if high_comp > 0:
                weaknesses.append(f"{high_comp} high cyclomatic complexity functions detected in source code")

        doc_ctx = context.get("documentation")
        if doc_ctx:
            missing_secs = [
                s for s in doc_ctx.get("sections_missing", [])
                if isinstance(s, str) and s.strip()
            ]
            if missing_secs:
                weaknesses.append(f"Missing documentation sections: {', '.join(missing_secs[:3])}")

        git_ctx = context.get("git_history")
        if git_ctx and (git_ctx.get("is_single_day") or git_ctx.get("is_shallow")):
            weaknesses.append("Development history appears compressed into a single day or shallow commit log")

        context["identified_weaknesses"] = weaknesses
        return context
