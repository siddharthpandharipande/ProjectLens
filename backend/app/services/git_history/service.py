"""
Git History Analysis Service — Phase 6 coordinator.

Orchestrates:
  1. Repository detection and validation (detector.py)
  2. Commit extraction (extractor.py)
  3. Timeline aggregation (timeline.py)
  4. Development signal generation (signals.py)
  5. Idempotent PostgreSQL persistence
"""
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from app.models.git_history import (
    ProjectGitHistoryAnalysis,
    ProjectCommitRecord,
    ProjectGitFinding,
)
from app.services.git_history.detector import GitRepositoryDetector
from app.services.git_history.extractor import GitCommitExtractor
from app.services.git_history.timeline import GitTimelineAggregator
from app.services.git_history.signals import generate_development_signals
from app.services.project_parser import ProjectParser


class GitHistoryService:
    """
    Public interface for Phase 6 Git development history analysis.
    """

    ANALYSIS_VERSION = "v1.0-git-analysis"
    MAX_COMMITS = 500  # Hard limit on commits inspected

    # ─── Query helpers ───────────────────────────────────────────────────────

    @classmethod
    def get_latest_analysis(
        cls, db: Session, project_id: str
    ) -> Optional[ProjectGitHistoryAnalysis]:
        return (
            db.query(ProjectGitHistoryAnalysis)
            .filter(ProjectGitHistoryAnalysis.project_id == project_id)
            .order_by(ProjectGitHistoryAnalysis.created_at.desc())
            .first()
        )

    # ─── Main analysis entry point ────────────────────────────────────────

    @classmethod
    def analyze_project_git_history(
        cls, db: Session, project_id: str
    ) -> ProjectGitHistoryAnalysis:
        """
        Runs full Git history analysis for a project.
        Idempotent: deletes previous analysis for this project and creates a fresh one.
        Returns the persisted ProjectGitHistoryAnalysis ORM object.
        """
        # 1. Get extract directory
        extract_dir = ProjectParser.get_project_extract_dir(project_id)

        # 2. Delete any existing analysis records for this project (idempotent)
        existing = cls.get_latest_analysis(db, project_id)
        if existing:
            db.delete(existing)
            db.flush()

        # 3. Detect repository
        status, availability, repo, is_shallow, error_msg = GitRepositoryDetector.detect_repository(
            extract_dir
        )

        # 4. Handle unavailable / empty / corrupt cases
        if availability in ("unavailable", "empty", "corrupt") or status != "completed":
            limitations = [error_msg] if error_msg else ["Git history is not available for this project."]
            if is_shallow:
                limitations.append("Repository is shallow — full history may not be available.")

            analysis = ProjectGitHistoryAnalysis(
                project_id=project_id,
                status=status,
                availability=availability,
                is_shallow=is_shallow,
                analysis_version=cls.ANALYSIS_VERSION,
                limitations=limitations,
                advisory_note=(
                    "No Git repository was found or could be read in this submission. "
                    "Git history analysis cannot be performed on archive submissions without .git metadata."
                ),
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            return analysis

        # 5. Extract commits
        commit_records, extraction_warnings = GitCommitExtractor.extract_commits(
            repo, max_commits=cls.MAX_COMMITS
        )

        # 6. Aggregate timeline
        aggregated = GitTimelineAggregator.aggregate_timeline(commit_records)

        # 7. Generate advisory signals
        findings_data = generate_development_signals(aggregated, commit_records)

        # 8. Build limitations list
        limitations: List[str] = []
        if is_shallow:
            limitations.append(
                "This repository is shallow. Only partial history is available — "
                "full commit timeline and statistics may be incomplete."
            )
        limitations.extend(extraction_warnings)
        limitations.append(
            "Git commit timestamps and author metadata can be altered by the committer. "
            "This analysis reflects recorded metadata only and cannot verify actual development timeline."
        )

        # 9. Persist analysis record
        analysis = ProjectGitHistoryAnalysis(
            project_id=project_id,
            status="completed",
            availability=availability,
            is_shallow=is_shallow,
            total_commits=aggregated["total_commits"],
            distinct_contributors_count=aggregated["distinct_contributors_count"],
            first_commit_at=aggregated["first_commit_at"],
            last_commit_at=aggregated["last_commit_at"],
            duration_days=aggregated["duration_days"],
            total_files_changed=aggregated["total_files_changed"],
            total_additions=aggregated["total_additions"],
            total_deletions=aggregated["total_deletions"],
            avg_time_between_commits_hours=aggregated["avg_time_between_commits_hours"],
            median_time_between_commits_hours=aggregated["median_time_between_commits_hours"],
            largest_commit_share_percent=aggregated["largest_commit_share_percent"],
            top_3_commit_share_percent=aggregated["top_3_commit_share_percent"],
            commit_activity_by_day=aggregated["activity_by_day"],
            commit_activity_by_weekday=aggregated["activity_by_weekday"],
            contributors_summary=aggregated["contributors"],
            commit_size_distribution=aggregated["size_distribution"],
            limitations=limitations,
            analysis_version=cls.ANALYSIS_VERSION,
        )
        db.add(analysis)
        db.flush()  # get analysis.id

        # 10. Persist commit records
        for cr in commit_records:
            record = ProjectCommitRecord(
                analysis_id=analysis.id,
                project_id=project_id,
                commit_hash=cr["commit_hash"],
                short_hash=cr["short_hash"],
                committed_at=cr["committed_at"],
                author_name=cr["author_name"],
                author_email=cr["author_email"],
                subject=cr["subject"],
                files_changed_count=cr["files_changed_count"],
                lines_added=cr["lines_added"],
                lines_deleted=cr["lines_deleted"],
                is_merge=cr["is_merge"],
                changed_files=cr["changed_files"],
            )
            db.add(record)

        # 11. Persist findings
        for fd in findings_data:
            finding = ProjectGitFinding(
                analysis_id=analysis.id,
                project_id=project_id,
                signal_id=fd["signal_id"],
                title=fd["title"],
                severity=fd["severity"],
                category=fd["category"],
                explanation=fd["explanation"],
                evidence=fd.get("evidence", {}),
                faculty_guidance=fd.get("faculty_guidance"),
            )
            db.add(finding)

        db.commit()
        db.refresh(analysis)
        return analysis
