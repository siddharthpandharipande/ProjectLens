from datetime import datetime, timezone
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
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


def generate_question_id() -> str:
    """Generate a clean unique identifier for a viva question."""
    return f"vq_{uuid.uuid4().hex[:12]}"


class ProjectVivaQuestionSet(Base):
    """Represents a generated viva question set for a project (Phase 8)."""

    __tablename__ = "project_viva_question_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mode = Column(String(32), nullable=False, default="complete_viva")
    generation_source = Column(String(32), nullable=False, default="gemini")
    model_name = Column(String(128), nullable=True, default="gemini-2.5-flash")
    total_questions = Column(Integer, nullable=False, default=0)
    practiced_count = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    project = relationship("Project", back_populates="viva_question_sets")
    questions = relationship(
        "ProjectVivaQuestion",
        back_populates="question_set",
        cascade="all, delete-orphan",
        order_by="ProjectVivaQuestion.created_at.asc()",
    )

    __table_args__ = (
        Index("ix_viva_set_project_created", "project_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectVivaQuestionSet(id={self.id}, project='{self.project_id}', "
            f"mode='{self.mode}', total={self.total_questions}, practiced={self.practiced_count})>"
        )


class ProjectVivaQuestion(Base):
    """Represents an individual personalized viva question."""

    __tablename__ = "project_viva_questions"

    id = Column(String(64), primary_key=True, default=generate_question_id)
    set_id = Column(
        Integer,
        ForeignKey("project_viva_question_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id = Column(
        String(64),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category = Column(String(64), nullable=False, index=True)
    difficulty = Column(String(32), nullable=False, default="intermediate", index=True)
    question = Column(Text, nullable=False)
    examiner_rationale = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=False, default=list)
    suggested_answer = Column(Text, nullable=False)
    evidence_reference = Column(String(512), nullable=True)
    is_practiced = Column(Boolean, nullable=False, default=False, index=True)
    source = Column(String(32), nullable=False, default="gemini")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    question_set = relationship("ProjectVivaQuestionSet", back_populates="questions")
    project = relationship("Project", back_populates="viva_questions")

    __table_args__ = (
        Index("ix_viva_questions_project_cat", "project_id", "category"),
        Index("ix_viva_questions_project_practiced", "project_id", "is_practiced"),
    )

    def __repr__(self) -> str:
        return (
            f"<ProjectVivaQuestion(id='{self.id}', project='{self.project_id}', "
            f"category='{self.category}', difficulty='{self.difficulty}')>"
        )

