from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class DocumentItemSchema(BaseModel):
    id: Optional[int] = None
    relative_path: str = Field(..., alias="relativePath")
    filename: str
    file_format: str = Field(..., alias="fileFormat")
    extracted_word_count: int = Field(0, alias="extractedWordCount")
    extracted_char_count: int = Field(0, alias="extractedCharCount")
    page_count: int = Field(1, alias="pageCount")
    sections_found: List[str] = Field(default_factory=list, alias="sectionsFound")
    extraction_status: str = Field("success", alias="extractionStatus")
    warning_message: Optional[str] = Field(None, alias="warningMessage")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class SectionCoverageItem(BaseModel):
    section_key: str = Field(..., alias="sectionKey")
    display_name: str = Field(..., alias="displayName")
    is_required: bool = Field(..., alias="isRequired")
    is_present: bool = Field(..., alias="isPresent")
    detected_headings: List[str] = Field(default_factory=list, alias="detectedHeadings")
    found_in_files: List[str] = Field(default_factory=list, alias="foundInFiles")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class DocumentationQualityMetrics(BaseModel):
    total_documents: int = Field(0, alias="totalDocuments")
    total_words: int = Field(0, alias="totalWords")
    recognized_sections_count: int = Field(0, alias="recognizedSectionsCount")
    required_sections_present: int = Field(0, alias="requiredSectionsPresent")
    required_sections_total: int = Field(0, alias="requiredSectionsTotal")
    has_readme: bool = Field(False, alias="hasReadme")
    has_setup_instructions: bool = Field(False, alias="hasSetupInstructions")
    has_testing_section: bool = Field(False, alias="hasTestingSection")
    pdf_pages_extracted: int = Field(0, alias="pdfPagesExtracted")
    repetition_warnings: List[str] = Field(default_factory=list, alias="repetitionWarnings")

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class DocumentationScoreFactor(BaseModel):
    name: str
    points_awarded: float = Field(..., alias="pointsAwarded")
    max_points: float = Field(..., alias="maxPoints")
    notes: str

    model_config = ConfigDict(
        populate_by_name=True,
        serialize_by_alias=True,
    )


class DocumentationFindingSchema(BaseModel):
    id: Optional[int] = None
    rule_id: str = Field(..., alias="ruleId")
    title: str
    severity: str  # "high", "medium", "low", "advisory"
    category: str  # "technology_consistency", "file_reference", "implementation_claim", "numerical_claim", "documentation_quality"
    explanation: str
    doc_path: Optional[str] = Field(None, alias="docPath")
    location_ref: Optional[str] = Field(None, alias="locationRef")
    documented_claim: Optional[str] = Field(None, alias="documentedClaim")
    code_evidence: Optional[str] = Field(None, alias="codeEvidence")
    verification_status: str = Field(..., alias="verificationStatus")
    faculty_guidance: Optional[str] = Field(None, alias="facultyGuidance")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class DocumentationResponse(BaseModel):
    project_id: str = Field(..., alias="projectId")
    status: str  # "completed", "insufficient_evidence", "not_started", "error"
    preliminary_score: Optional[float] = Field(None, alias="preliminaryScore")
    scoring_version: str = Field("v1.0-deterministic-rubric", alias="scoringVersion")
    advisory_note: str = Field(
        "Advisory documentation metrics and code consistency findings for faculty review. Scores and findings are diagnostic aids and must be reviewed by faculty.",
        alias="advisoryNote",
    )
    score_explanation: Dict[str, Any] = Field(default_factory=dict, alias="scoreExplanation")
    metrics_summary: DocumentationQualityMetrics = Field(..., alias="metricsSummary")
    section_coverage: List[SectionCoverageItem] = Field(default_factory=list, alias="sectionCoverage")
    documents: List[DocumentItemSchema] = Field(default_factory=list)
    findings: List[DocumentationFindingSchema] = Field(default_factory=list)
    extraction_warnings: List[str] = Field(default_factory=list, alias="extractionWarnings")
    limitations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(..., alias="createdAt")
    updated_at: datetime = Field(..., alias="updatedAt")

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        serialize_by_alias=True,
    )
