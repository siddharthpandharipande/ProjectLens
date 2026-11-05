"""Pydantic schemas for OpenRouter LLM input/output (Phase 7A).

These models define the structured evidence summary sent to the LLM and the
structured interpretation returned by the LLM. They are used to validate
both the request payload and the LLM response.
"""

from enum import StrEnum
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class InterpretationStatus(StrEnum):
    """Allowed LLM interpretation status values."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    ERROR = "error"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class EvidenceSignal(BaseModel):
    """A single deterministic evidence signal collected by Python."""

    signal_id: str = Field(..., min_length=1, max_length=64)
    category: str = Field(..., min_length=1, max_length=64)
    source: str = Field(..., min_length=1, max_length=64)
    observed_value: str = Field(..., min_length=1, max_length=2000)
    explanation: str = Field(..., min_length=1, max_length=2000)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    alternative_explanations: List[str] = Field(default_factory=list, max_length=5)
    availability_status: str = Field(..., min_length=1, max_length=32)

    model_config = ConfigDict(populate_by_name=True)


class EvidenceSummary(BaseModel):
    """Compact structured evidence summary sent to the LLM.

    Only signal metadata and references are sent — never source code,
    personal identifiers, secrets, or full documents.
    """

    project_id: str = Field(..., min_length=1, max_length=64)
    signals: List[EvidenceSignal] = Field(default_factory=list, max_length=200)
    rules_version: str = Field(..., min_length=1, max_length=32)
    advisory_category: Optional[str] = Field(None, max_length=64)

    model_config = ConfigDict(populate_by_name=True)


def _normalize_to_list_of_strings(v: Any) -> List[str]:
    """Helper to ensure input is converted to a clean list of strings."""
    if v is None:
        return []
    if isinstance(v, str):
        cleaned = v.strip()
        if not cleaned:
            return []
        lines = [line.strip().lstrip("-*•0123456789. ") for line in cleaned.split("\n") if line.strip()]
        return lines if len(lines) > 1 else [cleaned]
    if isinstance(v, (list, tuple, set)):
        result: List[str] = []
        for item in v:
            if isinstance(item, dict):
                text = " ".join(str(val) for val in item.values() if val).strip()
                if text:
                    result.append(text)
            elif item is not None:
                text = str(item).strip()
                if text:
                    result.append(text)
        return result
    if isinstance(v, dict):
        return [str(val).strip() for val in v.values() if val and str(val).strip()]
    return [str(v).strip()]


class EvidenceReference(BaseModel):
    """A reference from the LLM back to an input evidence signal ID."""

    signal_id: str = Field(..., min_length=1, max_length=64)
    observation: str = Field(..., min_length=1, max_length=1000)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("signal_id", "observation", mode="before")
    @classmethod
    def ensure_str(cls, v: Any) -> str:
        if v is None:
            return "unknown"
        if isinstance(v, (list, dict)):
            return str(v)
        return str(v)


class FactVsInterpretation(BaseModel):
    """Separation of directly observed facts, interpretation, and speculation."""

    facts: List[str] = Field(default_factory=list, max_length=50)
    interpretation: List[str] = Field(default_factory=list, max_length=50)
    speculation: List[str] = Field(default_factory=list, max_length=50)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("facts", "interpretation", "speculation", mode="before")
    @classmethod
    def normalize_list(cls, v: Any) -> List[str]:
        return _normalize_to_list_of_strings(v)


class AIAssistanceFinding(BaseModel):
    """An actionable, evidence-grounded finding and recommendation for student guidance."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1, max_length=2000)
    category: str = Field(default="Project Overview and Understanding")
    priority: str = Field(default="Medium")  # Critical, High, Medium, Low, Informational
    why_it_matters: str = Field(
        default="Important for system maintainability, correctness, and evaluation defense.",
        alias="whyItMatters",
    )
    supporting_evidence: str = Field(
        default="Derived from project analysis signals.",
        alias="supportingEvidence",
    )
    recommended_action: str = Field(..., alias="recommendedAction")
    expected_benefit: str = Field(
        default="Improves software quality and viva evaluation readiness.",
        alias="expectedBenefit",
    )
    source_reference: Optional[str] = Field(None, alias="sourceReference")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator(
        "supporting_evidence",
        "why_it_matters",
        "expected_benefit",
        "recommended_action",
        "description",
        "title",
        mode="before",
    )
    @classmethod
    def ensure_string_or_join(cls, v: Any) -> str:
        if isinstance(v, list):
            return ", ".join(str(item) for item in v if item).strip() or "Observed in project evidence."
        if isinstance(v, dict):
            return " ".join(str(val) for val in v.values() if val).strip() or "Observed in project evidence."
        if v is None:
            return ""
        return str(v)


