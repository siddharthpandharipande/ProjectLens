from typing import List, Optional, Any, Dict
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    id: str
    name: str
    student_name: Optional[str] = "Student Author"
    course: Optional[str] = "Academic Project"
    status: str
    created_at: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ProjectUploadResponse(BaseModel):
    project_id: str
    project_name: str
    status: str
    message: str

class AnalysisStatusResponse(BaseModel):
    project_id: str
    status: str
    progress: int
    current_stage: Optional[str] = None
    error: Optional[str] = None

class ProjectSummarySchema(BaseModel):
    source_files: int
    total_loc: int
    languages: int
    documentation_files: int
    test_files: int

class TechnologySchema(BaseModel):
    name: str
    category: str
    confidence: str = "HIGH"
    file_count: int = 0
    evidence: List[str] = []

class TechnologyStackSchema(BaseModel):
    technologies: List[TechnologySchema] = []
    total_count: int = 0
    category_count: int = 0

class CodeMetricsSchema(BaseModel):
    loc: int
    code_lines: int
    comment_lines: int
    average_complexity: float
    maximum_complexity: float
    functions: int
    classes: int
    test_files: int
    test_coverage: str  # e.g., "N/A"
    ai_assistance: str  # e.g., "Pending Analysis"

class EvaluationDetailSchema(BaseModel):
    score: Optional[float] = None
    status: str = "completed"
    evidence: List[str] = []
    breakdown: Dict[str, Any] = {}

class EvaluationSchema(BaseModel):
    overall_score: Optional[float] = None
    overall_status: Optional[str] = "Evaluation Pending"
    technical_execution: Optional[float] = None
    technical_execution_detail: Optional[EvaluationDetailSchema] = None
    originality: Optional[float] = None
    originality_detail: Optional[EvaluationDetailSchema] = None
    documentation_integrity: Optional[float] = None
    documentation_integrity_detail: Optional[EvaluationDetailSchema] = None
    development_process: Optional[float] = None
    development_process_detail: Optional[EvaluationDetailSchema] = None

class StrengthSchema(BaseModel):
    title: str
    description: str
    evidence: Optional[str] = None

class ImprovementSchema(BaseModel):
    title: str
    severity: str = "warning"
    description: str
    evidence: Optional[str] = None
    metric: Optional[Any] = None

class AnalysisMetaSchema(BaseModel):
    status: str
    files_analyzed: int
    files_failed: int
    total_files: int

class ProjectOverviewResponse(BaseModel):
    project: ProjectBase
    summary: ProjectSummarySchema
    technology_stack: TechnologyStackSchema
    code_metrics: CodeMetricsSchema
    evaluation: EvaluationSchema
    strengths: List[StrengthSchema]
    improvements: List[ImprovementSchema]
    analysis: AnalysisMetaSchema
