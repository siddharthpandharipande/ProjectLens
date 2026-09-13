import uuid
from typing import Optional
from sqlalchemy import String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


class CodeMetric(Base):
    __tablename__ = "code_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_loc: Mapped[int] = mapped_column(Integer, default=0)
    code_lines: Mapped[int] = mapped_column(Integer, default=0)
    comment_lines: Mapped[int] = mapped_column(Integer, default=0)
    blank_lines: Mapped[int] = mapped_column(Integer, default=0)
    source_file_count: Mapped[int] = mapped_column(Integer, default=0)
    function_count: Mapped[int] = mapped_column(Integer, default=0)
    class_count: Mapped[int] = mapped_column(Integer, default=0)
    average_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    maximum_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    test_file_count: Mapped[int] = mapped_column(Integer, default=0)
    documentation_file_count: Mapped[int] = mapped_column(Integer, default=0)
    git_history_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="code_metrics")

