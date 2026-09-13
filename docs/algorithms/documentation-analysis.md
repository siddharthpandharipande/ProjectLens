# Documentation Analysis & Consistency Algorithm Specification

## 1. Input
Markdown documentation (`README.md`) and PDF project reports (`Project_Report.pdf`).

## 2. Text Extraction
- PDF content extracted via PyMuPDF (`fitz`) with page tracking.
- Plain text & Markdown parsed for structure.

## 3. Section Structure Detection
Matches presence of standard academic sections:
- Abstract, Introduction, Problem Statement, Objectives, Methodology, System Architecture, Implementation, Results, Conclusion, References.

## 4. Code ↔ Documentation Consistency (Mismatch Engine)
- Extracts technical claims from documentation (e.g. "XGBoost", "PostgreSQL", "React", "Flask").
- Compares claims against actual detected frameworks and libraries in `ProjectFile` & `ProjectTechnology` tables.
- Emits `IMPLEMENTATION_MISMATCH` finding when documented claim is absent from codebase.

## 5. Scoring Formula
$$S_{\text{doc}} = 0.20 S_{\text{comp}} + 0.20 S_{\text{clarity}} + 0.15 S_{\text{struct}} + 0.25 S_{\text{consistency}} + 0.10 S_{\text{results}} + 0.10 S_{\text{ref}}$$
