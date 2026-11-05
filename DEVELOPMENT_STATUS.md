# ProjectLens — Development Status Tracker

*Last Updated: Final Phase (Overall Project Evaluation & Comprehensive Report Generator)*

---

## Evaluation Capabilities Matrix

| # | Capability | Description | Status | Verification & Test Coverage |
|---|------------|-------------|--------|------------------------------|
| **1** | **Project Parser** | Unpacks ZIP submissions, detects root directory, validates archives, extracts file catalog. | **COMPLETE** | 10 unit tests passing (`tests/test_parser.py`) |
| **2** | **Language & File Analyzer** | Classifies files by extension, language, LOC, size, and source categorization. | **COMPLETE** | Integrated in parser test suite |
| **3** | **Code Quality Analyzer** | AST-based cyclomatic complexity, code smells, function length, class hierarchy, quality score. | **COMPLETE** | 9 unit tests passing (`tests/test_code_quality.py`) |
| **4** | **Code Similarity Analyzer** | Token Jaccard overlap, AST subtree hashing, candidate peer comparison within cohort. | **COMPLETE** | 17 unit tests passing (`tests/test_similarity.py`) |
| **5** | **Documentation Analyzer** | Text extraction from PDF, DOCX, Markdown; section coverage; claim extraction; doc-to-code consistency. | **COMPLETE** | 13 unit tests passing (`tests/test_documentation.py`) |
| **6** | **Development History Analyzer** | Commit tempo, velocity spikes, single-batch dumps, author distribution, shallow history detection. | **COMPLETE** | 12 unit tests passing (`tests/test_git_history.py`) |
| **7** | **AI-Assistance Analyzer** | 26 deterministic signals, Google Gemini 2.5 Flash grounded interpretation, 10 key assistance areas, structured actionable findings with priority tags & viva readiness. | **COMPLETE (PHASE 9)** | 25 unit tests passing (`tests/test_ai_assistance.py`) |
| **8** | **Innovation Analyzer** | 5 feature classes detection, Google Gemini 2.5 Flash interpretation, cohort differentiation, transparent Confidence Classifications with explicit rationale, enriched strengths & gaps. | **COMPLETE (PHASE 9)** | 32 unit tests passing (`tests/test_innovation.py`) |
| **9** | **Viva Question Generator** | Intelligent examiner-style viva question generation using Google Gemini AI (`gemini-2.5-flash`), 4 modes, 9 categories, 3 difficulties, practice tracking, and deterministic fallback. | **COMPLETE (PHASE 8)** | 22 unit tests passing (`tests/test_viva.py`) |
| **10** | **Evaluation & Scoring Engine** | Multi-dimensional 6-category weighted rubric scoring model (Code Quality 30%, Similarity 15%, Documentation 20%, Git 10%, Innovation 15%, Engineering Rigor 10%), dynamic weight renormalization, letter grades (A–F), and honest coverage thresholds (<50% incomplete, 50-70% provisional, >=70% complete). | **COMPLETE (FINAL PHASE)** | 13 unit tests passing (`tests/test_evaluation.py`) |
| **11** | **Report & Faculty Dashboard** | Neo-Brutalist interactive dashboard (Tab 7), publication-grade ReportLab PDF generator (`#FAF6EE`, `#121212`, `#FFE600`, NumberedCanvas "Page X of Y"), JSON export, and faculty advisory banner. | **COMPLETE (FINAL PHASE)** | Production build verified (`tsc -b && vite build`) |

---

## Final Phase: Overall Evaluation Engine & Comprehensive Report Generator Highlights

1. **Deterministic Multi-Category Rubric Scoring Engine**:
   - 6 Core Categories summing to 100%:
     - **Code Quality & Engineering Standards** (30%)
     - **Code Similarity & Originality** (15%)
     - **Project Documentation & Alignment** (20%)
     - **Git Development History & Authenticity** (10%)
     - **Innovation & Technical Distinction** (15%)
     - **Engineering Rigor & Viva Readiness** (10%)
   - **Dynamic Weight Renormalization**: Missing/unassessed categories (e.g. clean student ZIP without Git history) do not unfairly penalize students as zero scores; active weights renormalize proportionally over assessed categories.
   - **Letter Grade Scale**:
     - `A`: 85.0 – 100.0 (Exceptional)
     - `B+`: 75.0 – 84.9 (Very Good)
     - `B`: 65.0 – 74.9 (Good / Competent)
     - `C`: 50.0 – 64.9 (Adequate / Pass)
     - `D`: 35.0 – 49.9 (Marginal / Needs Defense)
     - `F`: < 35.0 (Unsatisfactory)
   - **Honest Coverage Thresholds**:
     - `< 50.0%`: `incomplete` / Insufficient Evidence (numeric score withheld).
     - `50.0% – 69.9%`: `partial` / Provisional Evaluation Score.
     - `>= 70.0%`: `complete` / Certified Overall Score.

2. **Publication-Grade PDF Evaluation Report (ReportLab)**:
   - Adheres strictly to Neo-Brutalist design tokens: `#FAF6EE` canvas, `#121212` borders, `#FFE600` accent headers.
   - Two-pass `NumberedCanvas` rendering "Page X of Y" with document identification header.
   - Comprehensive content sections:
     1. Executive Header & Score/Grade Banner
     2. Multi-Dimensional Rubric Score Breakdown Table
     3. Key Technical Strengths
     4. Identified Weaknesses & Architecture Gaps
     5. Viva Defense Risk Advisory
     6. Prioritized Action Plan & Improvement Recommendations Table
     7. Sample Viva Voce Defense Questions (Examiner Focus)
     8. Academic Integrity & Faculty Advisory Disclaimer

3. **Machine-Readable JSON Export**:
   - Accessible via `GET /api/projects/{id}/evaluation/export.json` and in the frontend workspace.
   - Exports complete serialized project metadata, category breakdowns, strengths, weaknesses, risks, and recommendations.

4. **Interactive Neo-Brutalist Frontend Workspace (Tab 7 & Global Header)**:
   - Executive scorecard with overall score `/100`, grade chip, status badge, and assessed coverage indicator.
   - Multi-dimensional breakdown grid with progress bars and contribution points.
   - Tri-pillar synthesis layout (Strengths, Weaknesses, Viva Risks).
   - Prioritized Action Plan cards with priority chips (`Critical`, `High`, `Medium`, `Low`).
   - One-click buttons for "Run / Re-Evaluate Project", "Download Formal PDF Report", and "JSON Export".
   - Fixes empty `/100` glitch in the top workspace card before evaluation is executed.

---

## Phase 9 AI Assistance & Innovation Analyzer Highlights

1. **Unified Google Gemini AI Integration**:
   - Standardized on Google Gen AI SDK (`google-genai`) with model `gemini-2.5-flash`.
   - Native structured JSON output mode with strict Pydantic parsing and pre-validation normalizers.
   - Zero `TypeError: sequence item ... NoneType found` across all prompt templates and dictionary lookups.
   - Comprehensive exception mapping (`401/403` Auth, `429` Rate Limit, `503` Unavailable, Timeout) with provider-aware UI banners.

2. **AI Assistance Analyzer Refinement**:
   - Grounded context synthesis encompassing Project Overview, Architecture, Code Quality, Tech Stack, Documentation, Testing Gaps, Security & Performance, Missing Evidence, Actionable Recommendations, and Viva Readiness.
   - Actionable findings schema (`title`, `description`, `category`, `priority`, `why_it_matters`, `supporting_evidence`, `recommended_action`, `expected_benefit`, `source_reference`).
   - Summary-first interactive UI with priority badges (`Critical`, `High`, `Medium`, `Low`, `Informational`), category filter buttons, and expandable recommendation cards.
   - Complete deterministic fallback: when offline or rate-limited, generates comprehensive findings across all 10 areas from AST and document metrics.

3. **Innovation Analyzer Refinement**:
   - Distinct 5 feature classes:
     - `verified_match`: Verified Implemented Features (present in docs and verified in source code).
     - `documented_feature`: Documented Features (claimed with partial code presence).
     - `detected_implementation`: Detected Code Components (implemented in code without explicit doc claims).
     - `unverified_claim`: Claimed but Unverified (claimed in docs with zero code match).
     - `proposed_future`: Proposed / Future Scope (explicitly documented as future work/roadmap).
   - Transparent Confidence Classifications: `Directly Verified`, `Strong Evidence`, `Moderate Evidence`, `Indirect Evidence`, `Unverified`, `Insufficient Evidence` with human-readable rationale.
   - Enriched Section E blocks: Key Innovation Strengths, Missing Evidence & Blind Spots, and Prioritized Recommendations for Improvement.

---

## Phase 8 Viva Question Generator Highlights

1. **Google Gemini API Integration**:
   - Integrates official Google Gen AI Python SDK (`google-genai`).
   - Uses `gemini-2.5-flash` model with structured JSON responses adhering to strict Pydantic schemas.
   - Grounded strictly in factual project evidence (languages, frameworks, code quality metrics, documentation claims, and identified blind spots).
2. **Four Generation Modes**:
   - **Quick Preparation**: Concise set of high-probability core viva questions.
   - **Complete Viva**: Comprehensive 9-category question set with balanced difficulty.
   - **Technical Deep Dive**: Code-level deep dive on algorithms, databases, complexity, and key files.
   - **Examiner Challenge**: Probing questions on architectural trade-offs, scalability, and missing testing/docs.
3. **Question & Answer Format**:
   - Question text, category, difficulty badge, examiner rationale ("Why an examiner asks this"), key expected answer points, full suggested answer, and evidence references.
4. **Practice & Progress Tracking**:
   - Students can mark questions as practiced with persistent database storage.
   - Live progress indicator with category/difficulty mastery breakdown.
   - Filter by status (`All`, `To Practice`, `Practiced`) and category.
5. **Deterministic Fallback Generator**:
   - 100% offline resilience when Gemini is unconfigured or rate limited.
   - Generates project-personalized questions from AST metrics, tech stack, and documentation gaps.
   - Labeled transparently as `Deterministic Fallback`.

---

## Test Suite Summary
- **Backend**: 156 passed across 11 test files in 40.31s (`pytest backend/tests`).
- **Frontend**: 0 build errors (`tsc -b && vite build` bundled in 1.41s).
- **Live Gemini Verification**: Successfully executed live API calls for Viva Generator, AI Assistance, and Innovation Analyzer using `gemini-2.5-flash`.

