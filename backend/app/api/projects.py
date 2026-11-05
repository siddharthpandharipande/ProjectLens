import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.project import (
    ProjectResponse,
    UploadResponse,
    ProjectListResponse,
    ProjectFileListResponse,
    ProjectStructureResponse,
)
from app.schemas.code_quality import CodeQualityResponse
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
    DocumentationFindingSchema,
)
from app.models.documentation import ProjectDocumentationAnalysis
from app.schemas.git_history import (
    GitHistoryResponse,
    CommitRecordSchema,
    ContributorStatSchema,
    GitFindingSchema,
    GitHistorySummarySchema,
)
from app.services.storage_service import StorageService
from app.services.project_service import ProjectService
from app.services.project_parser import ProjectParser
from app.services.code_quality import CodeQualityService
from app.services.similarity import SimilarityService, SimilarityScoringEngine
from app.services.documentation import DocumentationService
from app.services.git_history import GitHistoryService
from app.services.ai_assistance.service import AIAssistanceService
from app.schemas.ai_assistance import AIAssistanceAnalysisResponse
from app.services.innovation.service import InnovationService
from app.schemas.innovation import (
    InnovationAnalysisResponse,
    InnovationProfileSchema,
)
from app.services.viva.service import VivaService
from app.services.evaluation.service import EvaluationService, sanitize_filename
from app.schemas.evaluation import ProjectEvaluationResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload project ZIP archive and parse structure",
)
async def upload_project(
    file: UploadFile = File(..., description="Project source code archive (.zip)"),
    course: Optional[str] = Form(None, description="Course / section identifier"),
    title: Optional[str] = Form(None, description="Human-readable project title"),
    team: Optional[str] = Form(None, description="Team or student group identifier"),
    db: Session = Depends(get_db),
):
    """
    Accept an uploaded ZIP archive, validate its integrity and path safety,
    enforce file size limits, persist the Project record, and execute safe
    extraction with language and framework detection.
    """
    # 1. Validate and save file securely
    sanitized_filename, archive_path, file_size = await StorageService.validate_and_save_upload(file)

    # 2. Persist initial project metadata in database
    project = ProjectService.create_project(
        db=db,
        title=title,
        course=course,
        team=team,
        archive_filename=sanitized_filename,
        archive_path=archive_path,
        file_size_bytes=file_size,
    )

    # 3. Extract and parse project structure safely
    try:
        ProjectParser.extract_and_parse_project(db, project)
    except Exception as e:
        # Keep project record but update stage if parsing encountered issues
        try:
            error_msg = getattr(e, "detail", str(e))
            project.processing_stage = f"Extraction error: {error_msg}"[:512]
            db.commit()
        except Exception:
            db.rollback()
        raise

    return UploadResponse(
        projectId=project.id,
        status=project.status,
        message="Project archive uploaded, safely extracted, and structure analyzed successfully.",
    )


@router.get(
    "",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List all submitted projects and summary stats",
)
def list_projects(db: Session = Depends(get_db)):
    """Retrieve all submitted project records with live aggregate status metrics."""
    projects, stats = ProjectService.list_projects(db)
    return ProjectListResponse(
        projects=projects,
        stats=stats,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single project details by ID",
)
def get_project(project_id: str, db: Session = Depends(get_db)):
    """Retrieve detailed project evaluation status and metadata."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    return project


@router.get(
    "/{project_id}/structure",
    response_model=ProjectStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project structure summary",
)
def get_project_structure(project_id: str, db: Session = Depends(get_db)):
    """
    Retrieve project structure analysis, including languages detected,
    frameworks, category counts, documentation presence, and Git metadata.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    structure = ProjectService.get_project_structure(db, project_id)
    if not structure:
        # Try on-demand parse if archive is present
        if project.archive_path:
            try:
                structure = ProjectParser.extract_and_parse_project(db, project)
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project structure has not been analyzed yet: {str(e)}",
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project structure has not been analyzed for '{project_id}'.",
            )

    return structure


@router.get(
    "/{project_id}/files",
    response_model=ProjectFileListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get file inventory for a project",
)
def get_project_files(
    project_id: str,
    category: Optional[str] = Query(None, description="Filter by file category"),
    limit: int = Query(100, ge=1, le=1000, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    db: Session = Depends(get_db),
):
    """
    Retrieve the indexed file inventory for a project, including relative paths,
    file sizes, categories, and detected programming languages.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    files, total = ProjectService.get_project_files(
        db=db,
        project_id=project_id,
        category=category,
        limit=limit,
        offset=offset,
    )

    return ProjectFileListResponse(
        projectId=project_id,
        total=total,
        files=files,
    )


@router.post(
    "/{project_id}/parse",
    response_model=ProjectStructureResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger or re-run project structure parsing",
)
def parse_project(project_id: str, db: Session = Depends(get_db)):
    """Trigger safe re-extraction, inventorying, and language/framework detection."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    structure = ProjectParser.extract_and_parse_project(db, project)
    return structure


# ─── Phase 3: Code Quality Analysis Endpoints ───────────────────────────────


@router.post(
    "/{project_id}/analyze/code-quality",
    response_model=CodeQualityResponse,
    status_code=status.HTTP_200_OK,
    summary="Run or refresh Code Quality AST analysis",
)
def analyze_code_quality(project_id: str, db: Session = Depends(get_db)):
    """
    Execute deterministic static code quality analysis using Python's built-in AST
    module and Radon, with Tree-sitter for JavaScript, TypeScript, and Java.
    Enforces safe execution without running or importing student scripts.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        quality_analysis = CodeQualityService.analyze_project(db=db, project_id=project_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code quality analysis failed: {str(e)}",
        )

    return quality_analysis


@router.get(
    "/{project_id}/code-quality",
    response_model=CodeQualityResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved Code Quality analysis results",
)
def get_code_quality(project_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the most recent saved code-quality analysis for a project,
    including project-level metrics, per-file metrics, findings, and score explanation.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    quality = CodeQualityService.get_project_quality(db=db, project_id=project_id)
    if not quality:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Code quality analysis has not been performed for project '{project_id}'.",
        )

    return quality


def _serialize_similarity_response(analysis) -> ProjectSimilarityResponse:
    """Helper to convert ProjectSimilarityAnalysis DB model into Pydantic schema."""
    matches_list = []
    for m in analysis.matches:
        file_matches = []
        for fm in (m.strongest_file_matches or []):
            cur_lines = fm.get("currentLines", (1, 1))
            mat_lines = fm.get("matchedLines", (1, 1))
            file_matches.append(
                FileSimilarityMatchItem(
                    currentFile=fm.get("currentFile", ""),
                    matchedFile=fm.get("matchedFile", ""),
                    currentLines=(cur_lines[0], cur_lines[1]) if len(cur_lines) >= 2 else (1, 1),
                    matchedLines=(mat_lines[0], mat_lines[1]) if len(mat_lines) >= 2 else (1, 1),
                    similarityPercent=fm.get("similarityPercent", 0.0),
                    identicalStatements=fm.get("identicalStatements", 0),
                    currentSnippet=fm.get("currentSnippet", ""),
                    matchedSnippet=fm.get("matchedSnippet", ""),
                    tokenSimilarity=fm.get("tokenSimilarity"),
                    structuralSimilarity=fm.get("structuralSimilarity"),
                    semanticSimilarity=fm.get("semanticSimilarity"),
                    comparisonMethod=fm.get("comparisonMethod", "token+ast"),
                )
            )

        matches_list.append(
            ProjectSimilarityMatchItem(
                matchedProjectId=m.matched_project_id,
                matchedProjectTitle=m.matched_project_title or m.matched_project_id,
                overallSimilarity=m.overall_similarity,
                similarityCategory=m.similarity_category or "minimal",
                tokenSimilarity=m.token_similarity,
                structuralSimilarity=m.structural_similarity,
                semanticSimilarity=m.semantic_similarity,
                sourceCoveragePct=m.source_coverage_pct,
                matchedCoveragePct=m.matched_coverage_pct,
                identicalStatements=m.identical_statements_count,
                matchedFilesCount=m.matched_files_count,
                totalComparedFiles=m.total_compared_files,
                strongestFileMatches=file_matches,
            )
        )

    sim_cat = "minimal"
    if analysis.highest_similarity_score is not None:
        sim_cat = SimilarityScoringEngine.get_similarity_category(analysis.highest_similarity_score)

    return ProjectSimilarityResponse(
        projectId=analysis.project_id,
        status=analysis.status,
        overallSimilarity=analysis.highest_similarity_score or 0.0,
        similarityCategory=sim_cat,
        advisoryNote=analysis.advisory_note,
        comparedProjectsCount=analysis.compared_projects_count,
        comparedFilesCount=analysis.compared_files_count,
        scoringVersion=analysis.scoring_version,
        methodsUsed=analysis.methods_used or [],
        limitations=analysis.limitations or [],
        matches=matches_list,
        createdAt=analysis.created_at,
        updatedAt=analysis.updated_at,
    )


@router.post(
    "/{project_id}/analyze/similarity",
    response_model=ProjectSimilarityResponse,
    summary="Run or refresh Code Similarity analysis",
)
def run_similarity_analysis(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Executes or refreshes code similarity comparison against other eligible
    submissions stored in the database.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        analysis = SimilarityService.analyze_project(db=db, project_id=project_id)
        return _serialize_similarity_response(analysis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Similarity analysis execution failed: {str(e)}",
        )


@router.get(
    "/{project_id}/similarity",
    response_model=ProjectSimilarityResponse,
    summary="Get saved Code Similarity analysis results",
)
def get_similarity_results(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the most recent saved code similarity analysis from PostgreSQL.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    analysis = SimilarityService.get_project_similarity(db=db, project_id=project_id)
    if not analysis:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return ProjectSimilarityResponse(
            projectId=project_id,
            status="not_started",
            overallSimilarity=0.0,
            similarityCategory="minimal",
            advisoryNote=SimilarityScoringEngine.ADVISORY_NOTE,
            comparedProjectsCount=0,
            comparedFilesCount=0,
            scoringVersion="v1.0-hierarchical-ast-tokens",
            methodsUsed=["token_shingles", "hierarchical_ast"],
            limitations=["No similarity analysis has been run for this project yet."],
            matches=[],
            createdAt=now,
            updatedAt=now,
        )

    return _serialize_similarity_response(analysis)


def _serialize_documentation_response(analysis: ProjectDocumentationAnalysis) -> DocumentationResponse:
    docs = [
        DocumentItemSchema(
            id=d.id,
            relativePath=d.relative_path,
            filename=d.filename,
            fileFormat=d.file_format,
            extractedWordCount=d.extracted_word_count,
            extractedCharCount=d.extracted_char_count,
            pageCount=d.page_count,
            sectionsFound=d.sections_found or [],
            extractionStatus=d.extraction_status,
            warningMessage=d.warning_message,
        )
        for d in (analysis.documents or [])
    ]

    findings = [
        DocumentationFindingSchema(
            id=f.id,
            ruleId=f.rule_id,
            title=f.title,
            severity=f.severity,
            category=f.category,
            explanation=f.explanation,
            docPath=f.doc_path,
            locationRef=f.location_ref,
            documentedClaim=f.documented_claim,
            codeEvidence=f.code_evidence,
            verificationStatus=f.verification_status,
            facultyGuidance=f.faculty_guidance,
        )
        for f in (analysis.findings or [])
    ]

    coverage = [
        SectionCoverageItem(
            sectionKey=item.get("sectionKey", item.get("section_key", "")),
            displayName=item.get("displayName", item.get("display_name", "")),
            isRequired=item.get("isRequired", item.get("is_required", False)),
            isPresent=item.get("isPresent", item.get("is_present", False)),
            detectedHeadings=item.get("detectedHeadings", item.get("detected_headings", [])),
            foundInFiles=item.get("foundInFiles", item.get("found_in_files", [])),
        )
        for item in (analysis.section_coverage or [])
    ]

    metrics_raw = analysis.metrics_summary or {}
    metrics = DocumentationQualityMetrics(
        totalDocuments=metrics_raw.get("totalDocuments", metrics_raw.get("total_documents", 0)),
        totalWords=metrics_raw.get("totalWords", metrics_raw.get("total_words", 0)),
        recognizedSectionsCount=metrics_raw.get("recognizedSectionsCount", metrics_raw.get("recognized_sections_count", 0)),
        requiredSectionsPresent=metrics_raw.get("requiredSectionsPresent", metrics_raw.get("required_sections_present", 0)),
        requiredSectionsTotal=metrics_raw.get("requiredSectionsTotal", metrics_raw.get("required_sections_total", 0)),
        hasReadme=metrics_raw.get("hasReadme", metrics_raw.get("has_readme", False)),
        hasSetupInstructions=metrics_raw.get("hasSetupInstructions", metrics_raw.get("has_setup_instructions", False)),
        hasTestingSection=metrics_raw.get("hasTestingSection", metrics_raw.get("has_testing_section", False)),
        pdfPagesExtracted=metrics_raw.get("pdfPagesExtracted", metrics_raw.get("pdf_pages_extracted", 0)),
        repetitionWarnings=metrics_raw.get("repetitionWarnings", metrics_raw.get("repetition_warnings", [])),
    )

    return DocumentationResponse(
        projectId=analysis.project_id,
        status=analysis.status,
        preliminaryScore=analysis.preliminary_score,
        scoringVersion=analysis.scoring_version or "v1.0-deterministic-rubric",
        advisoryNote=(
            "Advisory documentation metrics and code consistency findings for faculty review. "
            "Scores and findings are diagnostic aids and must be reviewed by faculty."
        ),
        scoreExplanation=analysis.factors_explanation or {},
        metricsSummary=metrics,
        sectionCoverage=coverage,
        documents=docs,
        findings=findings,
        extractionWarnings=analysis.extraction_warnings or [],
        limitations=analysis.limitations or [],
        createdAt=analysis.created_at,
        updatedAt=analysis.updated_at,
    )


@router.post(
    "/{project_id}/analyze/documentation",
    response_model=DocumentationResponse,
    summary="Run or refresh Documentation Analysis and Consistency checks",
)
def run_documentation_analysis(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Executes or refreshes documentation text extraction, section recognition,
    quality metrics calculation, and code-documentation consistency checks.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    try:
        analysis = DocumentationService.analyze_project(db=db, project_id=project_id)
        return _serialize_documentation_response(analysis)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Documentation analysis failed: {str(e)}",
        )


@router.get(
    "/{project_id}/documentation",
    response_model=DocumentationResponse,
    summary="Get saved Documentation Analysis and Consistency findings",
)
def get_documentation_results(
    project_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the most recent saved documentation analysis from PostgreSQL.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    analysis = DocumentationService.get_project_documentation(db=db, project_id=project_id)
    if not analysis:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return DocumentationResponse(
            projectId=project_id,
            status="not_started",
            preliminaryScore=None,
            scoringVersion="v1.0-deterministic-rubric",
            advisoryNote=(
                "Advisory documentation metrics and code consistency findings for faculty review. "
                "Scores and findings are diagnostic aids and must be reviewed by faculty."
            ),
            scoreExplanation={"status": "not_started", "summary": "Documentation analysis has not been executed yet."},
            metricsSummary=DocumentationQualityMetrics(
                totalDocuments=0,
                totalWords=0,
                recognizedSectionsCount=0,
                requiredSectionsPresent=0,
                requiredSectionsTotal=5,
                hasReadme=False,
                hasSetupInstructions=False,
                hasTestingSection=False,
                pdfPagesExtracted=0,
                repetitionWarnings=[],
            ),
            sectionCoverage=[],
            documents=[],
            findings=[],
            extractionWarnings=[],
            limitations=["No documentation analysis has been run for this project yet."],
            createdAt=now,
            updatedAt=now,
        )

    return _serialize_documentation_response(analysis)


@router.post(
    "/{project_id}/analyze/ai-assistance",
    response_model=AIAssistanceAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run AI-assistance evidence analysis",
)
def analyze_ai_assistance(project_id: str, db: Session = Depends(get_db)):
    """Collect deterministic evidence and optionally interpret it with OpenRouter."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    try:
        return AIAssistanceService.analyze_project(db=db, project_id=project_id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI-assistance analysis failed: {type(exc).__name__}.",
        ) from exc


@router.get(
    "/{project_id}/ai-assistance",
    response_model=AIAssistanceAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved AI-assistance analysis",
)
def get_ai_assistance(project_id: str, db: Session = Depends(get_db)):
    """Return the saved result without making an LLM request."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    analysis = AIAssistanceService.get_latest_analysis(db=db, project_id=project_id)
    if analysis:
        return analysis
    now = datetime.now(timezone.utc)
    return AIAssistanceAnalysisResponse(
        projectId=project_id,
        analysisStatus="not_started",
        advisoryCategory="Insufficient Evidence",
        evidenceSummary=[],
        rulesVersion="v1.0-deterministic",
        llmInterpretationStatus="not_requested",
        structuredInterpretation={},
        limitations=["AI-assistance analysis has not been run for this project yet."],
        createdAt=now,
        updatedAt=now,
    )


@router.post(
    "/{project_id}/analyze/innovation",
    response_model=InnovationAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Innovation and distinctiveness analysis",
)
def analyze_innovation(project_id: str, db: Session = Depends(get_db)):
    """Extract structured project profile, compare against cohort, and assess distinctiveness."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    try:
        return InnovationService.analyze_project(db=db, project_id=project_id)
    except Exception as exc:
        db.rollback()
        logger.exception("Innovation analysis failed for project %s: %s", project_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Innovation analysis failed: {type(exc).__name__}: {str(exc)}",
        ) from exc


@router.get(
    "/{project_id}/innovation",
    response_model=InnovationAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved Innovation analysis",
)
def get_innovation(project_id: str, db: Session = Depends(get_db)):
    """Return the saved innovation analysis without making an LLM request."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    analysis = InnovationService.get_latest_analysis(db=db, project_id=project_id)
    if analysis:
        return analysis
    now = datetime.now(timezone.utc)
    return InnovationAnalysisResponse(
        projectId=project_id,
        analysisStatus="not_started",
        advisoryCategory="Not Started",
        profile=InnovationProfileSchema(
            domain="General Software",
            hasDocumentation=False,
            isEmpty=False,
            isSufficient=False,
        ),
        cohortSize=0,
        comparisonMethod="unavailable",
        matches=[],
        dimensionScores={},
        limitations=["Innovation analysis has not been run for this project yet."],
        rulesVersion="v1.0-deterministic-rubric",
        llmInterpretationStatus="not_requested",
        structuredInterpretation={},
        createdAt=now,
        updatedAt=now,
    )


@router.get(
    "/{project_id}/analysis",
    status_code=status.HTTP_200_OK,
    summary="Get unified multi-module analysis status",
)
def get_project_analysis_bundle(project_id: str, db: Session = Depends(get_db)):
    """
    Unified analysis aggregator returning current progress across all ProjectLens
    modules. Phase 3 provides real Code Quality metrics; Phase 4 provides real
    Code Similarity results; Phase 5 provides real Documentation Analysis.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    cq = CodeQualityService.get_project_quality(db=db, project_id=project_id)

    code_quality_data = None
    if cq:
        metrics = cq.metrics_summary or {}
        code_quality_data = {
            "linesOfCode": metrics.get("total_sloc", 0),
            "languageBreakdown": {},
            "modulesAndClasses": metrics.get("total_classes", 0),
            "filesCount": metrics.get("total_source_files", 0),
            "cyclomaticComplexityAvg": metrics.get("avg_complexity", 1.0) or 1.0,
            "maintainabilityScore": metrics.get("maintainability_rating") or "A",
            "issues": [
                {
                    "severity": f.get("severity", "info").lower(),
                    "file": f.get("file_path", ""),
                    "ruleId": f.get("rule_id", ""),
                    "description": f.get("explanation", ""),
                }
                for f in (cq.findings or [])
            ],
        }

    sim = SimilarityService.get_project_similarity(db=db, project_id=project_id)
    similarity_data = None
    if sim and sim.status != "not_started":
        legacy_matches = []
        for m in sim.matches:
            for fm in (m.strongest_file_matches or []):
                cur_l = fm.get("currentLines", (1, 1))
                mat_l = fm.get("matchedLines", (1, 1))
                legacy_matches.append({
                    "matchedProject": m.matched_project_title or m.matched_project_id,
                    "matchedFile": fm.get("matchedFile", ""),
                    "currentFile": fm.get("currentFile", ""),
                    "currentLines": [cur_l[0], cur_l[1]] if len(cur_l) >= 2 else [1, 1],
                    "matchedLines": [mat_l[0], mat_l[1]] if len(mat_l) >= 2 else [1, 1],
                    "similarityPercent": fm.get("similarityPercent", 0.0),
                    "identicalStatements": fm.get("identicalStatements", 0),
                    "currentSnippet": fm.get("currentSnippet", ""),
                    "matchedSnippet": fm.get("matchedSnippet", ""),
                })
        similarity_data = {
            "overallSimilarity": sim.highest_similarity_score or 0.0,
            "matches": legacy_matches,
            "advisoryNote": sim.advisory_note,
        }

    doc = DocumentationService.get_project_documentation(db=db, project_id=project_id)
    documentation_data = None
    if doc and doc.status != "not_started":
        doc_checks = [
            {
                "section": f.category.replace("_", " ").title(),
                "claim": f.documented_claim or f.title,
                "actual": f.code_evidence or f.explanation,
                "status": "verified" if f.verification_status == "verified" else ("discrepancy" if f.verification_status == "potential_inconsistency" else "partial"),
            }
            for f in (doc.findings or [])
        ]
        documentation_data = {
            "docChecks": doc_checks,
            "preliminaryScore": doc.preliminary_score,
            "status": doc.status,
            "totalDocuments": doc.total_documents_count,
            "totalWords": doc.total_words_count,
            "recognizedSections": doc.recognized_sections_count,
            "metricsSummary": doc.metrics_summary,
            "sectionCoverage": doc.section_coverage,
            "findings": [
                {
                    "ruleId": f.rule_id,
                    "title": f.title,
                    "severity": f.severity,
                    "category": f.category,
                    "explanation": f.explanation,
                    "docPath": f.doc_path,
                    "locationRef": f.location_ref,
                    "documentedClaim": f.documented_claim,
                    "codeEvidence": f.code_evidence,
                    "verificationStatus": f.verification_status,
                    "facultyGuidance": f.faculty_guidance,
                }
                for f in (doc.findings or [])
            ],
            "documents": [
                {
                    "relativePath": d.relative_path,
                    "filename": d.filename,
                    "fileFormat": d.file_format,
                    "extractedWordCount": d.extracted_word_count,
                    "pageCount": d.page_count,
                    "extractionStatus": d.extraction_status,
                    "warningMessage": d.warning_message,
                }
                for d in (doc.documents or [])
            ],
            "commitHistory": [],
            "totalCommits": 0,
            "commitWeeks": 0,
        }

    doc_status = "not_started"
    if doc:
        doc_status = "completed" if doc.status in ("completed", "insufficient_evidence") else doc.status

    # Phase 6: Git development history
    git_hist = GitHistoryService.get_latest_analysis(db=db, project_id=project_id)
    dev_history_data = None
    if git_hist:
        dev_history_data = {
            "status": git_hist.status,
            "availability": git_hist.availability,
            "isShallow": git_hist.is_shallow,
            "totalCommits": git_hist.total_commits,
            "distinctContributorsCount": git_hist.distinct_contributors_count,
            "firstCommitAt": git_hist.first_commit_at.isoformat() if git_hist.first_commit_at else None,
            "lastCommitAt": git_hist.last_commit_at.isoformat() if git_hist.last_commit_at else None,
            "durationDays": git_hist.duration_days,
            "totalAdditions": git_hist.total_additions,
            "totalDeletions": git_hist.total_deletions,
            "totalFilesChanged": git_hist.total_files_changed,
            "limitations": git_hist.limitations,
        }

    git_status = "not_started"
    if git_hist:
        git_status = git_hist.status if git_hist.status != "completed" else "completed"

    ai_assistance = AIAssistanceService.get_latest_analysis(db=db, project_id=project_id)
    innovation = InnovationService.get_latest_analysis(db=db, project_id=project_id)
    viva_set = VivaService.get_latest_question_set(db=db, project_id=project_id)

    ai_innov_status = "not_started"
    if ai_assistance or innovation:
        ai_innov_status = "completed"

    viva_status = "completed" if viva_set and viva_set.questions else "not_started"

    # Final Phase: Consolidated Evaluation & Scoring
    latest_eval = EvaluationService.get_latest_evaluation(db=db, project_id=project_id)
    eval_report_data = None
    if latest_eval:
        eval_report_data = {
            "overallScore": latest_eval.overall_score if latest_eval.overall_score is not None else (project.score or 0.0),
            "grade": latest_eval.grade,
            "scoreBreakdown": [item.model_dump(by_alias=True) for item in latest_eval.score_breakdown],
            "facultyNotes": latest_eval.faculty_notes,
            "reportAvailable": True,
            "reportUrl": f"/api/projects/{project_id}/report",
            "evaluationStatus": latest_eval.evaluation_status,
            "coveragePct": latest_eval.coverage_pct,
            "evaluation": latest_eval.model_dump(by_alias=True),
        }
    elif project.score is not None:
        eval_report_data = {
            "overallScore": project.score,
            "grade": None,
            "scoreBreakdown": [],
            "facultyNotes": None,
            "reportAvailable": True,
            "reportUrl": f"/api/projects/{project_id}/report",
            "evaluationStatus": "partial",
            "coveragePct": 100.0,
        }
    else:
        eval_report_data = {
            "overallScore": 0.0,
            "grade": None,
            "scoreBreakdown": [],
            "facultyNotes": None,
            "reportAvailable": True,
            "reportUrl": f"/api/projects/{project_id}/report",
            "evaluationStatus": "not_started",
            "coveragePct": 0.0,
        }

    eval_status = "completed" if latest_eval else ("partial" if project.score is not None else "not_started")

    return {
        "projectId": project_id,
        "modules": [
            {"name": "Code Quality", "status": "completed" if cq else "not_started"},
            {"name": "Similarity", "status": "completed" if sim and sim.status != "not_started" else "not_started"},
            {"name": "Documentation & Development", "status": doc_status},
            {"name": "Development History", "status": git_status},
            {"name": "AI Assistance & Innovation", "status": ai_innov_status},
            {"name": "Viva Questions", "status": viva_status},
            {"name": "Evaluation Report", "status": eval_status},
        ],
        "codeQuality": code_quality_data,
        "similarity": similarity_data,
        "documentation": documentation_data,
        "developmentHistory": dev_history_data,
        "aiAssistance": ai_assistance.model_dump(by_alias=True) if ai_assistance else None,
        "innovation": innovation.model_dump(by_alias=True) if innovation else None,
        "vivaQuestions": [q.model_dump(by_alias=True) for q in viva_set.questions] if viva_set else [],
        "vivaQuestionSet": viva_set.model_dump(by_alias=True) if viva_set else None,
        "evaluationReport": eval_report_data,
    }


def _serialize_git_history_response(analysis) -> GitHistoryResponse:
    """Build GitHistoryResponse from ORM object."""
    commits_out = []
    for c in (analysis.commits or []):
        commits_out.append(
            CommitRecordSchema(
                commitHash=c.commit_hash,
                shortHash=c.short_hash,
                committedAt=c.committed_at,
                authorName=c.author_name,
                authorEmail=c.author_email,
                subject=c.subject,
                filesChangedCount=c.files_changed_count,
                linesAdded=c.lines_added,
                linesDeleted=c.lines_deleted,
                isMerge=c.is_merge,
                changedFiles=c.changed_files or [],
            )
        )
    # Sort oldest first for timeline display
    commits_out.sort(key=lambda x: x.committed_at)

    findings_out = [
        GitFindingSchema(
            id=f.id,
            signalId=f.signal_id,
            title=f.title,
            severity=f.severity,
            category=f.category,
            explanation=f.explanation,
            evidence=f.evidence or {},
            facultyGuidance=f.faculty_guidance,
        )
        for f in (analysis.findings or [])
    ]

    summary = None
    if analysis.availability == "available":
        contributors_out = [
            ContributorStatSchema(
                name=c.get("name", "Unknown"),
                email=c.get("email", ""),
                commitCount=c.get("commit_count", 0),
                additions=c.get("additions", 0),
                deletions=c.get("deletions", 0),
                percentage=c.get("percentage", 0.0),
            )
            for c in (analysis.contributors_summary or [])
        ]
        summary = GitHistorySummarySchema(
            totalCommits=analysis.total_commits,
            distinctContributorsCount=analysis.distinct_contributors_count,
            firstCommitAt=analysis.first_commit_at,
            lastCommitAt=analysis.last_commit_at,
            durationDays=analysis.duration_days,
            totalFilesChanged=analysis.total_files_changed,
            totalAdditions=analysis.total_additions,
            totalDeletions=analysis.total_deletions,
            avgTimeBetweenCommitsHours=analysis.avg_time_between_commits_hours,
            medianTimeBetweenCommitsHours=analysis.median_time_between_commits_hours,
            largestCommitSharePercent=analysis.largest_commit_share_percent,
            top3CommitSharePercent=analysis.top_3_commit_share_percent,
            activityByDay=analysis.commit_activity_by_day or {},
            activityByWeekday=analysis.commit_activity_by_weekday or {},
            sizeDistribution=analysis.commit_size_distribution or {},
            contributors=contributors_out,
        )

    return GitHistoryResponse(
        projectId=analysis.project_id,
        status=analysis.status,
        availability=analysis.availability,
        isShallow=analysis.is_shallow,
        analysisVersion=analysis.analysis_version,
        advisoryNote=analysis.advisory_note,
        summary=summary,
        timeline=commits_out,
        findings=findings_out,
        limitations=analysis.limitations or [],
        createdAt=analysis.created_at,
        updatedAt=analysis.updated_at,
    )


@router.post(
    "/{project_id}/analyze/development-history",
    status_code=status.HTTP_200_OK,
    summary="Analyze Git development history",
)
def analyze_development_history(project_id: str, db: Session = Depends(get_db)):
    """
    Runs or refreshes Git development history analysis for the project.
    Reads the local .git directory inside the safely extracted project directory.
    Read-only. Never executes student code or modifies the repository.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    try:
        analysis = GitHistoryService.analyze_project_git_history(db=db, project_id=project_id)
        return _serialize_git_history_response(analysis)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Git history analysis failed: {str(e)}",
        )


@router.get(
    "/{project_id}/development-history",
    status_code=status.HTTP_200_OK,
    summary="Get Git development history results",
)
def get_development_history(project_id: str, db: Session = Depends(get_db)):
    """
    Returns the latest saved Git history analysis including timeline, summary,
    findings, and limitations.
    """
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )

    analysis = GitHistoryService.get_latest_analysis(db=db, project_id=project_id)
    if not analysis:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        return GitHistoryResponse(
            projectId=project_id,
            status="not_started",
            availability="unavailable",
            isShallow=False,
            analysisVersion="v1.0-git-analysis",
            advisoryNote=(
                "Git development history analysis has not been run for this project yet. "
                "Use POST /api/projects/{project_id}/analyze/development-history to analyze."
            ),
            summary=None,
            timeline=[],
            findings=[],
            limitations=["No Git history analysis has been run for this project yet."],
            createdAt=now,
            updatedAt=now,
        )

    return _serialize_git_history_response(analysis)


# ---------------------------------------------------------------------------
# Final Phase: Overall Evaluation & Comprehensive Report Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/{project_id}/evaluate",
    response_model=ProjectEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Run or refresh overall project evaluation",
)
def evaluate_project(project_id: str, db: Session = Depends(get_db)):
    """Consolidate all analysis results, compute overall score (0-100), and persist evaluation."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    try:
        return EvaluationService.evaluate_project(db=db, project_id=project_id)
    except Exception as exc:
        db.rollback()
        logger.error("Evaluation failed for project '%s': %s", project_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Project evaluation failed: {type(exc).__name__} ({str(exc)})",
        ) from exc


@router.get(
    "/{project_id}/evaluation",
    response_model=ProjectEvaluationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get saved overall evaluation",
)
def get_project_evaluation(project_id: str, db: Session = Depends(get_db)):
    """Retrieve the latest saved overall evaluation for a project."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    evaluation = EvaluationService.get_latest_evaluation(db=db, project_id=project_id)
    if not evaluation:
        # If not evaluated yet, run evaluation dynamically so user gets results
        return EvaluationService.evaluate_project(db=db, project_id=project_id)
    return evaluation


@router.post(
    "/{project_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Request/generate evaluation report",
)
def request_evaluation_report(project_id: str, db: Session = Depends(get_db)):
    """Request formal report generation, ensuring evaluation is up to date."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    eval_res = EvaluationService.evaluate_project(db=db, project_id=project_id)
    return {
        "overallScore": eval_res.overall_score if eval_res.overall_score is not None else 0.0,
        "grade": eval_res.grade,
        "scoreBreakdown": [item.model_dump() for item in eval_res.score_breakdown],
        "facultyNotes": eval_res.faculty_notes,
        "reportAvailable": True,
        "reportUrl": f"/api/projects/{project_id}/report",
        "evaluationStatus": eval_res.evaluation_status,
        "coveragePct": eval_res.coverage_pct,
    }


@router.get(
    "/{project_id}/report",
    status_code=status.HTTP_200_OK,
    summary="Download generated PDF report",
)
def download_evaluation_report(project_id: str, db: Session = Depends(get_db)):
    """Stream generated PDF evaluation report directly to client."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    try:
        pdf_bytes, filename = EvaluationService.generate_pdf(db=db, project_id=project_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except Exception as exc:
        logger.error("PDF generation failed for '%s': %s", project_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF report generation failed: {type(exc).__name__}",
        ) from exc


@router.get(
    "/{project_id}/evaluation/export.json",
    status_code=status.HTTP_200_OK,
    summary="Download evaluation export as JSON",
)
def export_evaluation_json(project_id: str, db: Session = Depends(get_db)):
    """Export normalized evaluation results as downloadable JSON."""
    project = ProjectService.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_id}' not found.",
        )
    data = EvaluationService.generate_json_export(db=db, project_id=project_id)
    safe_fn = sanitize_filename(project.title or project_id)
    import json
    return Response(
        content=json.dumps(data, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{safe_fn}_evaluation.json"'},
    )
