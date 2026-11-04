from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Boolean,
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


class ProjectQualityAnalysis(Base):
    __tablename__ = "project_quality_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False, default="completed")
    score = Column(Float, nullable=True)
    score_explanation = Column(JSON, nullable=False, default=dict)
    metrics_summary = Column(JSON, nullable=False, default=dict)
    findings = Column(JSON, nullable=False, default=list)
    language_coverage = Column(JSON, nullable=False, default=dict)
    rules_version = Column(String(32), nullable=False, default="v1.0-deterministic")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="quality_analyses")
    file_metrics = relationship(
        "ProjectFileMetric",
        back_populates="quality_analysis",
        cascade="all, delete-orphan",
        order_by="ProjectFileMetric.relative_path",
    )

    def __repr__(self) -> str:
        return f"<ProjectQualityAnalysis(id={self.id}, project='{self.project_id}', score={self.score})>"


class ProjectFileMetric(Base):
    __tablename__ = "project_file_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quality_analysis_id = Column(
        Integer,
        ForeignKey("project_quality_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    relative_path = Column(String(512), nullable=False)
    language = Column(String(64), nullable=True)

    # Line metrics
    loc = Column(Integer, nullable=False, default=0)
    sloc = Column(Integer, nullable=False, default=0)
    comments = Column(Integer, nullable=False, default=0)
    blank = Column(Integer, nullable=False, default=0)

    # AST structural metrics
    functions_count = Column(Integer, nullable=False, default=0)
    classes_count = Column(Integer, nullable=False, default=0)
    function_names = Column(JSON, nullable=False, default=list)
    class_names = Column(JSON, nullable=False, default=list)
    imports = Column(JSON, nullable=False, default=list)
    max_nesting_depth = Column(Integer, nullable=True)

    # Complexity & Maintainability (Radon / language-specific)
    avg_complexity = Column(Float, nullable=True)
    max_complexity = Column(Integer, nullable=True)
    maintainability_index = Column(Float, nullable=True)

    # Parse / syntax status
    has_syntax_error = Column(Boolean, nullable=False, default=False)
    syntax_error_details = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    quality_analysis = relationship("ProjectQualityAnalysis", back_populates="file_metrics")

    __table_args__ = (
        UniqueConstraint("quality_analysis_id", "relative_path", name="uq_quality_file_metric_path"),
        Index("ix_file_metric_project_lang", "project_id", "language"),
    )

    def __repr__(self) -> str:
        return f"<ProjectFileMetric(project='{self.project_id}', path='{self.relative_path}', sloc={self.sloc})>"