class LLMInterpretation(BaseModel):
    """Structured interpretation returned by the LLM and validated by Python."""

    interpretation_status: InterpretationStatus
    executive_summary: str = Field(..., min_length=1, max_length=3000)
    explanation_of_patterns: str = Field(..., min_length=1, max_length=3000)
    evidence_references: List[EvidenceReference] = Field(default_factory=list, max_length=100)
    alternative_explanations: List[str] = Field(default_factory=list, max_length=20)
    faculty_follow_up_recommendations: List[str] = Field(default_factory=list, max_length=20)
    limitations: List[str] = Field(default_factory=list, max_length=20)
    fact_vs_interpretation: FactVsInterpretation = Field(default_factory=FactVsInterpretation)
    findings: List[AIAssistanceFinding] = Field(default_factory=list, max_length=50)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("interpretation_status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if any(k in v_lower for k in ("complete", "success", "ok", "review", "recommended", "analyzed")):
                return InterpretationStatus.COMPLETED
            if "partial" in v_lower:
                return InterpretationStatus.PARTIAL
            if "insufficient" in v_lower:
                return InterpretationStatus.INSUFFICIENT_EVIDENCE
            if "error" in v_lower or "failed" in v_lower:
                return InterpretationStatus.ERROR
            return InterpretationStatus.COMPLETED
        return v

    @field_validator(
        "alternative_explanations",
        "faculty_follow_up_recommendations",
        "limitations",
        mode="before",
    )
    @classmethod
    def normalize_list_fields(cls, v: Any) -> List[str]:
        return _normalize_to_list_of_strings(v)

    @field_validator("findings", mode="before")
    @classmethod
    def normalize_findings(cls, v: Any) -> List[Any]:
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
            return v
        return []

    @field_validator("fact_vs_interpretation", mode="before")
    @classmethod
    def normalize_fact_vs_interpretation(cls, v: Any) -> Any:
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            return {"interpretation": [v]}
        return {}

    @field_validator("evidence_references", mode="before")
    @classmethod
    def normalize_evidence_references(cls, v: Any) -> List[Any]:
        if isinstance(v, dict):
            if "signal_id" in v:
                return [v]
            return [{"signal_id": str(k), "observation": str(val)} for k, val in v.items()]
        if isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def _validate_non_empty_for_completed(self) -> "LLMInterpretation":
        """When status is completed, require at least an explanation."""
        if self.interpretation_status == InterpretationStatus.COMPLETED:
            if not self.explanation_of_patterns.strip():
                raise ValueError("explanation_of_patterns is required when status is completed.")
        return self


class InnovationEvidenceReference(BaseModel):
    """Reference from LLM back to an extracted feature or evidence item."""

    evidence_id: str = Field(..., min_length=1, max_length=128)
    observation: str = Field(..., min_length=1, max_length=1000)

    model_config = ConfigDict(populate_by_name=True)


class LLMInnovationInterpretation(BaseModel):
    """Structured interpretation returned by Gemini or OpenRouter model."""

    interpretation_status: str = Field("completed", min_length=1, max_length=32)
    innovation_summary: str = Field(..., min_length=1, max_length=3000)
    problem_understanding: str = Field(..., min_length=1, max_length=2000)
    proposed_solution_understanding: str = Field(..., min_length=1, max_length=2000)
    potential_contributions: List[str] = Field(default_factory=list, max_length=20)
    distinctive_elements: List[str] = Field(default_factory=list, max_length=20)
    cohort_comparison_interpretation: str = Field(..., min_length=1, max_length=3000)
    evidence_references: List[InnovationEvidenceReference] = Field(default_factory=list, max_length=50)
    alternative_explanations: List[str] = Field(default_factory=list, max_length=20)
    faculty_follow_up_recommendations: List[str] = Field(default_factory=list, max_length=20)
    limitations: List[str] = Field(default_factory=list, max_length=20)
    innovation_strengths: List[str] = Field(default_factory=list, max_length=20)
    missing_evidence: List[str] = Field(default_factory=list, max_length=20)
    improvement_recommendations: List[str] = Field(default_factory=list, max_length=20)
    confidence_classification: Optional[str] = Field(None, max_length=64)
    confidence_rationale: Optional[str] = Field(None, max_length=1000)

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("interpretation_status", mode="before")
    @classmethod
    def normalize_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("complete", "completed", "success", "ok"):
                return "completed"
            if v_lower in ("partial", "partially_completed"):
                return "partial"
            if v_lower in ("error", "failed"):
                return "error"
            if v_lower in ("insufficient_evidence", "insufficient"):
                return "insufficient_evidence"
        return v

    @field_validator(
        "problem_understanding",
        "proposed_solution_understanding",
        "innovation_summary",
        "cohort_comparison_interpretation",
        mode="before",
    )
    @classmethod
    def ensure_string(cls, v: Any) -> str:
        if isinstance(v, dict):
            return " ".join(str(val) for val in v.values() if val).strip() or "Evaluated from artifacts."
        if isinstance(v, list):
            return " ".join(str(val) for val in v if val).strip() or "Evaluated from artifacts."
        if v is None:
            return "Evaluated from artifacts."
        return str(v)

    @field_validator(
        "potential_contributions",
        "distinctive_elements",
        "alternative_explanations",
        "faculty_follow_up_recommendations",
        "limitations",
        "innovation_strengths",
        "missing_evidence",
        "improvement_recommendations",
        mode="before",
    )
    @classmethod
    def normalize_string_lists(cls, v: Any) -> List[str]:
        return _normalize_to_list_of_strings(v)

    @field_validator("evidence_references", mode="before")
    @classmethod
    def normalize_innovation_evidence_references(cls, v: Any) -> List[Any]:
        if isinstance(v, dict):
            if "evidence_id" in v:
                return [v]
            return [{"evidence_id": str(k), "observation": str(val)} for k, val in v.items()]
        if isinstance(v, list):
            return v
        return []
