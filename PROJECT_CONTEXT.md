# ProjectLens — Project Context

## 1. Project Introduction

ProjectLens is an AI-powered college project evaluation and academic integrity assessment system designed to assist faculty in evaluating student software projects.

Faculty upload a student's project as a ZIP archive. ProjectLens examines its source code, programming languages, frameworks, documentation, code similarity and available Git development history.

The system produces evidence-based analysis results to help faculty evaluate technical quality, documentation, originality signals and development patterns.

ProjectLens is an evaluation assistant. It does not independently determine plagiarism, misconduct or whether a student definitely used AI.

## 2. Existing Technology Stack

### Frontend
- React 19
- TypeScript
- Vite
- Tailwind CSS v4
- React Router v7
- Lucide Icons

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy
- Psycopg 3

### Database
- PostgreSQL 16

### Existing analysis libraries
- Python AST (`ast`)
- Radon
- Tree-sitter
- tree-sitter-javascript
- tree-sitter-java
- GitPython
- PyMuPDF
- python-docx
- Sentence Transformers (optional; semantic similarity currently disabled by default)

### Testing
- Pytest
- Frontend production build using `npm run build`

## 3. Completed Project Phases

### Phase 1 — Project Upload and Database Foundation
- FastAPI application, PostgreSQL integration, project ZIP upload, project record creation, project listing/retrieval, upload validation/security, health-check endpoints.
- Endpoints: `GET /health`, `GET /api/health`, `POST /api/projects/upload`, `GET /api/projects`, `GET /api/projects/{project_id}`.

### Phase 2 — Project Parser and Technology Detection
- Secure ZIP extraction, project file inventory, file categorization, language detection, framework/dependency detection, README detection, Git metadata availability detection.
- Endpoints: `GET /api/projects/{project_id}/files`, `GET /api/projects/{project_id}/structure`, `POST /api/projects/{project_id}/parse`.

### Phase 3 — Code Quality Analysis
- Python AST analysis, Radon code metrics, Tree-sitter parsing for supported languages, LOC/SLOC, function/class counts, cyclomatic complexity, maintainability index, syntax error detection, evidence-based quality findings, preliminary deterministic score.
- Endpoints: `POST /api/projects/{project_id}/analyze/code-quality`, `GET /api/projects/{project_id}/code-quality`.

### Phase 4 — Code Similarity Analysis
- Language-aware tokenization, token-shingle Jaccard similarity, exact file matching (SHA-256), hierarchical structural similarity, optional embedding-based semantic similarity (disabled by default), project-to-project comparison, coverage-aware scoring, file-level matching evidence, advisory similarity categories.
- Endpoints: `POST /api/projects/{project_id}/analyze/similarity`, `GET /api/projects/{project_id}/similarity`.

### Phase 5 — Documentation Analysis and Code Consistency
- Markdown/plain-text extraction, PDF extraction (PyMuPDF), DOCX extraction (python-docx), heading-aware section recognition, documentation completeness metrics, preliminary documentation quality score, technology consistency verification, file/component reference checking, implementation claim analysis, unverified numerical claim identification, evidence-based findings.
- Endpoints: `POST /api/projects/{project_id}/analyze/documentation`, `GET /api/projects/{project_id}/documentation`.

### Phase 6 — Git Development History Analysis
- Local Git repository detection, read-only commit inspection, commit timeline, contributor statistics, additions/deletions, commit intervals/activity distributions, commit concentration, development-pattern signals, shallow repository detection, missing/corrupt Git history handling, advisory faculty findings.
- Endpoints: `POST /api/projects/{project_id}/analyze/development-history`, `GET /api/projects/{project_id}/development-history`.

### Phase 7A — OpenRouter LLM Integration + AI-Assistance Analyzer (in progress)
- Reusable OpenRouter client (OpenAI-compatible Python SDK).
- Deterministic AI-assistance evidence collector from Phases 3–6 results.
- LLM-based evidence interpretation via OpenRouter (`google/gemma-4-26b-a4b-it:free`).
- SQLAlchemy persistence + API endpoints `POST /api/projects/{project_id}/analyze/ai-assistance` and `GET /api/projects/{project_id}/ai-assistance`.
- Unified `GET /api/projects/{project_id}/analysis` extended with `aiAssistance` section.

Not yet implemented: Innovation Analysis, Viva Question Generation, final evaluation scoring, PDF reporting.

## 4. Application Architecture

