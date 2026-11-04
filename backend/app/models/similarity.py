from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    JSON,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class ProjectSimilarityAnalysis(Base):
    """
    ProjectSimilarityAnalysis table stores the project-level similarity evaluation
    executed against existing cohort submissions in PostgreSQL.
    """
    __tablename__ = "project_similarity_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False, default="completed")
    compared_projects_count = Column(Integer, nullable=False, default=0)
    compared_files_count = Column(Integer, nullable=False, default=0)
    strongest_match_project_id = Column(String(64), nullable=True)
    highest_similarity_score = Column(Float, nullable=True)
    scoring_version = Column(String(64), nullable=False, default="v1.0-hierarchical-ast-tokens")
    methods_used = Column(JSON, nullable=False, default=list)
    limitations = Column(JSON, nullable=False, default=list)
    advisory_note = Column(
        String(512),
        nullable=False,
        default="Advisory evidence only. Similarity signals do not constitute proof of academic misconduct.",
    )
    summary = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="similarity_analyses", foreign_keys=[project_id])
    matches = relationship(
        "ProjectSimilarityMatch",
        back_populates="similarity_analysis",
        cascade="all, delete-orphan",
        order_by="desc(ProjectSimilarityMatch.overall_similarity)",
    )

    def __repr__(self) -> str:
        return f"<ProjectSimilarityAnalysis(id={self.id}, project='{self.project_id}', highest_score={self.highest_similarity_score})>"


class ProjectSimilarityMatch(Base):
    """
    ProjectSimilarityMatch table stores project-to-project comparison evidence
    and file-level similarity matches.
    """
    __tablename__ = "project_similarity_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_similarity_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    matched_project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    matched_project_title = Column(String(255), nullable=True)

    # Similarity Scores (0 - 100)
    overall_similarity = Column(Float, nullable=False, default=0.0)
    similarity_category = Column(String(32), nullable=False, default="minimal")  # high, moderate, low, minimal
    token_similarity = Column(Float, nullable=True)
    structural_similarity = Column(Float, nullable=True)
    semantic_similarity = Column(Float, nullable=True)

    # Coverage metrics
    source_coverage_pct = Column(Float, nullable=False, default=0.0)
    matched_coverage_pct = Column(Float, nullable=False, default=0.0)
    identical_statements_count = Column(Integer, nullable=False, default=0)
    matched_files_count = Column(Integer, nullable=False, default=0)
    total_compared_files = Column(Integer, nullable=False, default=0)

    # Structured file-to-file matches (JSON list)
    strongest_file_matches = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    similarity_analysis = relationship("ProjectSimilarityAnalysis", back_populates="matches")
    matched_project = relationship("Project", foreign_keys=[matched_project_id])

    __table_args__ = (
        UniqueConstraint("analysis_id", "matched_project_id", name="uq_similarity_analysis_match"),
        Index("ix_project_similarity_score", "analysis_id", "overall_similarity"),
    )

    def __repr__(self) -> str:
        return f"<ProjectSimilarityMatch(analysis={self.analysis_id}, matched='{self.matched_project_id}', score={self.overall_similarity})>"
