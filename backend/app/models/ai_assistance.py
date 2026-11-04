from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
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


class ProjectAIAssistanceAnalysis(Base):
    """Project-level AI-Assistance analysis result (Phase 7A).

    Stores the deterministic evidence summary, advisory category, and the
    structured LLM interpretation (when LLM was used). No API keys, source
    code, or personal identifiers are stored.
    """

    __tablename__ = "project_ai_assistance_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_status = Column(String(32), nullable=False, default="completed")
    advisory_category = Column(String(96), nullable=False)
    evidence_summary = Column(JSON, nullable=False, default=list)
    rules_version = Column(String(32), nullable=False, default="v1.0-deterministic")
    llm_provider = Column(String(64), nullable=True)
    llm_model = Column(String(128), nullable=True)
    llm_interpretation_status = Column(String(32), nullable=True)
    structured_interpretation = Column(JSON, nullable=False, default=dict)
    limitations = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="ai_assistance_analyses")
    evidence_signals = relationship(
        "ProjectAIAssistanceEvidenceSignal",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectAIAssistanceEvidenceSignal.id",
    )

    __table_args__ = (
        Index("ix_ai_assistance_project_created", "project_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectAIAssistanceAnalysis(id={self.id}, "
            f"project='{self.project_id}', category='{self.advisory_category}')>"
        )


class ProjectAIAssistanceEvidenceSignal(Base):
    """Individual evidence signal recorded for an AI-Assistance analysis."""

    __tablename__ = "project_ai_assistance_evidence_signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    signal_id = Column(String(64), nullable=False)
    analysis_id = Column(
        Integer,
        ForeignKey("project_ai_assistance_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    signal_category = Column(String(64), nullable=False)
    evidence_source = Column(String(128), nullable=False)
    observed_value = Column(String(1024), nullable=False)
    explanation = Column(String(2048), nullable=False)
    confidence = Column(String(16), nullable=True)  # stored as string to preserve None
    alternative_explanations = Column(JSON, nullable=False, default=list)
    evidence_availability_status = Column(String(32), nullable=False, default="available")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectAIAssistanceAnalysis", back_populates="evidence_signals")

    __table_args__ = (
        Index("ix_ai_signal_analysis_category", "analysis_id", "signal_category"),
        Index("ix_ai_signal_analysis_signal_id", "analysis_id", "signal_id"),
    )

    def __repr__(self) -> str:
        return f"<ProjectAIAssistanceEvidenceSignal(id={self.id}, category='{self.signal_category}')>"
