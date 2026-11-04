from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class QualityFinding(BaseModel):
    rule_id: str = Field(..., alias="ruleId")
    title: str
    explanation: str
    severity: str  # "High" | "Medium" | "Low" | "Info"
    file_path: str = Field(..., alias="filePath")
    line_number: Optional[int] = Field(None, alias="lineNumber")
    line_range: Optional[List[int]] = Field(None, alias="lineRange")
    metric_evidence: Optional[str] = Field(None, alias="metricEvidence")
    suggestion: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class FileMetricItem(BaseModel):
    id: Optional[int] = None
    relative_path: str = Field(..., alias="relativePath")
    language: Optional[str] = None
    loc: int = 0
    sloc: int = 0
    comments: int = 0
    blank: int = 0
    functions_count: int = Field(0, alias="functionsCount")
    classes_count: int = Field(0, alias="classesCount")
    function_names: List[str] = Field(default_factory=list, alias="functionNames")
    class_names: List[str] = Field(default_factory=list, alias="classNames")
    imports: List[str] = Field(default_factory=list)
    max_nesting_depth: Optional[int] = Field(None, alias="maxNestingDepth")
    avg_complexity: Optional[float] = Field(None, alias="avgComplexity")
    max_complexity: Optional[int] = Field(None, alias="maxComplexity")
    maintainability_index: Optional[float] = Field(None, alias="maintainabilityIndex")
    has_syntax_error: bool = Field(False, alias="hasSyntaxError")
    syntax_error_details: Optional[str] = Field(None, alias="syntaxErrorDetails")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class MetricsSummary(BaseModel):
    total_source_files: int = Field(0, alias="totalSourceFiles")
    total_loc: int = Field(0, alias="totalLoc")
    total_sloc: int = Field(0, alias="totalSloc")
    total_comments: int = Field(0, alias="totalComments")
    total_blank: int = Field(0, alias="totalBlank")
    total_functions: int = Field(0, alias="totalFunctions")
    total_classes: int = Field(0, alias="totalClasses")
    avg_complexity: Optional[float] = Field(None, alias="avgComplexity")
    max_complexity: Optional[int] = Field(None, alias="maxComplexity")
    avg_maintainability_index: Optional[float] = Field(None, alias="avgMaintainabilityIndex")
    maintainability_rating: Optional[str] = Field(None, alias="maintainabilityRating")
    syntax_errors_count: int = Field(0, alias="syntaxErrorsCount")
    total_findings: int = Field(0, alias="totalFindings")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ScoreFactor(BaseModel):
    name: str
    weight: float
    score: float
    max_score: float = Field(..., alias="maxScore")
    notes: str

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class ScoreExplanation(BaseModel):
    factors: List[ScoreFactor] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    deductions: List[str] = Field(default_factory=list)
    summary: str

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class LanguageCoverageItem(BaseModel):
    language: str
    file_count: int = Field(..., alias="fileCount")
    supported_metrics: List[str] = Field(..., alias="supportedMetrics")
    limitations: Optional[str] = None

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class CodeQualityResponse(BaseModel):
    id: Optional[int] = None
    project_id: str = Field(..., alias="projectId")
    status: str
    score: Optional[float] = None
    score_explanation: ScoreExplanation = Field(..., alias="scoreExplanation")
    metrics_summary: MetricsSummary = Field(..., alias="metricsSummary")
    file_metrics: List[FileMetricItem] = Field(default_factory=list, alias="fileMetrics")
    findings: List[QualityFinding] = Field(default_factory=list)
    language_coverage: List[LanguageCoverageItem] = Field(default_factory=list, alias="languageCoverage")
    rules_version: str = Field("v1.0-deterministic", alias="rulesVersion")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )
