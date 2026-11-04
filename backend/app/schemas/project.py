from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    FLAGGED = "flagged"


class FileCategory(str, Enum):
    SOURCE_CODE = "Source Code"
    DOCUMENTATION = "Documentation"
    CONFIGURATION = "Configuration"
    DATASET = "Dataset"
    IMAGE_OR_ASSET = "Image or Asset"
    BUILD_OR_GENERATED = "Build or Generated File"
    DEPENDENCY_OR_ENV = "Dependency or Environment File"
    OTHER = "Other"


class ProjectBase(BaseModel):
    title: str
    course: Optional[str] = None
    team: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    title: str
    course: Optional[str] = None
    team: Optional[str] = None
    status: ProjectStatus
    score: Optional[float] = None
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")
    processing_stage: Optional[str] = Field(None, alias="processingStage")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class UploadResponse(BaseModel):
    project_id: str = Field(..., alias="projectId")
    status: ProjectStatus
    message: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class DashboardStats(BaseModel):
    total_projects: int = Field(0, alias="totalProjects")
    completed_projects: int = Field(0, alias="completedProjects")
    processing_projects: int = Field(0, alias="processingProjects")
    flagged_projects: int = Field(0, alias="flaggedProjects")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    stats: Optional[DashboardStats] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


# ─── Phase 2 Schemas: Files & Structure ──────────────────────────────────────


class ProjectFileResponse(BaseModel):
    id: int
    project_id: str = Field(..., alias="projectId")
    relative_path: str = Field(..., alias="relativePath")
    filename: str
    extension: str
    size_bytes: int = Field(..., alias="sizeBytes")
    category: str
    detected_language: Optional[str] = Field(None, alias="detectedLanguage")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ProjectFileListResponse(BaseModel):
    project_id: str = Field(..., alias="projectId")
    total: int
    files: List[ProjectFileResponse]

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class FrameworkEvidence(BaseModel):
    name: str
    category: str = "Dependency"
    evidence: str

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class LanguageMetric(BaseModel):
    files: int = 0
    size_bytes: int = Field(0, alias="sizeBytes")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ProjectStructureResponse(BaseModel):
    project_id: str = Field(..., alias="projectId")
    total_files: int = Field(..., alias="totalFiles")
    source_files_count: int = Field(..., alias="sourceFilesCount")
    total_source_size_bytes: int = Field(..., alias="totalSourceSizeBytes")
    languages: Dict[str, Dict[str, int]]
    frameworks: List[Dict[str, Any]]
    categories_summary: Dict[str, int] = Field(..., alias="categoriesSummary")
    has_readme: bool = Field(..., alias="hasReadme")
    has_git: bool = Field(..., alias="hasGit")
    extracted_path: Optional[str] = Field(None, alias="extractedPath")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ProjectStructureWrapper(BaseModel):
    project_id: str = Field(..., alias="projectId")
    is_parsed: bool = Field(..., alias="isParsed")
    structure: Optional[ProjectStructureResponse] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )
