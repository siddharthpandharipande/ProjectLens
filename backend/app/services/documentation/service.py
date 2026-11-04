import os
from pathlib import Path
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectFile, ProjectStructure
from app.models.documentation import (
    ProjectDocumentationAnalysis,
    ProjectDocumentItem,
    ProjectDocumentationFinding,
)
from app.services.project_parser import ProjectParser
from app.services.documentation.extractor import DocumentExtractor, ExtractedDocument
from app.services.documentation.analyzer import DocumentationAnalyzer
from app.services.documentation.consistency import ConsistencyAnalyzer


class DocumentationService:
    """
    Orchestration service for Phase 5 Documentation Analysis and
    Code-Documentation Consistency checks.
    Manages safe file extraction, analysis, scoring, and atomic idempotent
    persistence into PostgreSQL.
    """

    @classmethod
    def get_project_documentation(
        cls, db: Session, project_id: str
    ) -> Optional[ProjectDocumentationAnalysis]:
        """
        Retrieves the latest saved documentation analysis for a project.
        """
        return (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .order_by(ProjectDocumentationAnalysis.created_at.desc())
            .first()
        )

    @classmethod
    def analyze_project(
        cls, db: Session, project_id: str
    ) -> ProjectDocumentationAnalysis:
        """
        Executes or refreshes documentation analysis and code-documentation
        consistency checks for a project.
        Atomic and idempotent: cleans up prior documentation records for this project.
        """
        # 1. Verify project exists
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project '{project_id}' not found.",
            )

        # 2. Ensure project is extracted
        project_dir = ProjectParser.get_project_extract_dir(project_id)
        if not project_dir.exists() or not any(project_dir.iterdir()):
            if project.archive_path and Path(project.archive_path).exists():
                project_dir = ProjectParser.extract_zip_archive(project.archive_path, project_id)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Project source files are not extracted and archive is missing for '{project_id}'.",
                )

        # 3. Retrieve database records for files and structure
        structure = db.query(ProjectStructure).filter(ProjectStructure.project_id == project_id).first()
        files = db.query(ProjectFile).filter(ProjectFile.project_id == project_id).all()

        # 4. Discover documentation files
        db_doc_rel_paths = [
            f.relative_path
            for f in files
            if f.category == "Documentation"
            or f.extension.lower() in {".md", ".markdown", ".rst", ".pdf", ".docx", ".txt"}
        ]
        discovered_docs = DocumentExtractor.discover_documents(
            project_dir=project_dir, relative_paths=db_doc_rel_paths
        )

        # 5. Extract text and structure from each document
        extracted_docs: List[ExtractedDocument] = []
        for full_p, rel_p in discovered_docs:
            extracted_doc = DocumentExtractor.extract(full_path=full_p, relative_path=rel_p)
            extracted_docs.append(extracted_doc)

        # 6. Analyze documents and calculate metrics & preliminary score
        (
            metrics,
            section_coverage,
            preliminary_score,
            score_explanation,
            quality_findings,
            extraction_warnings,
        ) = DocumentationAnalyzer.analyze_documents(documents=extracted_docs)

        # 7. Run code-documentation consistency checks
        consistency_findings = ConsistencyAnalyzer.analyze(
            documents=extracted_docs,
            structure=structure,
            files=files,
            project_dir=project_dir,
        )

        all_findings = quality_findings + consistency_findings

        # 8. Determine overall status and limitations
        if not extracted_docs or metrics.total_words < 50:
            analysis_status = "insufficient_evidence"
            limitations = [
                "Total extractable documentation across the project is minimal or absent.",
                "Student code is not executed during analysis; runtime consistency cannot be guaranteed.",
            ]
        else:
            analysis_status = "completed"
            limitations = [
                "Static analysis only: student code is not executed.",
                "Numerical claims and benchmarks require faculty verification during viva.",
                "Preliminary documentation score is an advisory rubric and not a final evaluation grade.",
            ]

        # 9. Idempotent database storage: delete existing analysis for this project
        existing_analyses = (
            db.query(ProjectDocumentationAnalysis)
            .filter(ProjectDocumentationAnalysis.project_id == project_id)
            .all()
        )
        for old in existing_analyses:
            db.delete(old)
        db.flush()

        # 10. Persist new analysis record
        new_analysis = ProjectDocumentationAnalysis(
            project_id=project_id,
            status=analysis_status,
            preliminary_score=preliminary_score,
            scoring_version="v1.0-deterministic-rubric",
            factors_explanation=score_explanation,
            metrics_summary=metrics.model_dump(by_alias=True),
            section_coverage=[item.model_dump(by_alias=True) for item in section_coverage],
            total_documents_count=len(extracted_docs),
            total_words_count=metrics.total_words,
            recognized_sections_count=metrics.recognized_sections_count,
            extraction_warnings=extraction_warnings,
            limitations=limitations,
        )
        db.add(new_analysis)
        db.flush()  # Populates new_analysis.id

        # 11. Persist document items
        for doc in extracted_docs:
            doc_item = ProjectDocumentItem(
                analysis_id=new_analysis.id,
                project_id=project_id,
                relative_path=doc.relative_path,
                filename=doc.filename,
                file_format=doc.file_format,
                extracted_word_count=doc.word_count,
                extracted_char_count=doc.char_count,
                page_count=doc.page_count,
                sections_found=doc.headings,
                extraction_status=doc.status,
                warning_message=doc.warning,
            )
            db.add(doc_item)

        # 12. Persist findings
        for f in all_findings:
            finding_item = ProjectDocumentationFinding(
                analysis_id=new_analysis.id,
                project_id=project_id,
                rule_id=f["rule_id"],
                title=f["title"],
                severity=f["severity"],
                category=f["category"],
                explanation=f["explanation"],
                doc_path=f.get("doc_path"),
                location_ref=f.get("location_ref"),
                documented_claim=f.get("documented_claim"),
                code_evidence=f.get("code_evidence"),
                verification_status=f["verification_status"],
                faculty_guidance=f.get("faculty_guidance"),
            )
            db.add(finding_item)

        db.commit()
        db.refresh(new_analysis)
        return new_analysis
