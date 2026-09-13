import uuid
from typing import Optional
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class ProjectFile(Base):
    __tablename__ = "project_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    file_type: Mapped[str] = mapped_column(String(50), nullable=False, default="other")  # source, documentation, config, test, asset
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    lines_total: Mapped[int] = mapped_column(Integer, default=0)
    lines_code: Mapped[int] = mapped_column(Integer, default=0)
    lines_comment: Mapped[int] = mapped_column(Integer, default=0)
    lines_blank: Mapped[int] = mapped_column(Integer, default=0)
    parse_status: Mapped[str] = mapped_column(String(50), default="success")  # success, failed, skipped
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="files")

