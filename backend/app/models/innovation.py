from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
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


class ProjectInnovationAnalysis(Base):
    """Project-level Innovation and Distinctiveness analysis result (Phase 7B).

    Stores the extracted project profile, cohort comparison matches,
    transparent dimension-wise distinctiveness scores, and optional
    structured LLM interpretation.
    """

    __tablename__ = "project_innovation_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_status = Column(String(32), nullable=False, default="completed")
    advisory_category = Column(String(96), nullable=False)
    project_profile = Column(JSON, nullable=False, default=dict)
    cohort_size = Column(Integer, nullable=False, default=0)
    comparison_method = Column(String(64), nullable=False, default="tfidf_cosine")
    dimension_scores = Column(JSON, nullable=False, default=dict)
    limitations = Column(JSON, nullable=False, default=list)
    rules_version = Column(String(32), nullable=False, default="v1.0-deterministic-rubric")
    llm_provider = Column(String(64), nullable=True)
    llm_model = Column(String(128), nullable=True)
    llm_interpretation_status = Column(String(32), nullable=True)
    structured_interpretation = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="innovation_analyses")
    matches = relationship(
        "ProjectInnovationMatch",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectInnovationMatch.overall_similarity.desc()",
    )

    __table_args__ = (
        Index("ix_innovation_project_created", "project_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectInnovationAnalysis(id={self.id}, "
            f"project='{self.project_id}', category='{self.advisory_category}')>"
        )


class ProjectInnovationMatch(Base):
    """Individual cohort project comparison record for an innovation analysis."""

    __tablename__ = "project_innovation_matches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_innovation_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    compared_project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_similarity = Column(Float, nullable=False, default=0.0)
    solution_similarity = Column(Float, nullable=False, default=0.0)
    feature_similarity = Column(Float, nullable=False, default=0.0)
    technology_overlap = Column(Float, nullable=False, default=0.0)
    technical_approach_similarity = Column(Float, nullable=False, default=0.0)
    overall_similarity = Column(Float, nullable=False, default=0.0)
    difference_summary = Column(String(1000), nullable=True)
    evidence_references = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectInnovationAnalysis", back_populates="matches")
    compared_project = relationship("Project", foreign_keys=[compared_project_id])

    __table_args__ = (
        Index("ix_innovation_matches_analysis_sim", "analysis_id", "overall_similarity"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectInnovationMatch(id={self.id}, project='{self.project_id}', "
            f"compared='{self.compared_project_id}', sim={self.overall_similarity})>"
        )

