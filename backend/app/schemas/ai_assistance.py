from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AIAssistanceSignalSchema(BaseModel):
    """A single evidence signal collected during AI-assistance analysis."""

    signal_id: str = Field(..., alias="signalId")
    category: str = Field(..., alias="signalCategory")
    source: str = Field(..., alias="evidenceSource")
    observed_value: str = Field(..., alias="observedValue")
    explanation: str
    confidence: Optional[float] = None
    alternative_explanations: List[str] = Field(default_factory=list, alias="alternativeExplanations")
    availability_status: str = Field(..., alias="availabilityStatus")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator(
        "signal_id",
        "category",
        "source",
        "observed_value",
        "explanation",
        "availability_status",
        mode="before",
    )
    @classmethod
    def ensure_str(cls, v: Any) -> str:
        return str(v) if v is not None else ""

    @field_validator("confidence", mode="before")
    @classmethod
    def ensure_float(cls, v: Any) -> Optional[float]:
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("alternative_explanations", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[str]:
        if isinstance(v, (list, tuple, set)):
            return [str(item) for item in v if item is not None]
        if isinstance(v, str) and v.strip():
            return [v.strip()]
        return []


class AIAssistanceAnalysisResponse(BaseModel):
    """Project-level AI-Assistance analysis result."""

    id: Optional[int] = None
    project_id: str = Field(..., alias="projectId")
    analysis_status: str = Field(..., alias="analysisStatus")
    advisory_category: str = Field(..., alias="advisoryCategory")
    evidence_summary: List[AIAssistanceSignalSchema] = Field(
        default_factory=list, alias="evidenceSummary"
    )
    rules_version: str = Field("v1.0-deterministic", alias="rulesVersion")
    llm_provider: Optional[str] = Field(None, alias="llmProvider")
    llm_model: Optional[str] = Field(None, alias="llmModel")
    llm_interpretation_status: Optional[str] = Field(None, alias="llmInterpretationStatus")
    structured_interpretation: dict = Field(default_factory=dict, alias="structuredInterpretation")
    limitations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )