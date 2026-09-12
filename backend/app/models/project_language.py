import uuid
from sqlalchemy import String, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class ProjectLanguage(Base):
    __tablename__ = "project_languages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(100), nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)

    project: Mapped["Project"] = relationship("Project", back_populates="languages")
