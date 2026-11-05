# ProjectLens 🔍

> **AI-Powered College Software Project Evaluation Assistant**  
> Tailored for academic faculty, evaluators, and viva panels.

ProjectLens helps academic institutions evaluate student software engineering projects objectively. By combining deterministic static analysis (AST complexity, code smells, token similarity, documentation cross-referencing, git development velocity, and cohort innovation comparisons) with optional LLM-assisted qualitative insights, ProjectLens equips evaluators with diagnostic evidence for viva defenses without ever generating automated misconduct scores.

---

## ⚡ Key Highlights & Philosophy

- **Advisory Screener, Not an Automated Judge**: ProjectLens never calculates an "AI probability score", "plagiarism percentage", or disciplinary penalty. All outputs are structured diagnostic signals for human evaluators.
- **Deterministic-First Architecture**: Parsing, complexity analysis, token overlap, document claim extraction, git velocity, innovation profile extraction, and cohort comparison run 100% locally and deterministically without requiring external API access.
- **Optional Supplementary LLM**: Seamlessly integrates with OpenRouter (`google/gemma-4-26b-a4b-it:free`). Resilient against rate limits (HTTP 429) with consolidated banners and zero downtime for deterministic metrics.
- **Academic Neo-Brutalist Interface**: High-contrast, utilitarian design with cream `#FAF6EE` canvas, `#121212` borders, hard drop shadows, high-visibility status chips, and expandable evidence accordions.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.14+, FastAPI 0.115+, Pydantic v2, SQLAlchemy 2.0, Psycopg 3, ReportLab 5.1, scikit-learn, pypdf, python-docx |
| **Frontend** | React 19, TypeScript 5, Vite 8, Tailwind CSS v4, Lucide Icons, React Router v7 |
| **Database** | PostgreSQL 16/17 (Local port 5432) |
| **AI / LLM** | Google Gemini API (`gemini-2.5-flash` via `google-genai`), OpenRouter API (`google/gemma-4-26b-a4b-it:free`) |
| **Testing** | Pytest, AnyIO, Pytest-AsyncIO (172 backend tests, 100% passing) |

---

## 📋 Evaluation Capabilities (Phases 1–Final)

1. **Project Parser**: Validates and safely unpacks ZIP archives, handles nested directories, and builds a secure project catalog.
2. **Language & File Analyzer**: Classifies files by extension, language, line counts, and functional categories.
3. **Code Quality Analyzer**: AST-based cyclomatic complexity, code smell detection, class hierarchies, and modularity metrics.
4. **Code Similarity Analyzer**: Token-level Jaccard overlap, AST subtree hashing, and candidate peer comparison within cohort submissions.
5. **Documentation Analyzer**: Safe text extraction from PDF, DOCX, and Markdown; structural heading extraction; doc-to-code claim cross-referencing.
6. **Development History Analyzer**: Commit tempo, abnormal velocity spikes, single-batch dumps, author distribution, and shallow history detection.
7. **AI-Assistance Analyzer (Phase 9 Refined)**: 26 deterministic signals, Google Gemini 2.5 Flash grounded interpretation, 10 key assistance areas, structured actionable findings with priority tags (`Critical`, `High`, `Medium`, `Low`, `Informational`), why it matters, recommended actions, and viva readiness indicators.
8. **Innovation Analyzer (Phase 9 Refined)**: 5 distinct feature classes (`verified_match`, `documented_feature`, `detected_implementation`, `unverified_claim`, `proposed_future`), transparent Confidence Classifications (`Directly Verified`, `Strong Evidence`, `Moderate Evidence`, `Indirect Evidence`, `Unverified`, `Insufficient Evidence`) with human-readable rationale, and enriched strengths, blind spots, and recommendations.
9. **Viva Question Generator (Phase 8)**: Intelligent examiner-style viva question generation using Google Gemini AI (`gemini-2.5-flash`), 4 modes (Quick Preparation, Complete Viva, Technical Deep Dive, Examiner Challenge), 9 categories, 3 difficulties, practice tracking, single-question regeneration, and 100% deterministic fallback.
10. **Evaluation & Scoring Engine (Final Phase)**: Multi-dimensional 6-category weighted rubric scoring model (Code Quality 30%, Similarity 15%, Documentation 20%, Git 10%, Innovation 15%, Engineering Rigor 10%), dynamic weight renormalization over assessed categories, letter grades (A–F), and honest coverage thresholds (<50% incomplete, 50-70% provisional, >=70% complete).
11. **Comprehensive Report Generator & Faculty Dashboard (Final Phase)**: Interactive workspace with Neo-Brutalist evaluation dashboard, publication-grade ReportLab PDF generator (`#FAF6EE`, `#121212`, `#FFE600`, NumberedCanvas "Page X of Y"), machine-readable JSON export, and faculty advisory banner.

