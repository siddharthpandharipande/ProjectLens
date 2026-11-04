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


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    course = Column(String(128), nullable=True)
    team = Column(String(128), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    score = Column(Float, nullable=True)

    # Safe storage metadata
    archive_filename = Column(String(255), nullable=False)
    archive_path = Column(String(512), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    processing_stage = Column(String(512), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Phase 2 Relationships
    files = relationship(
        "ProjectFile",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectFile.relative_path",
    )
    structure = relationship(
        "ProjectStructure",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan",
    )
    # Phase 3 Code Quality Relationships
    quality_analyses = relationship(
        "ProjectQualityAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectQualityAnalysis.created_at.desc()",
    )
    # Phase 4 Similarity Relationships
    similarity_analyses = relationship(
        "ProjectSimilarityAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectSimilarityAnalysis.created_at.desc()",
        foreign_keys="ProjectSimilarityAnalysis.project_id",
    )
    # Phase 5 Documentation Relationships
    documentation_analyses = relationship(
        "ProjectDocumentationAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectDocumentationAnalysis.created_at.desc()",
    )
    # Phase 6 Git History Relationships
    git_history_analyses = relationship(
        "ProjectGitHistoryAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectGitHistoryAnalysis.created_at.desc()",
    )
    # Phase 7A AI-Assistance Relationships
    ai_assistance_analyses = relationship(
        "ProjectAIAssistanceAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectAIAssistanceAnalysis.created_at.desc()",
    )
    # Phase 7B Innovation Relationships
    innovation_analyses = relationship(
        "ProjectInnovationAnalysis",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ProjectInnovationAnalysis.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<Project(id='{self.id}', title='{self.title}', status='{self.status}')>"


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relative_path = Column(String(512), nullable=False)
    filename = Column(String(255), nullable=False)
    extension = Column(String(32), nullable=False, default="")
    size_bytes = Column(Integer, nullable=False, default=0)
    category = Column(String(64), nullable=False, default="Other")
    detected_language = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    project = relationship("Project", back_populates="files")

    __table_args__ = (
        UniqueConstraint("project_id", "relative_path", name="uq_project_files_path"),
        Index("ix_project_files_category", "project_id", "category"),
    )

    def __repr__(self) -> str:
        return f"<ProjectFile(project='{self.project_id}', path='{self.relative_path}', category='{self.category}')>"


class ProjectStructure(Base):
    __tablename__ = "project_structures"

    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    total_files = Column(Integer, nullable=False, default=0)
    source_files_count = Column(Integer, nullable=False, default=0)
    total_source_size_bytes = Column(Integer, nullable=False, default=0)
    languages = Column(JSON, nullable=False, default=dict)
    frameworks = Column(JSON, nullable=False, default=list)
    categories_summary = Column(JSON, nullable=False, default=dict)
    has_readme = Column(Boolean, nullable=False, default=False)
    has_git = Column(Boolean, nullable=False, default=False)
    extracted_path = Column(String(512), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="structure")

    def __repr__(self) -> str:
        return f"<ProjectStructure(project='{self.project_id}', files={self.total_files}, sources={self.source_files_count})>"
