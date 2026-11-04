"""
service.py

Orchestration service for Code Quality analysis.
Extracts AST and Radon metrics, runs deterministic findings rules,
computes preliminary scores, and stores results cleanly in PostgreSQL.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.models.project import Project, ProjectFile
from app.models.code_quality import ProjectQualityAnalysis, ProjectFileMetric
from app.services.code_quality.analyzer import CodeQualityAnalyzer
from app.services.code_quality.rules import evaluate_quality_rules
from app.services.code_quality.scoring import DeterministicQualityScorer
from app.services.project_parser import ProjectParser


class CodeQualityService:
    """Service for running and retrieving Code Quality analysis."""

    @classmethod
    def analyze_project(cls, db: Session, project_id: str) -> ProjectQualityAnalysis:
        """
        Execute or refresh Code Quality analysis for an existing project.
        Safe re-analysis idempotent: updates existing records without duplicate rows.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project '{project_id}' not found.")

        # Ensure files are extracted & parsed
        if not project.files:
            if project.archive_path and Path(project.archive_path).exists():
                ProjectParser.extract_and_parse_project(db, project)
                db.refresh(project)
            else:
                raise ValueError(f"Project '{project_id}' has no archive or extracted files to analyze.")

        # Resolve extraction directory
        extracted_dir: Path
        if project.structure and project.structure.extracted_path:
            extracted_dir = Path(project.structure.extracted_path).resolve()
        else:
            extracted_dir = (Path(settings.EXTRACTED_DIR) / project.id).resolve()

        if not extracted_dir.exists():
            # If directory missing, try re-extracting
            ProjectParser.extract_and_parse_project(db, project)
            db.refresh(project)
            if project.structure and project.structure.extracted_path:
                extracted_dir = Path(project.structure.extracted_path).resolve()

        # Fetch all project files categorized as Source Code
        source_files = (
            db.query(ProjectFile)
            .filter(
                ProjectFile.project_id == project_id,
                ProjectFile.category == "Source Code",
            )
            .order_by(ProjectFile.relative_path)
            .all()
        )

        analyzed_file_metrics: List[Dict[str, Any]] = []

        for pf in source_files:
            file_on_disk = (extracted_dir / pf.relative_path).resolve()

            # Security sanity check: file must stay within project extracted dir
            try:
                file_on_disk.relative_to(extracted_dir)
            except ValueError:
                # Path traversal attempt or symlink escape
                continue

            metric = CodeQualityAnalyzer.analyze_file(
                file_path=file_on_disk,
                relative_path=pf.relative_path,
                language=pf.detected_language,
            )
            analyzed_file_metrics.append(metric)

        # ─── Aggregate Project-Level Metrics ──────────────────────────────────
        total_loc = sum(m.get("loc", 0) for m in analyzed_file_metrics)
        total_sloc = sum(m.get("sloc", 0) for m in analyzed_file_metrics)
        total_comments = sum(m.get("comments", 0) for m in analyzed_file_metrics)
        total_blank = sum(m.get("blank", 0) for m in analyzed_file_metrics)
        total_functions = sum(m.get("functions_count", 0) for m in analyzed_file_metrics)
        total_classes = sum(m.get("classes_count", 0) for m in analyzed_file_metrics)
        syntax_errors_count = sum(1 for m in analyzed_file_metrics if m.get("has_syntax_error"))

        # Complexity aggregations
        cc_values = [m["avg_complexity"] for m in analyzed_file_metrics if m.get("avg_complexity") is not None]
        avg_complexity = round(sum(cc_values) / len(cc_values), 1) if cc_values else None
        max_cc_values = [m["max_complexity"] for m in analyzed_file_metrics if m.get("max_complexity") is not None]
        max_complexity = max(max_cc_values) if max_cc_values else None

        # Maintainability Index aggregations
        mi_values = [m["maintainability_index"] for m in analyzed_file_metrics if m.get("maintainability_index") is not None]
        avg_mi = round(sum(mi_values) / len(mi_values), 1) if mi_values else None

        # Maintainability rating letter
        maintainability_rating = None
        if avg_mi is not None:
            if avg_mi >= 65.0:
                maintainability_rating = "A"
            elif avg_mi >= 40.0:
                maintainability_rating = "B"
            elif avg_mi >= 20.0:
                maintainability_rating = "C"
            else:
                maintainability_rating = "D"

        project_metrics = {
            "total_source_files": len(analyzed_file_metrics),
            "total_loc": total_loc,
            "total_sloc": total_sloc,
            "total_comments": total_comments,
            "total_blank": total_blank,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_complexity": avg_complexity,
            "max_complexity": max_complexity,
            "avg_maintainability_index": avg_mi,
            "maintainability_rating": maintainability_rating,
            "syntax_errors_count": syntax_errors_count,
        }

        # ─── Evaluate Quality Rules & Findings ────────────────────────────────
        findings = evaluate_quality_rules(analyzed_file_metrics, project_metrics)
        project_metrics["total_findings"] = len(findings)

        # ─── Compute Deterministic Score & Explanation ────────────────────────
        score, score_explanation = DeterministicQualityScorer.calculate_score(
            file_metrics=analyzed_file_metrics,
            project_metrics=project_metrics,
            findings=findings,
        )

        # ─── Build Explicit Language Coverage Matrix ──────────────────────────
        lang_groups: Dict[str, int] = {}
        for m in analyzed_file_metrics:
            lang = m.get("language") or "Other"
            lang_groups[lang] = lang_groups.get(lang, 0) + 1

        language_coverage: List[Dict[str, Any]] = []
        for lang, count in lang_groups.items():
            if lang == "Python":
                coverage_item = {
                    "language": "Python",
                    "file_count": count,
                    "supported_metrics": [
                        "AST Functions & Classes",
                        "AST Docstrings",
                        "Control Flow Nesting Depth",
                        "Import Analysis",
                        "Radon Physical & Source Lines",
                        "Radon Cyclomatic Complexity",
                        "Radon Maintainability Index",
                    ],
                    "limitations": "Full AST and Radon complexity/maintainability supported.",
                }
            elif lang in ("JavaScript", "TypeScript", "Java"):
                coverage_item = {
                    "language": lang,
                    "file_count": count,
                    "supported_metrics": [
                        "Tree-sitter Functions & Methods",
                        "Tree-sitter Classes & Interfaces",
                        "Tree-sitter Imports",
                        "Tree-sitter Syntax Validation",
                        "Source & Comment Line Counts",
                    ],
                    "limitations": (
                        "Structural AST supported via Tree-sitter. "
                        "Cyclomatic complexity and Maintainability Index are not calculated "
                        "for this language to avoid fabricated metrics."
                    ),
                }
            else:
                coverage_item = {
                    "language": lang,
                    "file_count": count,
                    "supported_metrics": [
                        "Source, Blank, and Comment Line Counts",
                        "Basic Import Directives",
                    ],
                    "limitations": (
                        "Basic physical metrics supported. "
                        "Deep AST, Cyclomatic Complexity, and Maintainability calculations "
                        "are currently unsupported for this language."
                    ),
                }
            language_coverage.append(coverage_item)

        # ─── Persist to PostgreSQL (Idempotent update/replace) ─────────────────
        # Find or create ProjectQualityAnalysis
        existing_analysis = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .first()
        )

        if not existing_analysis:
            existing_analysis = ProjectQualityAnalysis(
                project_id=project_id,
                status="completed",
                score=score,
                score_explanation=score_explanation,
                metrics_summary=project_metrics,
                findings=findings,
                language_coverage=language_coverage,
                rules_version="v1.0-deterministic",
            )
            db.add(existing_analysis)
            db.flush()
        else:
            existing_analysis.status = "completed"
            existing_analysis.score = score
            existing_analysis.score_explanation = score_explanation
            existing_analysis.metrics_summary = project_metrics
            existing_analysis.findings = findings
            existing_analysis.language_coverage = language_coverage
            existing_analysis.rules_version = "v1.0-deterministic"
            # Delete old file metrics to prevent duplicates
            db.query(ProjectFileMetric).filter(
                ProjectFileMetric.quality_analysis_id == existing_analysis.id
            ).delete()
            db.flush()

        # Insert new file metrics
        file_metric_records = []
        for m in analyzed_file_metrics:
            fm = ProjectFileMetric(
                quality_analysis_id=existing_analysis.id,
                project_id=project_id,
                relative_path=m["relative_path"],
                language=m.get("language"),
                loc=m.get("loc", 0),
                sloc=m.get("sloc", 0),
                comments=m.get("comments", 0),
                blank=m.get("blank", 0),
                functions_count=m.get("functions_count", 0),
                classes_count=m.get("classes_count", 0),
                function_names=m.get("function_names", []),
                class_names=m.get("class_names", []),
                imports=m.get("imports", []),
                max_nesting_depth=m.get("max_nesting_depth"),
                avg_complexity=m.get("avg_complexity"),
                max_complexity=m.get("max_complexity"),
                maintainability_index=m.get("maintainability_index"),
                has_syntax_error=m.get("has_syntax_error", False),
                syntax_error_details=m.get("syntax_error_details"),
            )
            file_metric_records.append(fm)

        db.add_all(file_metric_records)

        # Update project stage
        project.processing_stage = "Code quality analyzed"
        db.commit()
        db.refresh(existing_analysis)

        return existing_analysis

    @classmethod
    def get_project_quality(cls, db: Session, project_id: str) -> Optional[ProjectQualityAnalysis]:
        """Retrieve the most recent saved code-quality analysis for a project."""
        return (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .first()
        )
