from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.project import Project
from app.models.project_file import ProjectFile
from app.models.project_technology import ProjectTechnology
from app.services.doc_structure import analyze_documentation_structure
from app.services.consistency_analyzer import analyze_code_doc_consistency

def analyze_project_documentation(db: Session, project: Project) -> Dict[str, Any]:
    """
    Executes Phase 5 Documentation Analysis: README & PDF extraction, section coverage,
    and Code ↔ Documentation Consistency analysis.
    """
    doc_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project.id,
        ProjectFile.file_type == "documentation"
    ).all()

    techs = db.query(ProjectTechnology).filter(ProjectTechnology.project_id == project.id).all()
    tech_list = [{"name": t.name} for t in techs]

    source_files = db.query(ProjectFile).filter(
        ProjectFile.project_id == project.id,
        ProjectFile.file_type.in_(["source", "test"])
    ).all()
    source_content = "\n".join([sf.content or "" for sf in source_files])

    combined_doc_text = ""
    for df in doc_files:
        if df.content:
            combined_doc_text += f"\n--- {df.filename} ---\n" + df.content

    structure = analyze_documentation_structure(combined_doc_text)
    consistency = analyze_code_doc_consistency(combined_doc_text, tech_list, source_content)

    completeness_score = structure["coverage_percentage"]
    clarity_score = 85.0 if len(combined_doc_text) > 200 else 50.0
    structure_score = round((structure["detected_count"] / max(1, structure["total_count"])) * 100, 1)
    consistency_score = consistency["consistency_score"]
    results_score = 88.0 if "results" in structure["sections_detected"] and structure["sections_detected"]["results"] else 40.0
    references_score = 100.0 if "references" in structure["sections_detected"] and structure["sections_detected"]["references"] else 0.0

    # Configurable weighted documentation score
    overall_score = round(
        (completeness_score * 0.20) +
        (clarity_score * 0.20) +
        (structure_score * 0.15) +
        (consistency_score * 0.25) +
        (results_score * 0.10) +
        (references_score * 0.10),
        1
    )

    return {
        "project_id": project.id,
        "overall_score": overall_score,
        "subscores": {
            "completeness": completeness_score,
            "clarity": clarity_score,
            "structure": structure_score,
            "consistency": consistency_score,
            "results": results_score,
            "references": references_score,
        },
        "doc_file_count": len(doc_files),
        "structure": structure,
        "mismatches": consistency["mismatches"],
        "matched_claims": consistency["matched_claims"],
    }
