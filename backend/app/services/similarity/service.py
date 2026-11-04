"""
service.py

Orchestration service for Code Similarity Analysis.
Safely extracts project source files, executes candidate prefiltering,
calculates token, structural, and semantic similarity, applies coverage-aware
scoring, and stores results idempotently in PostgreSQL.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectFile
from app.models.similarity import ProjectSimilarityAnalysis, ProjectSimilarityMatch
from app.services.project_parser import ProjectParser
from app.services.similarity.candidate_generator import CandidateGenerator
from app.services.similarity.tokenizer import CodeTokenizer
from app.services.similarity.structural import StructuralSimilarityAnalyzer
from app.services.similarity.semantic import SemanticSimilarityService
from app.services.similarity.scoring import SimilarityScoringEngine


class SimilarityService:
    """Service for executing and retrieving code similarity comparisons."""

    @classmethod
    def _resolve_extract_dir(cls, db: Session, project: Project) -> Path:
        """Resolve absolute extraction path for project, re-extracting if missing."""
        if project.structure and project.structure.extracted_path:
            p = Path(project.structure.extracted_path).resolve()
            if p.exists():
                return p

        target = (Path(settings.EXTRACTED_DIR) / project.id).resolve()
        if not target.exists() and project.archive_path and Path(project.archive_path).exists():
            ProjectParser.extract_and_parse_project(db, project)
            db.refresh(project)
            if project.structure and project.structure.extracted_path:
                target = Path(project.structure.extracted_path).resolve()

        return target

    @classmethod
    def _read_file_safe(cls, extract_dir: Path, rel_path: str) -> Optional[str]:
        """Read file from disk with path containment verification."""
        file_path = (extract_dir / rel_path).resolve()
        try:
            file_path.relative_to(extract_dir)
        except ValueError:
            return None

        if not file_path.is_file():
            return None

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return None

    @classmethod
    def analyze_project(cls, db: Session, project_id: str) -> ProjectSimilarityAnalysis:
        """
        Execute or refresh similarity analysis for an existing project against
        all eligible cohort projects in the database.
        Safe and idempotent: atomically replaces previous results for the project.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Ensure project source files are indexed
        if not project.files:
            if project.archive_path and Path(project.archive_path).exists():
                ProjectParser.extract_and_parse_project(db, project)
                db.refresh(project)
            else:
                raise ValueError(f"Project '{project_id}' has no archive or extracted files to analyze.")

        current_extract_dir = cls._resolve_extract_dir(db, project)

        # Retrieve current project's source files
        current_source_files = (
            db.query(ProjectFile)
            .filter(
                ProjectFile.project_id == project_id,
                ProjectFile.category == "Source Code",
            )
            .order_by(ProjectFile.relative_path)
            .all()
        )

        # Compute current project total SLOC
        current_project_sloc = 0
        current_file_contents: Dict[str, Tuple[str, Optional[str], int]] = {}
        for pf in current_source_files:
            code = cls._read_file_safe(current_extract_dir, pf.relative_path)
            if code is not None:
                lines_count = len([l for l in code.splitlines() if l.strip()])
                current_project_sloc += lines_count
                current_file_contents[pf.relative_path] = (code, pf.detected_language, lines_count)

        # Query eligible cohort projects
        cohort_projects = CandidateGenerator.get_eligible_cohort_projects(db, project_id)

        # Build methods & limitations documentation
        methods_used = ["token_shingles", "hierarchical_ast"]
        limitations = [
            "Comparisons are restricted to projects in the local database.",
            "Structural AST analysis is supported for Python, Java, JavaScript, and TypeScript.",
            "External repositories and internet sources are not queried.",
        ]

        if settings.SIMILARITY_ENABLE_SEMANTIC:
            methods_used.append("semantic_embeddings")
        else:
            limitations.append("Semantic embedding similarity is disabled or unconfigured in settings.")

        # ── Case: No eligible cohort projects ─────────────────────────────────
        if not cohort_projects or not current_file_contents:
            return cls._save_analysis_record(
                db=db,
                project_id=project_id,
                status="no_candidates" if not cohort_projects else "insufficient_evidence",
                compared_projects_count=0,
                compared_files_count=len(current_file_contents),
                strongest_match_project_id=None,
                highest_similarity_score=None,
                methods_used=methods_used,
                limitations=limitations,
                matches=[],
            )

        # ── Compare against each cohort project ───────────────────────────────
        cohort_matches_data: List[Dict[str, Any]] = []
        total_compared_files_count = len(current_file_contents)

        for cohort in cohort_projects:
            cohort_extract_dir = cls._resolve_extract_dir(db, cohort)
            cohort_source_files = (
                db.query(ProjectFile)
                .filter(
                    ProjectFile.project_id == cohort.id,
                    ProjectFile.category == "Source Code",
                )
                .all()
            )

            cohort_project_sloc = 0
            cohort_file_contents: Dict[str, Tuple[str, Optional[str], int]] = {}
            for pf in cohort_source_files:
                code = cls._read_file_safe(cohort_extract_dir, pf.relative_path)
                if code is not None:
                    lines_count = len([l for l in code.splitlines() if l.strip()])
                    cohort_project_sloc += lines_count
                    cohort_file_contents[pf.relative_path] = (code, pf.detected_language, lines_count)

            total_compared_files_count += len(cohort_file_contents)
            file_matches_list: List[Dict[str, Any]] = []

            # Compare file pairs
            for path_a, (code_a, lang_a, sloc_a) in current_file_contents.items():
                for path_b, (code_b, lang_b, sloc_b) in cohort_file_contents.items():
                    is_candidate, is_exact, reason = CandidateGenerator.prefilter_file_pair(
                        path_a, code_a, lang_a, path_b, code_b, lang_b
                    )
                    if not is_candidate:
                        continue

                    if is_exact:
                        token_sim = 100.0
                        struct_sim = 100.0
                        semantic_sim = 100.0 if settings.SIMILARITY_ENABLE_SEMANTIC else None
                        combined_sim, method_used = SimilarityScoringEngine.calculate_file_combined_score(
                            token_sim, struct_sim, semantic_sim
                        )
                        lines_a = code_a.splitlines()
                        file_matches_list.append({
                            "currentFile": path_a,
                            "matchedFile": path_b,
                            "currentLines": (1, max(1, len(lines_a))),
                            "matchedLines": (1, max(1, len(lines_a))),
                            "similarityPercent": 100.0,
                            "identicalStatements": len(lines_a),
                            "currentSnippet": "\n".join(lines_a[:12]),
                            "matchedSnippet": "\n".join(lines_a[:12]),
                            "tokenSimilarity": 100.0,
                            "structuralSimilarity": 100.0,
                            "semanticSimilarity": semantic_sim,
                            "comparisonMethod": "exact_sha256",
                            "currentSloc": sloc_a,
                            "matchedSloc": sloc_b,
                        })
                    else:
                        tok_res = CodeTokenizer.calculate_token_similarity(code_a, code_b, lang_a, lang_b)
                        str_res = StructuralSimilarityAnalyzer.calculate_structural_similarity(code_a, code_b, lang_a, lang_b)
                        sem_res = SemanticSimilarityService.calculate_semantic_similarity(code_a, code_b)

                        token_sim = tok_res["token_similarity"]
                        struct_sim = str_res["structural_similarity"]
                        semantic_sim = sem_res["semantic_similarity"]

                        combined_sim, method_used = SimilarityScoringEngine.calculate_file_combined_score(
                            token_sim, struct_sim, semantic_sim
                        )

                        if combined_sim is not None and combined_sim >= SimilarityScoringEngine.MIN_NOTABLE_MATCH_THRESHOLD:
                            file_matches_list.append({
                                "currentFile": path_a,
                                "matchedFile": path_b,
                                "currentLines": tok_res["current_lines"],
                                "matchedLines": tok_res["matched_lines"],
                                "similarityPercent": combined_sim,
                                "identicalStatements": tok_res["identical_statements"],
                                "currentSnippet": tok_res["current_snippet"],
                                "matchedSnippet": tok_res["matched_snippet"],
                                "tokenSimilarity": token_sim,
                                "structuralSimilarity": struct_sim,
                                "semanticSimilarity": semantic_sim,
                                "comparisonMethod": method_used,
                                "currentSloc": sloc_a,
                                "matchedSloc": sloc_b,
                            })

            # Sort file matches by similarity descending
            file_matches_list.sort(key=lambda m: m["similarityPercent"], reverse=True)

            # Aggregate project level score
            agg = SimilarityScoringEngine.aggregate_project_similarity(
                current_project_sloc, cohort_project_sloc, file_matches_list
            )

            cohort_matches_data.append({
                "matched_project_id": cohort.id,
                "matched_project_title": cohort.title or cohort.id,
                "overall_similarity": agg["overall_similarity"],
                "similarity_category": agg["similarity_category"],
                "token_similarity": agg["token_similarity"],
                "structural_similarity": agg["structural_similarity"],
                "semantic_similarity": agg["semantic_similarity"],
                "source_coverage_pct": agg["source_coverage_pct"],
                "matched_coverage_pct": agg["matched_coverage_pct"],
                "identical_statements_count": agg["identical_statements_count"],
                "matched_files_count": agg["matched_files_count"],
                "total_compared_files": len(cohort_file_contents),
                "strongest_file_matches": file_matches_list[:20],  # Keep top 20 matches
            })

        # Sort cohort matches by overall similarity descending
        cohort_matches_data.sort(key=lambda c: c["overall_similarity"], reverse=True)

        highest_score = cohort_matches_data[0]["overall_similarity"] if cohort_matches_data else 0.0
        strongest_project_id = cohort_matches_data[0]["matched_project_id"] if cohort_matches_data else None

        return cls._save_analysis_record(
            db=db,
            project_id=project_id,
            status="completed",
            compared_projects_count=len(cohort_projects),
            compared_files_count=total_compared_files_count,
            strongest_match_project_id=strongest_project_id,
            highest_similarity_score=highest_score,
            methods_used=methods_used,
            limitations=limitations,
            matches=cohort_matches_data,
        )

    @classmethod
    def _save_analysis_record(
        cls,
        db: Session,
        project_id: str,
        status: str,
        compared_projects_count: int,
        compared_files_count: int,
        strongest_match_project_id: Optional[str],
        highest_similarity_score: Optional[float],
        methods_used: List[str],
        limitations: List[str],
        matches: List[Dict[str, Any]],
    ) -> ProjectSimilarityAnalysis:
        """
        Atomically saves or updates the ProjectSimilarityAnalysis record and its matches.
        Guarantees idempotent persistence without duplicate rows.
        """
        # Look for existing record
        analysis = (
            db.query(ProjectSimilarityAnalysis)
            .filter(ProjectSimilarityAnalysis.project_id == project_id)
            .first()
        )

        if not analysis:
            analysis = ProjectSimilarityAnalysis(
                project_id=project_id,
                status=status,
                compared_projects_count=compared_projects_count,
                compared_files_count=compared_files_count,
                strongest_match_project_id=strongest_match_project_id,
                highest_similarity_score=highest_similarity_score,
                methods_used=methods_used,
                limitations=limitations,
                advisory_note=SimilarityScoringEngine.ADVISORY_NOTE,
                summary={
                    "total_matches_found": len(matches),
                    "highest_score": highest_similarity_score,
                },
            )
            db.add(analysis)
            db.flush()
        else:
            analysis.status = status
            analysis.compared_projects_count = compared_projects_count
            analysis.compared_files_count = compared_files_count
            analysis.strongest_match_project_id = strongest_match_project_id
            analysis.highest_similarity_score = highest_similarity_score
            analysis.methods_used = methods_used
            analysis.limitations = limitations
            analysis.advisory_note = SimilarityScoringEngine.ADVISORY_NOTE
            analysis.summary = {
                "total_matches_found": len(matches),
                "highest_score": highest_similarity_score,
            }

            # Delete previous match rows to avoid duplicates
            db.query(ProjectSimilarityMatch).filter(
                ProjectSimilarityMatch.analysis_id == analysis.id
            ).delete()
            db.flush()

        # Insert fresh match rows
        for m in matches:
            match_row = ProjectSimilarityMatch(
                analysis_id=analysis.id,
                project_id=project_id,
                matched_project_id=m["matched_project_id"],
                matched_project_title=m.get("matched_project_title"),
                overall_similarity=m.get("overall_similarity", 0.0),
                similarity_category=m.get("similarity_category", "minimal"),
                token_similarity=m.get("token_similarity"),
                structural_similarity=m.get("structural_similarity"),
                semantic_similarity=m.get("semantic_similarity"),
                source_coverage_pct=m.get("source_coverage_pct", 0.0),
                matched_coverage_pct=m.get("matched_coverage_pct", 0.0),
                identical_statements_count=m.get("identical_statements_count", 0),
                matched_files_count=m.get("matched_files_count", 0),
                total_compared_files=m.get("total_compared_files", 0),
                strongest_file_matches=m.get("strongest_file_matches", []),
            )
            db.add(match_row)

        db.commit()
        db.refresh(analysis)
        return analysis

    @classmethod
    def get_project_similarity(
        cls, db: Session, project_id: str
    ) -> Optional[ProjectSimilarityAnalysis]:
        """Fetch the most recent saved similarity analysis for the project."""
        return (
            db.query(ProjectSimilarityAnalysis)
            .filter(ProjectSimilarityAnalysis.project_id == project_id)
            .order_by(ProjectSimilarityAnalysis.created_at.desc())
            .first()
        )
