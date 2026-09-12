import uuid
from typing import List
from sqlalchemy import String, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class ProjectTechnology(Base):
    __tablename__ = "project_technologies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), default="HIGH", nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="technologies")