```
ProjectLens/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app, lifespan, CORS, global exception handler
│   │   ├── config.py               # Pydantic Settings (.env-driven)
│   │   ├── database.py             # SQLAlchemy engine, SessionLocal, Base, get_db, init_db
│   │   ├── api/
│   │   │   ├── health.py           # /health, /api/health
│   │   │   └── projects.py         # All project + analysis routes
│   │   ├── models/
│   │   │   ├── project.py          # Project, ProjectFile, ProjectStructure
│   │   │   ├── code_quality.py     # ProjectQualityAnalysis, ProjectFileMetric
│   │   │   ├── similarity.py       # ProjectSimilarityAnalysis, ProjectSimilarityMatch
│   │   │   ├── documentation.py    # ProjectDocumentationAnalysis, ProjectDocumentItem, ProjectDocumentationFinding
│   │   │   ├── git_history.py      # ProjectGitHistoryAnalysis, ProjectCommitRecord, ProjectGitFinding
│   │   │   └── __init__.py         # model registration order (imported by database.init_db)
│   │   ├── schemas/
│   │   │   ├── project.py          # project response/upload/list schemas
│   │   │   ├── code_quality.py     # CodeQualityResponse etc.
│   │   │   ├── similarity.py       # ProjectSimilarityResponse etc.
│   │   │   ├── documentation.py    # DocumentationResponse etc.
│   │   │   ├── git_history.py      # GitHistoryResponse etc.
│   │   │   └── __init__.py         # schema exports
│   │   ├── services/
│   │   │   ├── project_service.py  # Project CRUD helpers
│   │   │   ├── project_parser.py   # ZIP extraction & parsing
│   │   │   ├── storage_service.py  # upload validation & persistence
│   │   │   ├── code_quality/       # CodeQualityService (Phase 3)
│   │   │   ├── similarity/         # SimilarityService (Phase 4)
│   │   │   ├── documentation/      # DocumentationService (Phase 5)
│   │   │   ├── git_history/        # GitHistoryService (Phase 6)
│   │   │   ├── llm/                # NEW Phase 7A: OpenRouter client
│   │   │   └── ai_assistance/      # NEW Phase 7A: evidence collector, analyzer, prompts, service
│   │   └── __init__.py
│   ├── tests/                      # Pytest suite (test_health, test_projects, test_parser, test_code_quality, test_similarity, test_documentation, test_git_history)
│   ├── requirements.txt
│   ├── .env                        # runtime configuration (never committed)
│   ├── .gitignore                  # NEW: excludes .env, .venv, uploads, caches
│   └── .venv/                      # existing virtual environment
└── projectlens-frontend/
    ├── src/
    │   ├── pages/                  # Dashboard, New Evaluation, Project Workspace, History & Reports
    │   ├── components/
    │   ├── services/
    │   │   ├── apiClient.ts        # centralized fetch client (no frontend LLM key)
    │   │   └── analysisApi.ts
    │   ├── types/
    │   │   ├── analysis.ts         # AIAssistanceResult type (frontend-facing)
    │   │   └── project.ts
    │   └── ...
    ├── package.json
    └── vite.config.ts
```

## 5. Database Table Relationships

All tables use SQLAlchemy `Base.metadata.create_all()` via `init_db()` (no Alembic migrations).

- `projects` (id PK) — 1:N `project_files`, 1:1 `project_structures`
- `project_files` (id PK, project_id FK → projects.id)
- `project_structures` (project_id PK → projects.id)
- `project_quality_analyses` (id PK, project_id FK → projects.id) — 1:N `project_file_metrics`
- `project_file_metrics` (id PK, quality_analysis_id FK)
- `project_similarity_analyses` (id PK, project_id FK → projects.id) — 1:N `project_similarity_matches`
- `project_similarity_matches` (id PK, analysis_id FK, matched_project_id FK → projects.id)
- `project_documentation_analyses` (id PK, project_id FK → projects.id) — 1:N `project_document_items`, `project_documentation_findings`
- `project_document_items` (id PK, analysis_id FK)
- `project_documentation_findings` (id PK, analysis_id FK)
- `project_git_history_analyses` (id PK, project_id FK → projects.id) — 1:N `project_commit_records`, `project_git_findings`
- `project_commit_records` (id PK, analysis_id FK)
- `project_git_findings` (id PK, analysis_id FK)

### Phase 7A new tables (created by `init_db()`, existing tables untouched)
- `project_ai_assistance_analyses` (id PK, project_id FK → projects.id)
- `project_ai_assistance_evidence_signals` (id PK, analysis_id FK)

