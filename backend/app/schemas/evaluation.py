from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CategoryScoreSchema(BaseModel):
    """Score, weight, contribution, and evidence for an evaluation category."""

    id: str
    name: str
    score: Optional[float] = None
    weight: float
    contribution: float = 0.0
    status: str = "assessed"  # assessed, unavailable, insufficient_evidence, error
    reason: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)


class ActionableRecommendationSchema(BaseModel):
    """Prioritized, evidence-linked improvement recommendation."""

    title: str
    description: str
    priority: str = "Medium"  # Critical, High, Medium, Low, Informational
    category: str = "General"
    why_it_matters: str = Field(..., alias="whyItMatters")
    recommended_action: str = Field(..., alias="recommendedAction")
    expected_benefit: str = Field(..., alias="expectedBenefit")
    source_module: str = Field("Evaluation", alias="sourceModule")

    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)


class ScoreBreakdownItem(BaseModel):
    """Legacy-compatible breakdown item for frontend compatibility."""

    dimension: str
    score: float
    maxScore: float = 100.0
    notes: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class ProjectEvaluationResponse(BaseModel):
    """Comprehensive evaluation response for API and frontend display."""

    id: Optional[int] = None
    project_id: str = Field(..., alias="projectId")
    overall_score: Optional[float] = Field(None, alias="overallScore")
    grade: Optional[str] = None
    evaluation_status: str = Field("incomplete", alias="evaluationStatus")  # complete, partial, incomplete
    coverage_pct: float = Field(0.0, alias="coveragePct")
    
    category_scores: List[CategoryScoreSchema] = Field(default_factory=list, alias="categoryScores")
    score_breakdown: List[ScoreBreakdownItem] = Field(default_factory=list, alias="scoreBreakdown")
    
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    recommendations: List[ActionableRecommendationSchema] = Field(default_factory=list)
    module_statuses: Dict[str, str] = Field(default_factory=dict, alias="moduleStatuses")
    
    executive_summary: Optional[str] = Field(None, alias="executiveSummary")
    faculty_notes: Optional[str] = Field(None, alias="facultyNotes")
    scoring_version: str = Field("v1.0-rubric", alias="scoringVersion")
    report_available: bool = Field(True, alias="reportAvailable")
    report_url: Optional[str] = Field(None, alias="reportUrl")
    
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

