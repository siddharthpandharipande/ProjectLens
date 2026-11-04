"""Pydantic schemas for OpenRouter LLM input/output (Phase 7A).

These models define the structured evidence summary sent to the LLM and the
structured interpretation returned by the LLM. They are used to validate
both the request payload and the LLM response.
"""

from enum import StrEnum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class EvidenceReference(BaseModel):
    """A reference from the LLM back to an input evidence signal ID."""

    signal_id: str = Field(..., min_length=1, max_length=64)
    observation: str = Field(..., min_length=1, max_length=1000)

    model_config = ConfigDict(populate_by_name=True)


class FactVsInterpretation(BaseModel):
    """Separation of directly observed facts, interpretation, and speculation."""

    facts: List[str] = Field(default_factory=list, max_length=50)
    interpretation: List[str] = Field(default_factory=list, max_length=50)
    speculation: List[str] = Field(default_factory=list, max_length=50)


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

    model_config = ConfigDict(populate_by_name=True)

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
    """Structured interpretation returned by OpenRouter Gemma model."""

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

    model_config = ConfigDict(populate_by_name=True)
