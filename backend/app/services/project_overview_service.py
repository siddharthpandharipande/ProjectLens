from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.project_language import ProjectLanguage
from app.models.code_metric import CodeMetric
from app.models.analysis_job import AnalysisJob
from app.services.project_parser import scan_project_files
from app.services.language_detector import (
    calculate_language_distribution,
    detect_technologies_from_evidence,
)
from app.services.code_analyzer import analyze_single_file
from app.services.score_engine import get_evaluation_scores
from app.config import analysis_thresholds as thresholds

def run_project_analysis(db: Session, project: Project, extracted_dir: Path, job: AnalysisJob):
    """
    Executes full static analysis pipeline for a project:
    1. Scan files
    2. Classify & parse each file (handling failures gracefully)
    3. Save files, languages, metrics to database
    4. Update Job progress
    """
    try:
        # Stage 1: File Scanning
        job.current_stage = "Scanning files and structure"
        job.progress = 10
        db.commit()
        
        scanned_files = scan_project_files(extracted_dir)
        
        # Stage 2: Language & Framework Detection
        job.current_stage = "Detecting languages and frameworks"
        job.progress = 30
        db.commit()
        
        languages_data = calculate_language_distribution(scanned_files)
        tech_stack = detect_technologies_from_evidence(extracted_dir, scanned_files)
        
        # Delete old project records if re-analyzing
        db.query(ProjectFile).filter(ProjectFile.project_id == project.id).delete()
        db.query(ProjectLanguage).filter(ProjectLanguage.project_id == project.id).delete()
        db.query(CodeMetric).filter(CodeMetric.project_id == project.id).delete()
        db.commit()
        
        # Save languages
        for lang_item in languages_data:
            pl = ProjectLanguage(
                project_id=project.id,
                language=lang_item["language"],
                file_count=lang_item["file_count"],
                percentage=lang_item["percentage"],
            )
            db.add(pl)
            
        # Stage 3: Code Parsing & Metrics Extraction
        job.current_stage = "Parsing source files and extracting metrics"
        job.progress = 50
        db.commit()
        
        total_loc = 0
        total_code_lines = 0
        total_comment_lines = 0
        total_blank_lines = 0
        total_functions = 0
        total_classes = 0
        complexities: List[float] = []
        
        source_file_count = 0
        test_file_count = 0
        doc_file_count = 0
        failed_files_count = 0
        
        total_files = len(scanned_files)
        
        for idx, sf in enumerate(scanned_files):
            file_metrics = analyze_single_file(
                sf["abs_path"], sf["language"], sf["file_type"]
            )
            
            pf = ProjectFile(
                project_id=project.id,
                path=sf["rel_path"],
                filename=sf["filename"],
                extension=sf["extension"],
                language=sf["language"],
                file_type=sf["file_type"],
                size_bytes=sf["size_bytes"],
                lines_total=file_metrics["lines_total"],
                lines_code=file_metrics["lines_code"],
                lines_comment=file_metrics["lines_comment"],
                lines_blank=file_metrics["lines_blank"],
                parse_status=file_metrics["parse_status"],
                error_message=file_metrics["error_message"],
            )
            db.add(pf)
            
            if file_metrics["parse_status"] == "failed":
                failed_files_count += 1
                
            if sf["file_type"] in {"source", "test"}:
                source_file_count += 1
                total_loc += file_metrics["lines_total"]
                total_code_lines += file_metrics["lines_code"]
                total_comment_lines += file_metrics["lines_comment"]
                total_blank_lines += file_metrics["lines_blank"]
                total_functions += file_metrics["function_count"]
                total_classes += file_metrics["class_count"]
                
                if file_metrics["average_complexity"] > 0:
                    complexities.append(file_metrics["average_complexity"])
                    
            if sf["file_type"] == "test":
                test_file_count += 1
            elif sf["file_type"] == "documentation":
                doc_file_count += 1
                
            # Update progress
            if total_files > 0 and idx % 5 == 0:
                prog = 50 + int((idx / total_files) * 35)
                job.progress = min(prog, 85)
                db.commit()

        # Stage 4: Overview Aggregation
        job.current_stage = "Aggregating code overview metrics"
        job.progress = 90
        db.commit()
        
        avg_complexity = round(sum(complexities) / len(complexities), 1) if complexities else 1.0
        max_complexity = round(max(complexities), 1) if complexities else 1.0
        
        cm = CodeMetric(
            project_id=project.id,
            total_loc=total_loc,
            code_lines=total_code_lines,
            comment_lines=total_comment_lines,
            blank_lines=total_blank_lines,
            source_file_count=source_file_count,
            function_count=total_functions,
            class_count=total_classes,
            average_complexity=avg_complexity,
            maximum_complexity=max_complexity,
            test_file_count=test_file_count,
            documentation_file_count=doc_file_count,
        )
        db.add(cm)
        
        # Complete Job
        project.status = "completed"
        job.status = "completed"
        job.progress = 100
        job.current_stage = "Analysis complete"
        db.commit()
        
    except Exception as e:
        db.rollback()
        project.status = "failed"
        job.status = "failed"
        job.error_message = str(e)
        job.current_stage = "Analysis failed"
        db.commit()
        raise e

def compute_evidence_based_strengths(cm: CodeMetric, tech_stack: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """
    Generate strengths backed ONLY by concrete metric evidence.
    """
    strengths = []
    
    if cm.average_complexity <= thresholds.HIGH_COMPLEXITY:
        strengths.append({
            "title": "Low Average Code Complexity",
            "description": f"Average cyclomatic complexity is {cm.average_complexity}, indicating clean, maintainable logic structures."
        })
        
    if cm.test_file_count > 0:
        strengths.append({
            "title": "Automated Test Suite Detected",
            "description": f"Found {cm.test_file_count} test file(s) in the project structure."
        })
        
    if cm.documentation_file_count >= thresholds.MIN_DOC_FILE_COUNT:
        strengths.append({
            "title": "Project Documentation Included",
            "description": f"Discovered {cm.documentation_file_count} documentation file(s) providing setup and usage details."
        })
        
    if cm.source_file_count >= 5:
        strengths.append({
            "title": "Modular Project Organization",
            "description": f"Source code is organized into {cm.source_file_count} separate files."
        })
        
    return strengths

def compute_evidence_based_improvements(
    cm: CodeMetric, failed_files_count: int
) -> List[Dict[str, str]]:
    """
    Generate areas for improvement backed ONLY by actual findings.
    """
    improvements = []
    
    if cm.average_complexity > thresholds.HIGH_COMPLEXITY:
        improvements.append({
            "title": "High Average Cyclomatic Complexity",
            "description": f"Average complexity is {cm.average_complexity} (threshold: {thresholds.HIGH_COMPLEXITY}). Consider refactoring complex functions."
        })
        
    if cm.test_file_count == 0:
        improvements.append({
            "title": "No Automated Test Files Detected",
            "description": "No unit or integration test files were found in the codebase."
        })
        
    if cm.documentation_file_count == 0:
        improvements.append({
            "title": "Missing Documentation Files",
            "description": "No README or markdown documentation files were detected in the project root."
        })
        
    if failed_files_count > 0:
        improvements.append({
            "title": "Source Files Parser Warnings",
            "description": f"{failed_files_count} file(s) encountered syntax parsing errors during analysis."
        })
        
    return improvements

def build_project_overview_response(db: Session, project: Project) -> Dict[str, Any]:
    """
    Build structured Project Overview response payload matching technical spec.
    """
    # Fetch DB models
    files = db.query(ProjectFile).filter(ProjectFile.project_id == project.id).all()
    languages = db.query(ProjectLanguage).filter(ProjectLanguage.project_id == project.id).all()
    cm = db.query(CodeMetric).filter(CodeMetric.project_id == project.id).first()
    
    total_files_count = len(files)
    failed_files_count = sum(1 for f in files if f.parse_status == "failed")
    
    # Defaults if metrics not yet computed
    total_loc = cm.total_loc if cm else 0
    avg_complexity = cm.average_complexity if cm else 0.0
    max_complexity = cm.maximum_complexity if cm else 0.0
    functions_count = cm.function_count if cm else 0
    classes_count = cm.class_count if cm else 0
    test_files_count = cm.test_file_count if cm else 0
    doc_files_count = cm.documentation_file_count if cm else 0
    comment_lines = cm.comment_lines if cm else 0
    code_lines = cm.code_lines if cm else 0

    # Tech stack from languages & manifests
    scanned_mock = [{"filename": f.filename, "file_type": f.file_type, "language": f.language, "abs_path": Path(f.path)} for f in files]
    tech_stack = detect_technologies_from_evidence(Path("."), scanned_mock)
    
    # Compute strengths & improvements
    strengths = compute_evidence_based_strengths(cm, tech_stack) if cm else []
    improvements = compute_evidence_based_improvements(cm, failed_files_count) if cm else []
    
    # Unimplemented scores interface (returns nulls)
    scores = get_evaluation_scores(project.id)

    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "student_name": project.student_name or "Student Author",
            "course": project.course or "Final Academic Project",
            "status": project.status,
            "created_at": project.created_at.isoformat() if project.created_at else None,
        },
        "summary": {
            "source_files": cm.source_file_count if cm else 0,
            "total_loc": total_loc,
            "languages": len(languages),
            "documentation_files": doc_files_count,
            "test_files": test_files_count,
        },
        "technology_stack": tech_stack,
        "code_metrics": {
            "loc": total_loc,
            "code_lines": code_lines,
            "comment_lines": comment_lines,
            "average_complexity": avg_complexity,
            "maximum_complexity": max_complexity,
            "functions": functions_count,
            "classes": classes_count,
            "test_files": test_files_count,
            "test_coverage": "N/A",  # No coverage report detected
            "ai_assistance": "Pending Analysis",  # Future AI Signals module
        },
        "evaluation": scores,
        "strengths": strengths,
        "improvements": improvements,
        "analysis": {
            "status": project.status,
            "files_analyzed": total_files_count - failed_files_count,
            "files_failed": failed_files_count,
            "total_files": total_files_count,
        }
    }
