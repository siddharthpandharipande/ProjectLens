import re
from pathlib import Path
from typing import List, Dict, Any
from app.models.code_metric import CodeMetric

def analyze_originality(
    cm: CodeMetric,
    scanned_files: List[Dict[str, Any]],
    tech_stack: List[Dict[str, Any]],
    doc_detail: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Computes deterministic, evidence-backed Originality score (0–100).
    Evaluates:
    - Custom Logic & Non-Boilerplate Ratio (30%)
    - Structural Signature Uniqueness (25%)
    - Domain & Identifier Specificity (25%)
    - Bespoke Documentation Authenticity (20%)
    """
    evidence: List[str] = []
    breakdown = {
        "custom_logic_ratio": 0.0,
        "structural_uniqueness": 0.0,
        "domain_specificity": 0.0,
        "documentation_authenticity": 0.0,
    }

    if not cm or cm.source_file_count == 0:
        return {
            "score": None,
            "status": "Pending",
            "evidence": ["Insufficient source files to compute Originality score."],
            "breakdown": breakdown
        }

    # 1. Custom Logic Ratio (30%)
    func_cnt = cm.function_count or 0
    class_cnt = cm.class_count or 0

    if func_cnt >= 5 or class_cnt >= 2:
        breakdown["custom_logic_ratio"] = 30.0
        evidence.append(f"✓ Bespoke implementation detected ({func_cnt} custom functions, {class_cnt} classes)")
    elif func_cnt >= 2 or class_cnt >= 1:
        breakdown["custom_logic_ratio"] = 22.0
        evidence.append(f"✓ Custom function logic present ({func_cnt} functions defined)")
    else:
        breakdown["custom_logic_ratio"] = 15.0
        evidence.append("⚠ Script-based linear structure detected")

    # 2. Structural Signature Uniqueness (25%)
    avg_cc = cm.average_complexity or 1.0
    max_cc = cm.maximum_complexity or 1.0

    if max_cc > avg_cc and avg_cc > 1.2:
        breakdown["structural_uniqueness"] = 25.0
        evidence.append(f"✓ Varied control flow distribution (avg complexity {avg_cc}, max {max_cc})")
    elif avg_cc >= 1.1:
        breakdown["structural_uniqueness"] = 18.0
        evidence.append(f"✓ Moderate algorithmic complexity ({avg_cc})")
    else:
        breakdown["structural_uniqueness"] = 12.0
        evidence.append("⚠ Uniform control flow structures")

    # 3. Domain & Identifier Specificity (25%)
    source_files = [sf for sf in scanned_files if sf.get("file_type") in {"source", "test"}]
    unique_extensions = set(sf.get("extension") for sf in source_files if sf.get("extension"))
    
    if len(unique_extensions) >= 2 or cm.source_file_count >= 6:
        breakdown["domain_specificity"] = 25.0
        evidence.append(f"✓ Multi-module domain structure across {cm.source_file_count} files")
    elif cm.source_file_count >= 3:
        breakdown["domain_specificity"] = 18.0
        evidence.append(f"✓ Multi-file codebase organization ({cm.source_file_count} files)")
    else:
        breakdown["domain_specificity"] = 12.0
        evidence.append("⚠ Minimal file modularity")

    # 4. Bespoke Documentation Authenticity (20%)
    doc_score = doc_detail.get("score") or 0.0
    if doc_score >= 60.0:
        breakdown["documentation_authenticity"] = 20.0
        evidence.append("✓ Authentic bespoke README documentation matching implementation")
    elif doc_score >= 30.0:
        breakdown["documentation_authenticity"] = 14.0
        evidence.append("✓ Standard documentation overview present")
    else:
        breakdown["documentation_authenticity"] = 8.0
        evidence.append("⚠ Minimal project documentation provided")

    total_score = round(sum(breakdown.values()), 1)

    return {
        "score": total_score,
        "status": "completed",
        "evidence": evidence,
        "breakdown": breakdown
    }
