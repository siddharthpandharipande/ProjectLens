"""Deterministic evidence collection for Phase 7A AI-Assistance Analyzer.

Reads saved results from Phases 3-6 (code quality, similarity, documentation,
git history) and normalises them into evidence signals. Never assumes every
analysis has completed; missing results are recorded as "unavailable" rather
than fabricated. No source code, personal identifiers, or secrets are included.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.code_quality import ProjectQualityAnalysis, ProjectFileMetric
from app.models.similarity import ProjectSimilarityAnalysis, ProjectSimilarityMatch
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentationFinding,
)
from app.models.git_history import ProjectGitHistoryAnalysis


def _signal(
    signal_id: str,
    category: str,
    source: str,
    observed_value: str,
    explanation: str,
    *,
    confidence: Optional[float] = None,
    alternative_explanations: Optional[List[str]] = None,
    availability_status: str = "available",
) -> Dict[str, Any]:
    """Build a normalised evidence signal dict."""
    return {
        "signal_id": signal_id,
        "category": category,
        "source": source,
        "observed_value": observed_value,
        "explanation": explanation,
        "confidence": confidence,
        "alternative_explanations": alternative_explanations or [],
        "availability_status": availability_status,
    }


def _unavailable_signal(
    signal_id: str,
    category: str,
    source: str,
    reason: str,
) -> Dict[str, Any]:
    """Build a signal recording that a data source is unavailable."""
    return _signal(
        signal_id=signal_id,
        category=category,
        source=source,
        observed_value="unavailable",
        explanation=reason,
        confidence=None,
        alternative_explanations=[
            "The upstream analysis has not been run for this project.",
            "Results may become available after running the corresponding analysis.",
        ],
        availability_status="unavailable",
    )


def _finding_value(finding: Any, field: str, default: Any = "") -> Any:
    """Read a documentation finding from either an ORM row or a test dict."""
    if isinstance(finding, dict):
        return finding.get(field, default)
    return getattr(finding, field, default)


class EvidenceCollector:
    """Collects and normalises real evidence from saved Phase 3-6 analyses."""

    @classmethod
    def collect_all(cls, db: Session, project_id: str) -> List[Dict[str, Any]]:
        """Collect all available evidence signals for a project."""
        signals: List[Dict[str, Any]] = []
        signals.extend(cls.collect_code_quality(db, project_id))
        signals.extend(cls.collect_similarity(db, project_id))
        signals.extend(cls.collect_documentation(db, project_id))
        signals.extend(cls.collect_git_history(db, project_id))
        return signals

    # ------------------------------------------------------------------
    # Phase 3: Code Quality
    # ------------------------------------------------------------------

    @classmethod
    def collect_code_quality(
        cls, db: Session, project_id: str
    ) -> List[Dict[str, Any]]:
        """Collect code-quality evidence signals."""
        signals: List[Dict[str, Any]] = []
        analysis = (
            db.query(ProjectQualityAnalysis)
            .filter(ProjectQualityAnalysis.project_id == project_id)
            .order_by(ProjectQualityAnalysis.created_at.desc())
            .first()
        )
        if not analysis:
            signals.append(
                _unavailable_signal(
                    signal_id="cq-missing",
                    category="code_quality",
                    source="project_quality_analyses",
                    reason="No code quality analysis has been run for this project.",
                )
            )
            return signals

        metrics: Dict[str, Any] = analysis.metrics_summary or {}
        findings: List[Dict[str, Any]] = analysis.findings or []

        total_source_files = int(metrics.get("total_source_files", 0) or 0)
        total_functions = int(metrics.get("total_functions", 0) or 0)
        total_classes = int(metrics.get("total_classes", 0) or 0)
        avg_complexity = metrics.get("avg_complexity")
        max_complexity = metrics.get("max_complexity")
        maintainability = metrics.get("maintainability_rating")

        signals.append(
            _signal(
                signal_id="cq-source-files",
                category="code_quality",
                source="project_quality_analyses.metrics_summary",
                observed_value=str(total_source_files),
                explanation="Total source files analysed in the code-quality step.",
                confidence=1.0 if total_source_files > 0 else None,
                availability_status="available",
            )
        )
        signals.append(
            _signal(
                signal_id="cq-functions-classes",
                category="code_quality",
                source="project_quality_analyses.metrics_summary",
                observed_value=f"{total_functions} functions, {total_classes} classes",
                explanation="Aggregate function and class counts across source files.",
                confidence=1.0,
                availability_status="available",
            )
        )
        if avg_complexity is not None:
            signals.append(
                _signal(
                    signal_id="cq-complexity",
                    category="code_quality",
                    source="project_quality_analyses.metrics_summary",
                    observed_value=f"average cyclomatic complexity {avg_complexity}",
                    explanation="Average cyclomatic complexity indicates control-flow complexity.",
                    confidence=0.8,
                    alternative_explanations=[
                        "Standard algorithms can legitimately have higher complexity.",
                        "Complexity alone does not indicate AI-generated code.",
                    ],
                    availability_status="available",
                )
            )
        else:
            signals.append(
                _unavailable_signal(
                    signal_id="cq-complexity",
                    category="code_quality",
                    source="project_quality_analyses.metrics_summary",
                    reason="Average complexity metric is not recorded.",
                )
            )
        if max_complexity is not None:
            signals.append(
                _signal(
                    signal_id="cq-max-complexity",
                    category="code_quality",
                    source="project_quality_analyses.metrics_summary",
                    observed_value=f"maximum cyclomatic complexity {max_complexity}",
                    explanation="Highest single-function cyclomatic complexity observed.",
                    confidence=0.8,
                    availability_status="available",
                )
            )
        if maintainability:
            signals.append(
                _signal(
                    signal_id="cq-maintainability",
                    category="code_quality",
                    source="project_quality_analyses.metrics_summary",
                    observed_value=f"maintainability rating {maintainability}",
                    explanation="Preliminary maintainability rating from Radon metrics.",
                    confidence=0.7,
                    availability_status="available",
                )
            )
        syntax_errors = int(metrics.get("syntax_errors_count", 0) or 0)
        total_findings = int(metrics.get("total_findings", 0) or 0)
        signals.append(
            _signal(
                signal_id="cq-syntax-errors",
                category="code_quality",
                source="project_quality_analyses.metrics_summary",
                observed_value=f"{syntax_errors} syntax error(s)",
                explanation="Count of files with detected syntax errors.",
                confidence=1.0,
                alternative_explanations=[
                    "Syntax errors may reflect incomplete snippets rather than AI authorship.",
                ],
                availability_status="available",
            )
        )
        signals.append(
            _signal(
                signal_id="cq-findings",
                category="code_quality",
                source="project_quality_analyses.findings",
                observed_value=f"{total_findings} quality finding(s)",
                explanation="Deterministic quality findings generated by rule evaluation.",
                confidence=0.9,
                availability_status="available",
            )
        )
        # High-severity findings as individual signals for traceability.
        high_findings = [
            f for f in findings if str(f.get("severity", "")).lower() in ("high", "critical")
        ]
        for idx, f in enumerate(high_findings[:5]):
            signals.append(
                _signal(
                    signal_id=f"cq-finding-{idx}",
                    category="code_quality_finding",
                    source="project_quality_analyses.findings",
                    observed_value=str(f.get("rule_id", "")) + ": " + str(f.get("explanation", "")),
                    explanation=f"High-severity finding in {f.get('file_path', 'unknown file')}.",
                    confidence=0.85,
                    availability_status="available",
                )
            )
        return signals

    # ------------------------------------------------------------------
    # Phase 4: Similarity
    # ------------------------------------------------------------------

    @classmethod
    def collect_similarity(
        cls, db: Session, project_id: str
    ) -> List[Dict[str, Any]]:
        """Collect code-similarity evidence signals."""
        signals: List[Dict[str, Any]] = []
        analysis = (
            db.query(ProjectSimilarityAnalysis)
            .filter(ProjectSimilarityAnalysis.project_id == project_id)
            .order_by(ProjectSimilarityAnalysis.created_at.desc())
            .first()
        )
        if not analysis:
            signals.append(
                _unavailable_signal(
                    signal_id="sim-missing",
                    category="similarity",
                    source="project_similarity_analyses",
                    reason="No code similarity analysis has been run for this project.",
                )
            )
            return signals

        compared_projects = int(analysis.compared_projects_count or 0)
        highest_score = analysis.highest_similarity_score
        sim_summary = analysis.summary or {}
        sim_category = getattr(analysis, "similarity_category", None) or sim_summary.get("similarity_category") or "minimal"
        methods = analysis.methods_used or []
        limitations = analysis.limitations or []

        signals.append(
            _signal(
                signal_id="sim-compared-projects",
                category="similarity",
                source="project_similarity_analyses",
                observed_value=f"{compared_projects} comparable project(s)",
                explanation="Number of eligible cohort projects compared against this submission.",
                confidence=1.0,
                availability_status="available",
            )
        )
        if highest_score is not None:
            signals.append(
                _signal(
                    signal_id="sim-highest-score",
                    category="similarity",
                    source="project_similarity_analyses",
                    observed_value=f"highest similarity {highest_score:.1f}%",
                    explanation="Highest similarity signal across all cohort comparisons.",
                    confidence=0.8,
                    alternative_explanations=[
                        "Shared boilerplate, common educational templates, and standard "
                        "algorithms can produce similarity without copying.",
                        "Similarity is an advisory signal, not proof of misconduct.",
                    ],
                    availability_status="available",
                )
            )
        else:
            signals.append(
                _unavailable_signal(
                    signal_id="sim-highest-score",
                    category="similarity",
                    source="project_similarity_analyses",
                    reason="No similarity score was recorded.",
                )
            )
        signals.append(
            _signal(
                signal_id="sim-category",
                category="similarity",
                source="project_similarity_analyses",
                observed_value=f"similarity category '{sim_category}'",
                explanation="Advisory categorisation of the strongest similarity signal.",
                confidence=0.7,
                availability_status="available",
            )
        )
        signals.append(
            _signal(
                signal_id="sim-methods",
                category="similarity",
                source="project_similarity_analyses",
                observed_value=", ".join(methods) if methods else "none",
                explanation="Comparison methods applied (token, structural, semantic).",
                confidence=0.9,
                availability_status="available",
            )
        )
        strongest_match = (
            db.query(ProjectSimilarityMatch)
            .filter(ProjectSimilarityMatch.project_id == project_id)
            .order_by(ProjectSimilarityMatch.overall_similarity.desc())
            .first()
        )
        if strongest_match and strongest_match.overall_similarity is not None:
            matched_project = strongest_match.matched_project_id or "unknown"
            signals.append(
                _signal(
                    signal_id="sim-strongest-match",
                    category="similarity_match",
                    source="project_similarity_matches",
                    observed_value=f"strongest match with project {matched_project} "
                    f"({strongest_match.overall_similarity:.1f}%)",
                    explanation="Top project-to-project similarity match with file-level evidence.",
                    confidence=0.75,
                    alternative_explanations=[
                        "Common starter code or assignment templates may explain shared structure.",
                    ],
                    availability_status="available",
                )
            )
        if limitations:
            signals.append(
                _signal(
                    signal_id="sim-limitations",
                    category="similarity",
                    source="project_similarity_analyses",
                    observed_value="; ".join(limitations[:5]),
                    explanation="Recorded limitations of the similarity analysis.",
                    confidence=0.9,
                    availability_status="available",
                )
            )
        return signals

    # ------------------------------------------------------------------
    # Phase 5: Documentation
    # ------------------------------------------------------------------

    @classmethod
    def collect_documentation(
        cls, db: Session, project_id: str
    ) -> List[Dict[str, Any]]:
        """Collect documentation and consistency evidence signals."""
        signals: List[Dict[str, Any]] = []
        analysis = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )
        if not analysis:
            signals.append(
                _unavailable_signal(
                    signal_id="doc-missing",
                    category="documentation",
                    source="project_documentation_analyses",
                    reason="No documentation analysis has been run for this project.",
                )
            )
            return signals

        metrics: Dict[str, Any] = analysis.metrics_summary or {}
        findings: List[Dict[str, Any]] = analysis.findings or []
        total_documents = int(analysis.total_documents_count or 0)
        total_words = int(analysis.total_words_count or 0)
        recognized_sections = int(analysis.recognized_sections_count or 0)
        preliminary_score = analysis.preliminary_score

        signals.append(
            _signal(
                signal_id="doc-total-documents",
                category="documentation",
                source="project_documentation_analyses",
                observed_value=f"{total_documents} document(s)",
                explanation="Total documentation documents discovered and extracted.",
                confidence=1.0,
                availability_status="available",
            )
        )
        signals.append(
            _signal(
                signal_id="doc-total-words",
                category="documentation",
                source="project_documentation_analyses",
                observed_value=f"{total_words} word(s)",
                explanation="Total extracted words across documentation.",
                confidence=1.0,
                availability_status="available",
            )
        )
        signals.append(
            _signal(
                signal_id="doc-recognized-sections",
                category="documentation",
                source="project_documentation_analyses",
                observed_value=f"{recognized_sections} recognized section(s)",
                explanation="Count of recognised documentation sections (e.g. README, setup, testing).",
                confidence=0.8,
                availability_status="available",
            )
        )
        if preliminary_score is not None:
            signals.append(
                _signal(
                    signal_id="doc-preliminary-score",
                    category="documentation",
                    source="project_documentation_analyses",
                    observed_value=f"preliminary documentation score {preliminary_score}",
                    explanation="Preliminary documentation quality rubric score (advisory only).",
                    confidence=0.7,
                    availability_status="available",
                )
            )
        # Technology consistency findings.
        tech_findings = [
            f for f in findings if _finding_value(f, "category") == "technology_consistency"
        ]
        for idx, f in enumerate(tech_findings[:5]):
            signals.append(
                _signal(
                    signal_id=f"doc-tech-{idx}",
                    category="documentation_finding",
                    source="project_documentation_findings",
                    observed_value=f"{_finding_value(f, 'rule_id')}: {_finding_value(f, 'verification_status')}",
                    explanation=f"{_finding_value(f, 'title')} — {_finding_value(f, 'explanation')}",
                    confidence=0.8,
                    alternative_explanations=[
                        "Documentation may be outdated relative to the current codebase.",
                    ],
                    availability_status="available",
                )
            )
        # Implementation / numerical claim findings.
        claim_findings = [
            f
            for f in findings
            if _finding_value(f, "category") in ("implementation_claim", "numerical_claim")
        ]
        for idx, f in enumerate(claim_findings[:5]):
            signals.append(
                _signal(
                    signal_id=f"doc-claim-{idx}",
                    category="documentation_finding",
                    source="project_documentation_findings",
                    observed_value=f"{_finding_value(f, 'verification_status')}",
                    explanation=f"Claim '{_finding_value(f, 'documented_claim')}' verification: "
                    f"{_finding_value(f, 'verification_status')}.",
                    confidence=0.75,
                    alternative_explanations=[
                        "Claims may be aspirational or based on planned rather than implemented work.",
                    ],
                    availability_status="available",
                )
            )
        return signals

    # ------------------------------------------------------------------
    # Phase 6: Git History
    # ------------------------------------------------------------------

    @classmethod
    def collect_git_history(
        cls, db: Session, project_id: str
    ) -> List[Dict[str, Any]]:
        """Collect git development-history evidence signals."""
        signals: List[Dict[str, Any]] = []
        analysis = (
            db.query(ProjectGitHistoryAnalysis)
            .filter(ProjectGitHistoryAnalysis.project_id == project_id)
            .order_by(ProjectGitHistoryAnalysis.created_at.desc())
            .first()
        )
        if not analysis:
            signals.append(
                _unavailable_signal(
                    signal_id="git-missing",
                    category="git_history",
                    source="project_git_history_analyses",
                    reason="No git history analysis has been run for this project.",
                )
            )
            return signals

        availability = analysis.availability or "unavailable"
        total_commits = int(analysis.total_commits or 0)
        duration_days = float(analysis.duration_days or 0.0)
        largest_share = analysis.largest_commit_share_percent
        top3_share = analysis.top_3_commit_share_percent
        is_shallow = bool(analysis.is_shallow)
        contributors = int(analysis.distinct_contributors_count or 0)

        signals.append(
            _signal(
                signal_id="git-availability",
                category="git_history",
                source="project_git_history_analyses",
                observed_value=f"availability '{availability}'",
                explanation="Whether readable Git metadata exists for this submission.",
                confidence=1.0,
                availability_status="available",
            )
        )
        if availability == "available":
            signals.append(
                _signal(
                    signal_id="git-total-commits",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=f"{total_commits} commit(s)",
                    explanation="Total number of commits inspected.",
                    confidence=0.9,
                    alternative_explanations=[
                        "A small commit count may result from squashed commits or a single upload.",
                        "Commit count does not measure effort or authorship.",
                    ],
                    availability_status="available",
                )
            )
            signals.append(
                _signal(
                    signal_id="git-duration",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=f"{duration_days:.1f} day(s) of recorded history",
                    explanation="Recorded development duration between first and last commit.",
                    confidence=0.8,
                    alternative_explanations=[
                        "Timestamps can be amended by the committer; they reflect recorded metadata only.",
                    ],
                    availability_status="available",
                )
            )
            signals.append(
                _signal(
                    signal_id="git-concentration",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=(
                        f"largest commit share {largest_share:.1f}%, top-3 share {top3_share:.1f}%"
                        if largest_share is not None
                        else "concentration not recorded"
                    ),
                    explanation="Commit concentration indicates how much change is in few large commits.",
                    confidence=0.75,
                    alternative_explanations=[
                        "Large initial imports or squashed histories concentrate changes naturally.",
                    ],
                    availability_status="available",
                )
            )
            signals.append(
                _signal(
                    signal_id="git-contributors",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=f"{contributors} distinct contributor(s)",
                    explanation="Number of distinct contributors recorded in commit metadata.",
                    confidence=0.85,
                    availability_status="available",
                )
            )
            if is_shallow:
                signals.append(
                    _signal(
                        signal_id="git-shallow",
                        category="git_history",
                        source="project_git_history_analyses",
                        observed_value="repository is shallow",
                        explanation="Only partial history is available; full timeline may be incomplete.",
                        confidence=0.9,
                        availability_status="limited",
                    )
                )
        else:
            signals.append(
                _signal(
                    signal_id="git-unavailable",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=f"availability '{availability}'",
                    explanation="Git metadata is not available or not readable.",
                    confidence=0.9,
                    alternative_explanations=[
                        "Archive submissions without a .git directory have no recorded history.",
                    ],
                    availability_status="unavailable",
                )
            )
        for limitation in (analysis.limitations or [])[:5]:
            signals.append(
                _signal(
                    signal_id="git-limitation",
                    category="git_history",
                    source="project_git_history_analyses",
                    observed_value=limitation,
                    explanation="Recorded git-analysis limitation.",
                    confidence=0.9,
                    availability_status="available",
                )
            )
        return signals
