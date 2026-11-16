from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.project import Project, ProjectFile, ProjectStructure
from app.schemas.project import DashboardStats, ProjectStatus
from app.services.storage_service import StorageService


class ProjectService:
    @staticmethod
    def create_project(
        db: Session,
        title: Optional[str],
        course: Optional[str],
        archive_filename: str,
        archive_path: str,
        file_size_bytes: int,
        team: Optional[str] = None,
    ) -> Project:
        """Create and persist a new Project record."""
        project_id = StorageService.generate_project_id()
        
        # Fall back to base filename if no explicit title given
        effective_title = (title or "").strip()
        if not effective_title:
            effective_title = archive_filename.removesuffix(".zip").removesuffix(".ZIP")

        project = Project(
            id=project_id,
            title=effective_title,
            course=(course or "").strip() or None,
            team=(team or "").strip() or None,
            status=ProjectStatus.PENDING.value,
            archive_filename=archive_filename,
            archive_path=archive_path,
            file_size_bytes=file_size_bytes,
            processing_stage="Queued for analysis",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_project_by_id(db: Session, project_id: str) -> Optional[Project]:
        """Fetch a single project by its primary key ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def list_projects(db: Session) -> Tuple[List[Project], DashboardStats]:
        """Fetch all projects ordered by newest first, and calculate summary stats."""
        projects = db.query(Project).order_by(Project.created_at.desc()).all()

        total = len(projects)
        completed = sum(
            1 for p in projects
            if p.status == ProjectStatus.COMPLETED.value or p.score is not None
        )
        processing = sum(
            1 for p in projects
            if p.status == ProjectStatus.PROCESSING.value and p.score is None
        )
        flagged = sum(1 for p in projects if p.status == ProjectStatus.FLAGGED.value)

        stats = DashboardStats(
            totalProjects=total,
            completedProjects=completed,
            processingProjects=processing,
            flaggedProjects=flagged,
        )

        return projects, stats

    @staticmethod
    def get_project_structure(db: Session, project_id: str) -> Optional[ProjectStructure]:
        """Fetch the parsed structure for a project, or None if not yet parsed."""
        return db.query(ProjectStructure).filter(ProjectStructure.project_id == project_id).first()

    @staticmethod
    def get_project_files(
        db: Session,
        project_id: str,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[ProjectFile], int]:
        """Fetch paginated file records for a project, with optional category filtering."""
        query = db.query(ProjectFile).filter(ProjectFile.project_id == project_id)
        if category:
            query = query.filter(ProjectFile.category == category)
        
        total = query.count()
        files = query.order_by(ProjectFile.relative_path).offset(offset).limit(limit).all()
        return files, total
