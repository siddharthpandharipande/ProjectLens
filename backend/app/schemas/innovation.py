from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class FeatureEvidenceSchema(BaseModel):
    """Evidence classification for an individual project feature."""

    name: str
    description: str = ""
    evidence_type: str = Field(
        ...,
        description=(
            "One of: 'verified_match', 'documented_feature', "
            "'detected_implementation', 'unverified_claim', 'insufficient_information', 'proposed_future'"
        ),
    )
    doc_reference: Optional[str] = None
    code_reference: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class TechnologyStackSchema(BaseModel):
    """Detailed technology stack and algorithms used by the project."""

    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    libraries: List[str] = Field(default_factory=list)
    databases: List[str] = Field(default_factory=list)
    algorithms: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ArchitectureSchema(BaseModel):
    """Architecture and system component breakdown."""

    frontend_components: List[str] = Field(default_factory=list)
    backend_components: List[str] = Field(default_factory=list)
    database_structure: List[str] = Field(default_factory=list)
    modules: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class ClaimedContributionSchema(BaseModel):
    """Claims of novelty and distinction made by the project author."""

    claims: List[str] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    verification_needed: List[str] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True)


class InnovationProfileSchema(BaseModel):
    """Normalized structured profile of a project."""

    problem_statement: str = Field("", alias="problemStatement")
    domain: str = "General Software"
    target_users: List[str] = Field(default_factory=list, alias="targetUsers")
    proposed_solution: str = Field("", alias="proposedSolution")
    features: List[FeatureEvidenceSchema] = Field(default_factory=list)
    technology_stack: TechnologyStackSchema = Field(default_factory=TechnologyStackSchema, alias="technologyStack")
    architecture: ArchitectureSchema = Field(default_factory=ArchitectureSchema)
    claimed_contribution: ClaimedContributionSchema = Field(default_factory=ClaimedContributionSchema, alias="claimedContribution")
    has_documentation: bool = Field(False, alias="hasDocumentation")
    is_empty: bool = Field(False, alias="isEmpty")
    is_sufficient: bool = Field(True, alias="isSufficient")

    model_config = ConfigDict(populate_by_name=True)


class InnovationMatchSchema(BaseModel):
    """Comparison record between the current project and a cohort project."""

    compared_project_id: str = Field(..., alias="comparedProjectId")
    compared_project_title: str = Field(..., alias="comparedProjectTitle")
    problem_similarity: float = Field(0.0, alias="problemSimilarity")
    solution_similarity: float = Field(0.0, alias="solutionSimilarity")
    feature_similarity: float = Field(0.0, alias="featureSimilarity")
    technology_overlap: float = Field(0.0, alias="technologyOverlap")
    technical_approach_similarity: float = Field(0.0, alias="technicalApproachSimilarity")
    overall_similarity: float = Field(0.0, alias="overallSimilarity")
    difference_summary: Optional[str] = Field(None, alias="differenceSummary")
    evidence_references: List[Dict[str, Any]] = Field(default_factory=list, alias="evidenceReferences")

    model_config = ConfigDict(populate_by_name=True)


class InnovationAnalysisResponse(BaseModel):
    """API response model for project innovation analysis."""

    id: Optional[int] = None
    project_id: str = Field(..., alias="projectId")
    analysis_status: str = Field(..., alias="analysisStatus")
    advisory_category: str = Field(..., alias="advisoryCategory")
    profile: InnovationProfileSchema
    cohort_size: int = Field(0, alias="cohortSize")
    comparison_method: str = Field("tfidf_cosine", alias="comparisonMethod")
    matches: List[InnovationMatchSchema] = Field(default_factory=list)
    dimension_scores: Dict[str, Any] = Field(default_factory=dict, alias="dimensionScores")
    confidence_classification: Optional[str] = Field(None, alias="confidenceClassification")
    confidence_rationale: Optional[str] = Field(None, alias="confidenceRationale")
    limitations: List[str] = Field(default_factory=list)
    rules_version: str = Field("v1.0-deterministic-rubric", alias="rulesVersion")
    llm_provider: Optional[str] = Field(None, alias="llmProvider")
    llm_model: Optional[str] = Field(None, alias="llmModel")
    llm_interpretation_status: Optional[str] = Field(None, alias="llmInterpretationStatus")
    structured_interpretation: Dict[str, Any] = Field(default_factory=dict, alias="structuredInterpretation")
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )

