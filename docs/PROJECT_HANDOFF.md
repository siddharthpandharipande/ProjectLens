# ProjectLens — Developer Handoff Specification (Phase 9)

## 1. Project Overview & Mission

**ProjectLens** is an AI-powered college software project evaluation assistant tailored for academic faculty, evaluators, and viva panels. It helps faculty objectively evaluate student project submissions by parsing project archives, computing deterministic code quality and similarity metrics, auditing documentation claims against implementation evidence, analyzing git development timelines, performing cohort innovation comparisons, and generating personalized examiner viva questions.

### Core Philosophy
- **Evaluator Assistance, Not Automated Adjudication**: ProjectLens provides analytical screening signals and diagnostic aids. It **never** computes or displays an automated "AI probability score", "plagiarism percentage", or misconduct verdict.
- **Deterministic-First Resilience**: All evaluation features (parsing, AST analysis, token Jaccard similarity, doc coverage, git velocity, innovation profile extraction, and cohort comparison) function fully deterministically without requiring external API keys.
- **Google Gemini AI with Resilient Fallback**: Uses Google Gen AI SDK (`gemini-2.5-flash`) for deep qualitative synthesis (Viva Questions, AI Assistance, Innovation Analyzer). When unavailable or rate-limited, the platform gracefully falls back to deterministic analysis with zero downtime.
- **Neo-Brutalist Academic Aesthetics**: High-contrast, utilitarian design with cream `#FAF6EE` canvas, `#121212` borders, hard drop shadows (`4px 4px 0px #121212`), high-visibility status chips, and crisp tabular data.

---

## 2. Technology Stack

### Backend
- **Python**: 3.14+
- **FastAPI**: 0.115+ (REST API, Pydantic v2 schemas, CORS middleware)
- **Database**: PostgreSQL 16/17 (via SQLAlchemy 2.0 + Psycopg 3 binary driver)
- **Parsing & Static Analysis**: Python standard `ast`, tree-sitter bindings, `zipfile` archive extraction
- **Text & NLP**: `scikit-learn` (TF-IDF vectorizer, cosine similarity), `pypdf`, `python-docx`, `markdown`
- **Testing**: `pytest`, `pytest-asyncio`, `anyio` (156 unit & integration tests)

### Frontend
- **React**: 19.x (Functional components, custom hooks)
- **TypeScript**: 5.x (Strict typing across all models and API responses)
- **Bundler & Tooling**: Vite 8.x
- **Styling**: Tailwind CSS v4 (Neo-Brutalist token set)
- **Icons**: Lucide Icons
- **Routing**: React Router DOM v7

### AI & LLM Service
- **Primary Provider**: Google Gemini API (`gemini-2.5-flash` via `google-genai` SDK)
- **Secondary Provider**: OpenRouter API (`https://openrouter.ai/api/v1`)
- **Fallback Behavior**: Resilient error handling with exception mapping, rate-limit notifications, and deterministic fallback generators

---

## 3. Evaluation Capabilities Status Matrix

The project is structured around 11 core capabilities:

| # | Capability | Implementation Status | Test Coverage | Key Modules |
|---|------------|----------------------|---------------|-------------|
| 1 | **Project Parser** | Implemented & Production-Ready | 10 tests | `backend/app/services/parser.py` |
| 2 | **Language & File Analyzer** | Implemented & Production-Ready | Included in Parser | `backend/app/services/parser.py` |
| 3 | **Code Quality Analyzer** | Implemented & Production-Ready | 9 tests | `backend/app/services/code_quality/` |
| 4 | **Code Similarity Analyzer** | Implemented & Production-Ready | 17 tests | `backend/app/services/similarity/` |
| 5 | **Documentation Analyzer** | Implemented & Production-Ready | 13 tests | `backend/app/services/documentation/` |
| 6 | **Development History Analyzer** | Implemented & Production-Ready | 12 tests | `backend/app/services/git_history/` |
| 7 | **AI-Assistance Analyzer** | Implemented & Refined (Phase 9) | 25 tests | `backend/app/services/ai_assistance/` |
| 8 | **Innovation Analyzer** | Implemented & Refined (Phase 9) | 32 tests | `backend/app/services/innovation/` |
| 9 | **Viva Question Generator** | Implemented (Phase 8 Gemini + Fallback) | 22 tests | `backend/app/services/viva/` |
| 10 | **Evaluation & Scoring Engine** | Fully Implemented (Final Phase) | 13 tests | `backend/app/services/evaluation/` |
| 11 | **Faculty Report & Dashboard** | Fully Implemented (Final Phase) | 172 backend tests + Frontend build clean | `projectlens-frontend/src/pages/ProjectWorkspacePage.tsx` |

