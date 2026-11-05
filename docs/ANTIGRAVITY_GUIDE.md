# Antigravity Developer Guide for ProjectLens

Welcome to the ProjectLens project! This guide is written specifically for developers working on ProjectLens inside Google Antigravity.

---

## 1. Workspace Structure & Key Directories

```
ProjectLens-main/
├── backend/                         # FastAPI Python Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI Application entry point
│   │   ├── config.py                # Pydantic Settings & environment loader
│   │   ├── database.py              # SQLAlchemy engine & session factory
│   │   ├── models/                  # Database entity models
│   │   │   ├── project.py           # Project & ProjectFile models
│   │   │   └── analysis.py          # Analysis, Evidence, and Score models
│   │   ├── routers/                 # API route handlers
│   │   │   ├── projects.py          # /api/projects routes
│   │   │   └── analysis.py          # /api/analysis routes
│   │   └── services/                # Evaluation Engines (Phases 1–8)
│   │       ├── parser.py            # Phase 1 & 2 Archive extraction & parsing
│   │       ├── code_quality/        # Phase 3 AST complexity, smells, metrics
│   │       ├── similarity/          # Phase 4 Token & tree similarity
│   │       ├── documentation/       # Phase 5 Safe text extraction & consistency
│   │       ├── git_history/         # Phase 6 Commit velocity, author metrics
│   │       ├── ai_assistance/       # Phase 7A & 7B Multi-module signal collection
│   │       └── innovation/          # Phase 7B & 7C Profile extraction & cohort analysis
│   ├── tests/                       # Pytest test suite (129 passing tests)
│   ├── .env                         # Local environment configuration
│   └── .venv/                       # Python 3.14 virtual environment
│
├── projectlens-frontend/            # React 19 + TypeScript + Vite Frontend
│   ├── src/
│   │   ├── App.tsx                  # Main router setup
│   │   ├── pages/
│   │   │   ├── DashboardPage.tsx    # Recent submissions & system status
│   │   │   ├── NewEvaluationPage.tsx# Project upload & analysis kick-off
│   │   │   └── ProjectWorkspacePage.tsx # Master evaluation dashboard (11 tabs)
│   │   ├── components/              # UI components (Neo-Brutalist design system)
│   │   ├── services/                # API client functions (Axios / Fetch)
│   │   └── types/                   # TypeScript interfaces
│   └── package.json
│
├── docs/                            # Developer Documentation
│   ├── PROJECT_HANDOFF.md           # Master handoff specification
│   └── ANTIGRAVITY_GUIDE.md         # This Antigravity runtime manual
│
├── AGENTS.md                        # Agent operating instructions & constraints
├── DEVELOPMENT_STATUS.md            # Capability tracking matrix
└── README.md                        # Public repository README
```

---

## 2. Windows PowerShell Commands Quick Reference

### Running the Backend
Always use the virtual environment python interpreter or activate first:
```powershell
# Method A: Direct command execution
Set-Location .\backend
& .\.venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8001

# Method B: Activate script
Set-Location .\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

### Running Backend Tests
```powershell
Set-Location .\backend
& .\.venv\Scripts\pytest.exe -v
```

### Running the Frontend
```powershell
Set-Location .\projectlens-frontend
npm run dev
```

### Verifying Frontend Build & TypeScript
```powershell
Set-Location .\projectlens-frontend
npm run build
```

---

## 3. PostgreSQL Management on Windows

ProjectLens runs against a local PostgreSQL 16 or 17 service.
- **Service Name**: `postgresql-x64-17` (or `postgresql-x64-16`)
- **Port**: `5432`
- **Database Name**: `projectlens`
- **Driver**: `psycopg` (binary driver using SQLAlchemy URL: `postgresql+psycopg://username:password@localhost:5432/projectlens`)

### Useful PowerShell Diagnostic Commands:
```powershell
# Check PostgreSQL service status
Get-Service -Name "*postgres*"

# Start service if stopped
Start-Service -Name "postgresql-x64-17"

# Test TCP port availability
Test-NetConnection -ComputerName 127.0.0.1 -Port 5432

# Create the projectlens database
& "C:\Program Files\PostgreSQL\17\bin\createdb.exe" -U postgres -h localhost projectlens
```

---

## 4. Antigravity Agent Guidelines

When prompting Antigravity to write or modify code in this repository:

1. **Deterministic-First Principle**:
   - Never make features rely solely on an external AI API. Deterministic algorithms must work even when `LLM_ENABLED=false` or upstream APIs return HTTP 429.
2. **Academic Integrity & Transparency**:
   - Never generate or display an "AI plagiarism score" or "AI probability percentage".
   - Use screening labels and honest heuristic badges (`Direct Metric`, `Strong Heuristic`, `Moderate Heuristic`, `Indirect Signal`).
3. **Preserve Neo-Brutalist Design Tokens**:
   - Canvas background: `#FAF6EE`
   - Hard borders: `border-2` or `border-[2.5px] border-[#121212]`
   - Primary action buttons: `#FFE600`
   - Accent highlights: `#00E5BE` (cyan/teal), `#FF5C8D` (pink/red), `#D8B4FE` (purple)
   - Hard drop-shadows: `boxShadow: '4px 4px 0px #121212'` or `'2px 2px 0px #121212'`
4. **Never Leak Credentials**:
   - Check `.gitignore` before committing.
   - Keep actual database passwords and API keys in `backend/.env`.
   - Keep `backend/.env.example` scrubbed with generic placeholders.
5. **Always Verify Changes with Tests**:
   - Backend: run `pytest` (129 tests must pass).
   - Frontend: run `npm run build` (`tsc -b && vite build` must pass with 0 errors).

