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


class ProjectDocumentationAnalysis(Base):
    __tablename__ = "project_documentation_analyses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(String(32), nullable=False, default="completed")
    preliminary_score = Column(Float, nullable=True)
    scoring_version = Column(String(32), nullable=False, default="v1.0-deterministic-rubric")
    factors_explanation = Column(JSON, nullable=False, default=dict)
    metrics_summary = Column(JSON, nullable=False, default=dict)
    section_coverage = Column(JSON, nullable=False, default=dict)
    total_documents_count = Column(Integer, nullable=False, default=0)
    total_words_count = Column(Integer, nullable=False, default=0)
    recognized_sections_count = Column(Integer, nullable=False, default=0)
    extraction_warnings = Column(JSON, nullable=False, default=list)
    limitations = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="documentation_analyses")
    documents = relationship(
        "ProjectDocumentItem",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectDocumentItem.relative_path",
    )
    findings = relationship(
        "ProjectDocumentationFinding",
        back_populates="analysis",
        cascade="all, delete-orphan",
        order_by="ProjectDocumentationFinding.id",
    )

    def __repr__(self) -> str:
        return f"<ProjectDocumentationAnalysis(id={self.id}, project='{self.project_id}', score={self.preliminary_score})>"


class ProjectDocumentItem(Base):
    __tablename__ = "project_document_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_documentation_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    relative_path = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=False)
    file_format = Column(String(32), nullable=False)
    extracted_word_count = Column(Integer, nullable=False, default=0)
    extracted_char_count = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=1)
    sections_found = Column(JSON, nullable=False, default=list)
    extraction_status = Column(String(32), nullable=False, default="success")
    warning_message = Column(String(512), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectDocumentationAnalysis", back_populates="documents")

    __table_args__ = (
        Index("ix_project_doc_items_analysis_format", "analysis_id", "file_format"),
    )

    def __repr__(self) -> str:
        return f"<ProjectDocumentItem(analysis={self.analysis_id}, path='{self.relative_path}', status='{self.extraction_status}')>"


class ProjectDocumentationFinding(Base):
    __tablename__ = "project_documentation_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("project_documentation_analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(String(64), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    severity = Column(String(32), nullable=False)  # high, medium, low, advisory
    category = Column(String(64), nullable=False)  # technology_consistency, file_reference, implementation_claim, numerical_claim, documentation_quality
    explanation = Column(String(1024), nullable=False)
    doc_path = Column(String(512), nullable=True)
    location_ref = Column(String(255), nullable=True)
    documented_claim = Column(String(1024), nullable=True)
    code_evidence = Column(String(1024), nullable=True)
    verification_status = Column(String(64), nullable=False)  # verified, potential_inconsistency, claim_not_verified, insufficient_evidence
    faculty_guidance = Column(String(1024), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    analysis = relationship("ProjectDocumentationAnalysis", back_populates="findings")

    __table_args__ = (
        Index("ix_doc_findings_category_status", "analysis_id", "category", "verification_status"),
    )

    def __repr__(self) -> str:
        return f"<ProjectDocumentationFinding(id={self.id}, rule='{self.rule_id}', status='{self.verification_status}')>"