---

## 4. Phase 7C Architecture Audit & Refinement Details

### 4.1 Innovation Analyzer Backend Audit (`backend/app/services/innovation/`)
- **Profile Extractor (`extractor.py`)**:
  - Filtered out heading-only stubs (`"About"`, `"Overview"`, `"Introduction"`, `"Project Description"`).
  - Added `is_meaningful_description()` validator rejecting generic descriptions, single words, shell commands (`git clone`, `npm install`), and headings.
  - When meaningful text cannot be extracted from project documentation, falls back cleanly to `"Not identified from the available project documents."` instead of inventing fictional descriptions.
  - Improved feature classification: Distinguishes between documented claims (`documented_feature`), verified implementations (`verified_match`), and internal code components (`detected_implementation` prefixed with `"Code Component: "` to avoid claiming a source file is a user-facing feature).
- **Cohort Comparison (`cohort_comparison.py`)**:
  - Replaced internal raw directory UUIDs/hashes with formatted titles (`format_cohort_project_title`), disambiguating duplicate project names with short identifiers.
  - Added duplicate submission screening detection (`similarity >= 0.85` or `0.95` flagged as `"Potential exact duplicate submission detected"`).
  - Explicitly marked all cohort similarity metrics with advisory screening disclaimers.
- **Scoring Engine (`scoring.py`)**:
  - Audited all 5 dimension formulas (`problem_distinctiveness`, `solution_distinctiveness`, `feature_differentiation`, `technical_contribution`, `supporting_evidence_strength`).
  - Missing problem statements, missing proposed solutions, or empty cohorts now yield `None` (rendered as `"Insufficient Evidence"`) rather than misleading `100%` or `0%` scores.

### 4.2 AI Assistance UI Refinement (`projectlens-frontend/src/pages/ProjectWorkspacePage.tsx`)
- **Summary-First Design**:
  - Compact 6-metric summary ribbon at top: Analysis Status, Total Signals, Available Signals, Unavailable Signals, Active Sources, LLM Interpretation Status.
- **Prioritized Main Findings**:
  - Top 4 highlighted findings across Code Quality, Similarity, Documentation, and Git History displayed initially in compact cards.
- **Compact Expandable Source Accordions**:
  - 4 module accordions (Code Quality, Similarity, Documentation, Git History) initially collapsed to reduce scrolling.
  - Per-signal toggle to inspect alternative explanations and benign context.
- **Interactive Evidence Filters**:
  - Filters by status (`All`, `Available`, `Unavailable`) and source module (`Code Quality`, `Similarity`, `Documentation`, `Git History`).
- **Honest Heuristic Strength Badges**:
  - Replaced misleading numerical confidence percentages (`85%`) with honest labels (`Direct Metric`, `Strong Heuristic`, `Moderate Heuristic`, `Indirect Signal`).

### 4.3 Resilient OpenRouter Rate-Limit Handling
- Upstream HTTP 429 rate-limit responses consolidated into a single compact notification banner with collapsible error details and a small retry action, preventing repetitive banner spam.

### 4.4 Phase 8 Intelligent Viva Question Generator with Google Gemini AI
- **Google Gen AI SDK Integration**:
  - Direct integration with official `google-genai` SDK using `gemini-2.5-flash`.
  - Securely configured from `backend/.env` with `GEMINI_API_KEY` and fallback handling.
- **Nine Viva Categories & Three Difficulties**:
  - Project Fundamentals, Technical Architecture, Technology Stack, Implementation and Coding, Innovation and Uniqueness, Testing and Validation, Critical Thinking, Technical Deep Dive, and Future Scope.
  - Beginner, Intermediate, and Advanced difficulty levels.
- **Four Viva Generation Modes**:
  - Quick Preparation, Complete Viva, Technical Deep Dive, and Examiner Challenge.
