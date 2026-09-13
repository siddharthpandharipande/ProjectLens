from typing import Dict, Any, Optional, List
from app.models.code_metric import CodeMetric
from app.services.technical_execution_analyzer import analyze_technical_execution
from app.services.documentation_analyzer import analyze_documentation_integrity
from app.services.git_analyzer import analyze_development_process
from app.services.originality_analyzer import analyze_originality

def calculate_evaluation_scores(
    cm: Optional[CodeMetric],
    scanned_files: List[Dict[str, Any]],
    extracted_dir: Any,
    tech_stack: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Computes deterministic, evidence-backed evaluation scores for all 4 core dimensions:
    - Technical Execution
    - Documentation Integrity
    - Development Process
    - Originality
    """
    file_types = [sf.get("file_type") for sf in scanned_files]

    # 1. Technical Execution
    tech_exec_res = analyze_technical_execution(cm, file_types) if cm else {
        "score": None, "status": "Pending", "evidence": ["Code metrics pending analysis."], "breakdown": {}
    }

    # 2. Documentation Integrity
    doc_res = analyze_documentation_integrity(scanned_files)

    # 3. Development Process
    git_res = analyze_development_process(extracted_dir)

    # 4. Originality Evaluation
    orig_res = analyze_originality(cm, scanned_files, tech_stack or [], doc_res) if cm else {
        "score": None, "status": "Pending", "evidence": ["Code metrics pending analysis."], "breakdown": {}
    }

    # 5. Overall Score (Derived transparently from available numerical scores)
    valid_scores = []
    if tech_exec_res.get("score") is not None:
        valid_scores.append(tech_exec_res["score"])
    if doc_res.get("score") is not None:
        valid_scores.append(doc_res["score"])
    if git_res.get("score") is not None:
        valid_scores.append(git_res["score"])
    if orig_res.get("score") is not None:
        valid_scores.append(orig_res["score"])

    if valid_scores:
        overall_val = round(sum(valid_scores) / len(valid_scores), 1)
        overall_status = f"Based on {len(valid_scores)} of 4 evaluation dimensions"
    else:
        overall_val = None
        overall_status = "Evaluation Pending"

    return {
        "overall_score": overall_val,
        "overall_status": overall_status,
        "technical_execution": tech_exec_res.get("score"),
        "technical_execution_detail": tech_exec_res,
        "documentation_integrity": doc_res.get("score"),
        "documentation_integrity_detail": doc_res,
        "development_process": git_res.get("score"),
        "development_process_detail": git_res,
        "originality": orig_res.get("score"),
        "originality_detail": orig_res,
    }
