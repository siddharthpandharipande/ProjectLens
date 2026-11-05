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
    Text,
)
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now() -> datetime:
    """Return current UTC datetime with timezone awareness."""
    return datetime.now(timezone.utc)


class ProjectEvaluation(Base):
    """Overall project evaluation consolidating all analysis modules (Final Phase)."""

    __tablename__ = "project_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    overall_score = Column(Float, nullable=True)
    grade = Column(String(8), nullable=True)
    evaluation_status = Column(String(32), nullable=False, default="incomplete")
    coverage_pct = Column(Float, nullable=False, default=0.0)
    
    category_scores = Column(JSON, nullable=False, default=list)
    strengths = Column(JSON, nullable=False, default=list)
    weaknesses = Column(JSON, nullable=False, default=list)
    risks = Column(JSON, nullable=False, default=list)
    recommendations = Column(JSON, nullable=False, default=list)
    module_statuses = Column(JSON, nullable=False, default=dict)
    
    executive_summary = Column(Text, nullable=True)
    faculty_notes = Column(Text, nullable=True)
    scoring_version = Column(String(32), nullable=False, default="v1.0-rubric")
    
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="evaluations")

    __table_args__ = (
        Index("ix_project_evaluations_project_created", "project_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectEvaluation(id={self.id}, project_id='{self.project_id}', "
            f"score={self.overall_score}, status='{self.evaluation_status}')>"
        )

