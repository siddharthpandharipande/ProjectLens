from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


VIVA_CATEGORIES = [
    "Project Fundamentals",
    "Technical Architecture",
    "Technology Stack",
    "Implementation and Coding",
    "Innovation and Uniqueness",
    "Testing and Validation",
    "Critical Thinking and Problem Solving",
    "Project-Specific Technical Deep Dive",
    "Future Scope and Improvements",
]

VIVA_DIFFICULTIES = ["beginner", "intermediate", "advanced"]

VIVA_MODES = [
    "quick_prep",
    "complete_viva",
    "technical_deep_dive",
    "examiner_challenge",
]


class VivaQuestionSchema(BaseModel):
    """Schema for an individual personalized viva question."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: str = Field(..., description="Unique question ID")
    category: str = Field(..., description="One of the 9 Viva categories")
    difficulty: str = Field(..., description="Difficulty level: beginner, intermediate, or advanced")
    question: str = Field(..., description="The viva question text")
    examiner_rationale: str = Field(
        ...,
        alias="examinerRationale",
        description="Why an examiner might ask this question",
    )
    key_points: List[str] = Field(
        default_factory=list,
        alias="keyPoints",
        description="Key points expected in a good answer",
    )
    suggested_answer: str = Field(
        ...,
        alias="suggestedAnswer",
        description="Technically grounded suggested answer based on actual project evidence",
    )
    evidence_reference: Optional[str] = Field(
        None,
        alias="evidenceReference",
        description="Reference to relevant source file, doc section, or missing evidence note",
    )
    is_practiced: bool = Field(
        default=False,
        alias="isPracticed",
        description="Whether student marked question as practiced",
    )
    source: str = Field(
        default="gemini",
        description="Generation source: 'gemini' or 'deterministic_fallback'",
    )
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class VivaQuestionSetResponse(BaseModel):
    """Schema for a complete viva question set response."""

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    id: int = Field(..., description="Question Set ID")
    project_id: str = Field(..., alias="projectId", description="Project ID")
    mode: str = Field(..., description="Generation mode (quick_prep, complete_viva, etc.)")
    generation_source: str = Field(
        ...,
        alias="generationSource",
        description="Source of questions: gemini or deterministic_fallback",
    )
    model_name: Optional[str] = Field(
        None,
        alias="modelName",
        description="LLM Model used if Gemini AI was active",
    )
    total_questions: int = Field(..., alias="totalQuestions")
    practiced_count: int = Field(default=0, alias="practicedCount")
    questions: List[VivaQuestionSchema] = Field(default_factory=list)
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")


class VivaGenerateRequest(BaseModel):
    """Request payload for generating viva questions."""

    mode: str = Field(
        default="complete_viva",
        description="Generation mode: quick_prep, complete_viva, technical_deep_dive, examiner_challenge",
    )
    difficulty: Optional[str] = Field(
        default="all",
        description="Filter by difficulty: all, beginner, intermediate, advanced",
    )
    question_count: int = Field(
        default=10,
        ge=3,
        le=25,
        alias="questionCount",
        description="Target number of questions (3 to 25)",
    )
    force_regenerate: bool = Field(
        default=True,
        alias="forceRegenerate",
        description="Whether to overwrite existing question set",
    )


class VivaPracticeUpdateRequest(BaseModel):
    """Request to update practiced status of a question."""

    is_practiced: bool = Field(..., alias="isPracticed", description="Practiced toggle")


class VivaCategoryProgress(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    total: int = 0
    practiced: int = 0


class VivaProgressResponse(BaseModel):
    """Response detailing preparation and practice progress."""

    model_config = ConfigDict(populate_by_name=True)

    project_id: str = Field(..., alias="projectId")
    total_questions: int = Field(..., alias="totalQuestions")
    practiced_count: int = Field(..., alias="practicedCount")
    percentage: float = Field(..., description="Percentage of practiced questions (0 to 100)")
    by_category: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        alias="byCategory",
        description="Category-wise practiced breakdown",
    )
    by_difficulty: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        alias="byDifficulty",
        description="Difficulty-wise practiced breakdown",
    )
    generation_source: str = Field(default="gemini", alias="generationSource")
    last_generated_at: Optional[datetime] = Field(None, alias="lastGeneratedAt")

