from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class ProjectGitHistoryAnalysis(Base):
    __tablename__ = "project_git_history_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False, default="completed")
    availability = Column(String(32), nullable=False, default="available")  # available, unavailable, empty, corrupt
    is_shallow = Column(Boolean, nullable=False, default=False)
    total_commits = Column(Integer, nullable=False, default=0)
    distinct_contributors_count = Column(Integer, nullable=False, default=0)
    first_commit_at = Column(DateTime(timezone=True), nullable=True)
    last_commit_at = Column(DateTime(timezone=True), nullable=True)
    duration_days = Column(Float, nullable=False, default=0.0)
    total_files_changed = Column(Integer, nullable=False, default=0)
    total_additions = Column(Integer, nullable=False, default=0)
    total_deletions = Column(Integer, nullable=False, default=0)
    avg_time_between_commits_hours = Column(Float, nullable=True)
    median_time_between_commits_hours = Column(Float, nullable=True)
    largest_commit_share_percent = Column(Float, nullable=True)
    top_3_commit_share_percent = Column(Float, nullable=True)
    commit_activity_by_day = Column(JSON, nullable=False, default=dict)
    commit_activity_by_weekday = Column(JSON, nullable=False, default=dict)
    contributors_summary = Column(JSON, nullable=False, default=list)
    commit_size_distribution = Column(JSON, nullable=False, default=dict)
    advisory_note = Column(
        String(1024),
        nullable=False,
        default=(
            "Advisory development cadence and commit velocity findings. "
            "Git metadata reflects repository history as committed and cannot independently prove work authorship or timing."
        ),
    )
    limitations = Column(JSON, nullable=False, default=list)
    analysis_version = Column(String(32), nullable=False, default="v1.0-git-analysis")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="git_history_analyses")
    commits = relationship(
        "ProjectCommitRecord",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectCommitRecord.committed_at.desc()",
    )
    findings = relationship(
        "ProjectGitFinding",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectGitFinding.id",
    )

    def __repr__(self) -> str:
        return f"<ProjectGitHistoryAnalysis(id={self.id}, project='{self.project_id}', commits={self.total_commits})>"


class ProjectCommitRecord(Base):
    __tablename__ = "project_commit_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_git_history_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    commit_hash = Column(String(64), nullable=False)
    short_hash = Column(String(16), nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=False)
    author_name = Column(String(255), nullable=False, default="Unknown")
    author_email = Column(String(255), nullable=False, default="")
    subject = Column(String(512), nullable=False, default="")
    files_changed_count = Column(Integer, nullable=False, default=0)
    lines_added = Column(Integer, nullable=False, default=0)
    lines_deleted = Column(Integer, nullable=False, default=0)
    is_merge = Column(Boolean, nullable=False, default=False)
    changed_files = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectGitHistoryAnalysis", back_populates="commits")

    __table_args__ = (
        Index("ix_commit_records_analysis_hash", "analysis_id", "commit_hash"),
        Index("ix_commit_records_analysis_date", "analysis_id", "committed_at"),
    )

    def __repr__(self) -> str:
        return f"<ProjectCommitRecord(hash='{self.short_hash}', author='{self.author_name}', date='{self.committed_at}')>"


class ProjectGitFinding(Base):
    __tablename__ = "project_git_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_git_history_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    signal_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(32), nullable=False)  # high, medium, low, advisory, info
    category = Column(String(64), nullable=False)  # commit_concentration, timestamp_anomaly, history_duration, dormancy_gap, contributor_distribution
    explanation = Column(String(1024), nullable=False)
    evidence = Column(JSON, nullable=False, default=dict)
    faculty_guidance = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectGitHistoryAnalysis", back_populates="findings")

    __table_args__ = (
        Index("ix_git_findings_category_severity", "analysis_id", "category", "severity"),
    )

    def __repr__(self) -> str:
        return f"<ProjectGitFinding(id={self.id}, signal='{self.signal_id}', severity='{self.severity}')>"
