import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(50), default="full_analysis")
    status: Mapped[str] = mapped_column(String(50), default="queued")  # queued, analyzing, completed, failed
    progress: Mapped[int] = mapped_column(Integer, default=0)
    current_stage: Mapped[Optional[str]] = mapped_column(String(255), default="Initialized")
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="analysis_jobs")
