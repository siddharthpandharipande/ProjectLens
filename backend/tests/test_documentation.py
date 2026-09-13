import pytest
from app.services.doc_structure import analyze_documentation_structure
from app.services.consistency_analyzer import analyze_code_doc_consistency

def test_doc_structure_analysis():
    text = "# Abstract\nThis project implements XGBoost.\n# Introduction\nDetails here.\n# Methodology\nModel training.\n# Results\n95% accuracy.\n"
    res = analyze_documentation_structure(text)
    assert res["sections_detected"]["abstract"] is True
    assert res["sections_detected"]["introduction"] is True
    assert res["sections_detected"]["results"] is True

def test_code_doc_consistency_mismatch():
    doc_text = "We use XGBoost and PostgreSQL for high throughput data storage."
    detected_techs = [{"name": "RandomForest"}]
    source_content = "import random\ndef train(): pass"
    
    res = analyze_code_doc_consistency(doc_text, detected_techs, source_content)
    assert len(res["mismatches"]) >= 1
    mismatch_claims = [m["claim"] for m in res["mismatches"]]
    assert "XGBoost" in mismatch_claims or "PostgreSQL" in mismatch_claims
