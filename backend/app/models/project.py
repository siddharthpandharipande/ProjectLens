import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    student_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    course: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status: Mapped[str] = mapped_column(String(50), default="uploaded", nullable=False)
    source_type: Mapped[str] = mapped_column(String(50), default="zip", nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    files: Mapped[List["ProjectFile"]] = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    languages: Mapped[List["ProjectLanguage"]] = relationship("ProjectLanguage", back_populates="project", cascade="all, delete-orphan")
    technologies: Mapped[List["ProjectTechnology"]] = relationship("ProjectTechnology", back_populates="project", cascade="all, delete-orphan")
    code_metrics: Mapped[Optional["CodeMetric"]] = relationship("CodeMetric", back_populates="project", uselist=False, cascade="all, delete-orphan")
    analysis_jobs: Mapped[List["AnalysisJob"]] = relationship("AnalysisJob", back_populates="project", cascade="all, delete-orphan")
