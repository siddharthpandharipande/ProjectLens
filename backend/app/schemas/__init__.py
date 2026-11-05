from app.schemas.project import (
    ProjectStatus,
    FileCategory,
    ProjectResponse,
    UploadResponse,
    DashboardStats,
    ProjectListResponse,
    ProjectFileResponse,
    ProjectFileListResponse,
    FrameworkEvidence,
    LanguageMetric,
    ProjectStructureResponse,
    ProjectStructureWrapper,
)
from app.schemas.code_quality import (
    CodeQualityResponse,
    QualityFinding,
    FileMetricItem,
    MetricsSummary,
    ScoreExplanation,
    LanguageCoverageItem,
)

from app.schemas.similarity import (
    ProjectSimilarityResponse,
    ProjectSimilarityMatchItem,
    FileSimilarityMatchItem,
)
from app.schemas.documentation import (
    DocumentationResponse,
    DocumentItemSchema,
    SectionCoverageItem,
    DocumentationQualityMetrics,
    DocumentationScoreFactor,
    DocumentationFindingSchema,
)
from app.schemas.git_history import (
    GitHistoryResponse,
    CommitRecordSchema,
    ContributorStatSchema,
    GitFindingSchema,
    GitHistorySummarySchema,
)
from app.schemas.ai_assistance import (
    AIAssistanceSignalSchema,
    AIAssistanceAnalysisResponse,
)
from app.schemas.viva import (
    VivaQuestionSchema,
    VivaQuestionSetResponse,
    VivaGenerateRequest,
    VivaPracticeUpdateRequest,
    VivaProgressResponse,
    VIVA_CATEGORIES,
    VIVA_DIFFICULTIES,
    VIVA_MODES,
)
from app.schemas.evaluation import (
    ProjectEvaluationResponse,
    CategoryScoreSchema,
    ActionableRecommendationSchema,
    ScoreBreakdownItem,
)

__all__ = [
    "ProjectStatus",
    "FileCategory",
    "ProjectResponse",
    "UploadResponse",
    "DashboardStats",
    "ProjectListResponse",
    "ProjectFileResponse",
    "ProjectFileListResponse",
    "FrameworkEvidence",
    "LanguageMetric",
    "ProjectStructureResponse",
    "ProjectStructureWrapper",
    "CodeQualityResponse",
    "QualityFinding",
    "FileMetricItem",
    "MetricsSummary",
    "ScoreExplanation",
    "LanguageCoverageItem",
    "ProjectSimilarityResponse",
    "ProjectSimilarityMatchItem",
    "FileSimilarityMatchItem",
    "DocumentationResponse",
    "DocumentItemSchema",
    "SectionCoverageItem",
    "DocumentationQualityMetrics",
    "DocumentationScoreFactor",
    "DocumentationFindingSchema",
    "GitHistoryResponse",
    "CommitRecordSchema",
    "ContributorStatSchema",
    "GitFindingSchema",
    "GitHistorySummarySchema",
    "AIAssistanceSignalSchema",
    "AIAssistanceAnalysisResponse",
]