---

## 🚀 Quick Start Guide (Windows PowerShell)

### Prerequisites
- **Python**: 3.14 (or 3.11+) installed
- **Node.js**: 20+ and npm installed
- **PostgreSQL**: 16 or 17 installed and running on `localhost:5432`

---

### Step 1: PostgreSQL Setup

Verify your PostgreSQL service is running and create the `projectlens` database:

```powershell
# Check service status
Get-Service -Name "*postgres*"

# Create the database using PostgreSQL createdb utility
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres -h localhost projectlens
```

---

### Step 2: Backend Setup & Launch

Open a Windows PowerShell terminal:

```powershell
# Navigate to backend directory
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\backend

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Configure environment (if .env doesn't exist yet)
Copy-Item .env.example .env -Force

# (Optional) Add your Google Gemini API key to backend/.env for AI viva questions:
# GEMINI_API_KEY=your_gemini_api_key_here
# Free keys can be obtained from: https://aistudio.google.com/app/apikey

# Start FastAPI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

- **Backend API**: `http://127.0.0.1:8001`
- **Interactive Swagger Docs**: `http://127.0.0.1:8001/docs`

> [!NOTE]
> **Deterministic Fallback**: If `GEMINI_API_KEY` is omitted or if rate limits occur, the Viva Question Generator operates 100% deterministically using local project evidence without downtime.

---

### Step 3: Frontend Setup & Launch

Open a second Windows PowerShell terminal:

```powershell
# Navigate to frontend directory
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\projectlens-frontend

# Install dependencies (first time only)
npm install

# Start Vite dev server
npm run dev
```

- **Frontend App**: `http://localhost:5173`

---

## 🧪 Running Tests & Quality Verification

### Run Backend Tests (156 tests)
```powershell
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\backend
& .\.venv\Scripts\pytest.exe -v
```
All 156 tests pass across parser, quality, similarity, docs, git history, AI assistance, innovation, and Viva Question Generator modules.

### Run Frontend Production Build & TypeScript Typecheck
```powershell
cd C:\Users\sidpa\OneDrive\VIT-SEM-5-TY\AI\ProjectLens-main\projectlens-frontend
npm run build
```
Compiles cleanly with `tsc -b && vite build` with zero errors.

---

## 📚 Project Documentation

- **[Developer Handoff Guide](docs/PROJECT_HANDOFF.md)**: Comprehensive handoff manual detailing architecture, implemented vs planned capabilities, and API endpoints.
- **[Antigravity Guide](docs/ANTIGRAVITY_GUIDE.md)**: Practical workflows and environment guidance for Antigravity AI pair programming.
- **[Development Status Tracker](DEVELOPMENT_STATUS.md)**: Capability matrix with test verification details.
- **[Agent Operating Rules](AGENTS.md)**: Operating constraints, design system tokens, and security boundaries for AI agents.

---

## 🔒 Security & Privacy Notice

- **Never commit `.env` or sensitive credentials**: Database passwords and OpenRouter keys are excluded via `.gitignore`.
- **Uploaded project files**: Stored locally in `backend/uploads/` and excluded from git tracking.
- **No data telemetry**: ProjectLens runs self-contained on your local machine.

---

## 📄 License

Academic Evaluation Software — Built for educational research and faculty evaluation.