- **Practice Tracking & Database Persistence**:
  - Questions and question sets stored in PostgreSQL (`project_viva_question_sets`, `project_viva_questions`).
  - Interactive practice toggle, difficulty mastery breakdown, and single-question regeneration.
- **Deterministic Fallback Generator**:
  - 100% offline fallback using AST metrics, tech stack, and documentation gaps when Gemini is unconfigured or rate limited.

### 4.5 Phase 9 AI Assistance & Innovation Analyzer Gemini Refinement
- **Unified Gemini 2.5 Flash SDK Integration**:
  - `LLMClient` enhanced with `_interpret_evidence_gemini` and `_interpret_innovation_gemini` using `google-genai` SDK and `gemini-2.5-flash`.
  - Pydantic pre-validation schemas guarantee null safety and normalize status casing and structured evidence strings.
  - Granular error mapping: maps 401/403 to `LLMAuthenticationError`, 429 to `LLMRateLimitError`, 503 to `LLMProviderUnavailableError`, and timeouts to `LLMTimeoutError`.
- **AI Assistance Actionable Recommendations**:
  - Synthesizes 10 key project dimensions: Project Overview, Architecture, Code Quality, Tech Stack, Documentation, Testing Gaps, Security & Performance, Missing Evidence, Actionable Recommendations, and Viva Readiness.
  - Actionable findings schema (`title`, `description`, `category`, `priority`, `why_it_matters`, `supporting_evidence`, `recommended_action`, `expected_benefit`, `source_reference`).
  - Interactive UI with priority filtering (`Critical`, `High`, `Medium`, `Low`, `Informational`) and expandable recommendation cards.
  - 100% deterministic fallback findings generation if offline or rate-limited.
- **Innovation 5 Feature Classes & Confidence Classifications**:
  - 5 feature classes: `verified_match`, `documented_feature`, `detected_implementation`, `unverified_claim`, and `proposed_future`.
  - Transparent Confidence Classifications: `Directly Verified`, `Strong Evidence`, `Moderate Evidence`, `Indirect Evidence`, `Unverified`, `Insufficient Evidence` with explicit human-readable rationale.
  - Enriched Section E blocks: Key Innovation Strengths, Missing Evidence & Blind Spots, and Prioritized Recommendations for Improvement.

---

## 5. Running the Application Locally (Windows PowerShell)

### Prerequisites
1. **Python**: 3.14 (or 3.11+)
2. **Node.js**: 20+ with npm
3. **PostgreSQL**: 16 or 17 running on `localhost:5432`

### Step 1: PostgreSQL Setup
```powershell
# Verify PostgreSQL service is running
Get-Service -Name "*postgres*"

# Create projectlens database (if not already created)
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres -h localhost projectlens
```

### Step 2: Backend Setup
```powershell
# Navigate to backend directory
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Ensure configuration is present
Copy-Item .env.example .env -Force # if .env does not exist

# Run database migrations and start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```
*Backend API available at: `http://127.0.0.1:8001` (Docs at `/docs`)*

### Step 3: Frontend Setup
```powershell
# Open a new PowerShell terminal and navigate to frontend
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\projectlens-frontend

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```
*Frontend UI available at: `http://localhost:5173`*

---

## 6. Running Tests & Quality Verification

### Backend Pytest Suite
```powershell
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\backend
& .\.venv\Scripts\pytest.exe -v
```
*Current test suite: **156 passed in ~40 seconds**.*

### Frontend Production Build
```powershell
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\projectlens-frontend
npm run build
```
*Compiles TypeScript with `tsc -b` and bundles with Vite without warnings or errors.*

---

## 7. Next Development Roadmap (For Next Developer)

1. **Phase 8: Viva Question Generator Enhancement**:
   - Expand the viva generator to synthesize custom questions by cross-referencing code smells, high complexity files, and documentation claims.
2. **Phase 9: Comprehensive Faculty PDF Report Export**:
   - Wire the backend `/reports/export` endpoint with a clean PDF generation pipeline (e.g. WeasyPrint or reportlab) matching the Neo-Brutalist layout.
3. **Multi-file Batch Uploads & Evaluation Queue**:
   - Provide bulk ZIP upload support for entire classroom project batches.