No existing Phase 1–6 tables are dropped, recreated, or overwritten. No submitted project records are deleted.

## 6. Important API Endpoints

| Method | Endpoint | Phase | Notes |
|---|---|---|---|
| GET | /health | 1 | Health check |
| GET | /api/health | 1 | Health check (frontend) |
| POST | /api/projects/upload | 1 | Upload ZIP, create project |
| GET | /api/projects | 1 | List projects |
| GET | /api/projects/{id} | 1 | Project details |
| GET | /api/projects/{id}/files | 2 | File inventory |
| GET | /api/projects/{id}/structure | 2 | Parsed structure |
| POST | /api/projects/{id}/parse | 2 | Re-parse structure |
| POST | /api/projects/{id}/analyze/code-quality | 3 | Run code quality |
| GET | /api/projects/{id}/code-quality | 3 | Get code quality |
| POST | /api/projects/{id}/analyze/similarity | 4 | Run similarity |
| GET | /api/projects/{id}/similarity | 4 | Get similarity |
| POST | /api/projects/{id}/analyze/documentation | 5 | Run documentation |
| GET | /api/projects/{id}/documentation | 5 | Get documentation |
| POST | /api/projects/{id}/analyze/development-history | 6 | Run git history |
| GET | /api/projects/{id}/development-history | 6 | Get git history |
| POST | /api/projects/{id}/analyze/ai-assistance | 7A | NEW: Run AI-assistance analysis |
| GET | /api/projects/{id}/ai-assistance | 7A | NEW: Get saved AI-assistance result |
| GET | /api/projects/{id}/analysis | 1–7A | NEW: unified bundle now includes `aiAssistance` section |

## 7. How to Start

### Backend
1. Ensure PostgreSQL 16 is running and database `projectlens_db` exists (see `backend/init_postgres.py`).
2. Activate the existing virtual environment: `backend\.venv\Scripts\Activate.ps1` (Windows) or `source backend/.venv/bin/activate` (Unix).
3. Install dependencies: `pip install -r backend/requirements.txt`.
4. Configure `backend/.env` (DATABASE_URL, LLM_* settings for Phase 7A). `.env` is git-ignored and never committed.
5. Start: `uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload` (or run `backend/app/main.py`).
6. API docs: `http://127.0.0.1:8000/docs`.

### Frontend
1. `cd projectlens-frontend`
2. `npm install`
3. `npm run dev` (Vite dev server, default port 5173/5174)
4. `npm run build` for production build.

Note: frontend points at `VITE_API_BASE_URL` (default `http://127.0.0.1:8001`). Point it at the running backend.

## 8. Configuration (backend/.env)

Non-secret keys shown here. Secret values (LLM_API_KEY) are stored in `.env` which is git-ignored and never logged or printed.

- `ENVIRONMENT=development`, `DEBUG=True`
- `HOST=127.0.0.1`, `PORT=8000`
- `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/projectlens_db`
- `UPLOAD_DIR=./uploads`, `MAX_UPLOAD_SIZE_MB=50`
- Phase 7A LLM settings:
  - `LLM_ENABLED=true`
  - `LLM_PROVIDER=openrouter`
  - `LLM_BASE_URL=https://openrouter.ai/api/v1`
  - `LLM_MODEL=google/gemma-4-26b-a4b-it:free`
  - `LLM_API_KEY=<secret>`
  - `LLM_TIMEOUT_SECONDS=60`
  - `LLM_MAX_INPUT_CHARS=18000`
  - `LLM_MAX_OUTPUT_TOKENS=2000`
  - `LLM_TEMPERATURE=0.2`

## 9. Current Implementation Status

| Phase | Status |
|---|---|
| 1 Upload & DB Foundation | Complete |
| 2 Parser & Tech Detection | Complete |
| 3 Code Quality Analysis | Complete |
| 4 Code Similarity Analysis | Complete |
| 5 Documentation & Consistency | Complete |
| 6 Git Development History | Complete |
| 7A OpenRouter LLM + AI-Assistance | In Progress |
| 7B Innovation Analysis | Not Started |
| 7C Viva Question Generation | Not Started |
| 7D Final Evaluation Scoring | Not Started |
| 7E PDF Reporting | Not Started |

## 10. Security Notes

- Never commit `backend/.env` (contains DATABASE credentials and LLM API key).
- Never log or print API keys, database credentials, or personal identifiers.
- LLM API key is read only by the backend LLM client; never exposed to frontend.
- Frontend contains no LLM keys or credentials.
- `openai` SDK is used only on the backend with OpenRouter base URL.