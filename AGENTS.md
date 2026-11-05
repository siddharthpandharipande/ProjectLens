# AGENTS.md — Repository Instructions for Antigravity AI Agents

This repository is **ProjectLens**, an AI-powered college software project evaluation assistant for faculty evaluators and viva panels.

All AI agents working on this codebase must strictly observe the following principles, patterns, and rules:

---

## 1. Core Operating Principles

1. **Academic Advisory Only (No Automated Penalties)**:
   - ProjectLens is strictly an **advisory assistant** for academic evaluators.
   - **Never** introduce or calculate an "AI probability score", "plagiarism percentage", or misconduct verdict.
   - All similarity, AI-assistance, and innovation metrics are screening signals designed to guide faculty questioning during project defense (viva).
2. **Deterministic-First Resilience**:
   - All core features must work without internet access or external API keys.
   - Upstream LLMs (OpenRouter Google Gemma) are supplementary. If the LLM is disabled (`LLM_ENABLED=false`) or rate-limited (HTTP 429), deterministic analysis must remain 100% operational.
3. **Honest Confidence & Strength Ratings**:
   - Do not display arbitrary rule heuristic numbers as scientific "Confidence: 85%". Use categorical strength badges: `Direct Metric`, `Strong Heuristic`, `Moderate Heuristic`, or `Indirect Signal`.
   - If project documentation does not provide sufficient data, output `"Not identified from the available project documents."` and mark scores as `Insufficient Evidence` (`None`). Never invent fake statements.

---

## 2. Design System & UI Tokens (Neo-Brutalism)

The frontend uses Tailwind CSS v4 and adheres strictly to Neo-Brutalist aesthetics:
- **Canvas / Background**: `#FAF6EE` (warm cream)
- **Borders**: `#121212` (solid dark charcoal/black, usually `border-2` or `border-[2.5px]`)
- **Box Shadows**: Hard drop-shadows without blur (`boxShadow: '4px 4px 0px #121212'` or `'2px 2px 0px #121212'`)
- **Action Buttons**: `#FFE600` (yellow) with `#121212` border and hard shadow
- **Accent Tags**:
  - Success / Available / Verified: `#00E5BE` or `#EBF7F5` with `#006b58` text
  - Warning / Advisory: `#FFF4D6` with `#b43b5b` or `#7a5c00`
  - Error / Rate-Limited / Unavailable: `#FF5C8D` or `#FFF0F5` with `#b43b5b`
  - Documentation: `#D8B4FE` (purple)
- **Typography**: Clean sans-serif headers and body, with font-mono for metrics, IDs, paths, and status badges.

---

## 3. Technology Stack & Running Conventions

- **Python**: 3.14+
- **Backend Framework**: FastAPI with SQLAlchemy 2.0 & Psycopg 3
- **Database**: PostgreSQL 16/17 (Local port 5432)
- **Frontend**: React 19, TypeScript, Vite, Tailwind CSS v4, Lucide Icons
- **Target OS**: Windows PowerShell

### Essential Commands:
```powershell
# Run backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001

# Run backend tests
cd backend
& .\.venv\Scripts\pytest.exe -v

# Run frontend dev server
cd projectlens-frontend
npm run dev

# Run frontend production build
cd projectlens-frontend
npm run build
```

---

## 4. Coding & Security Standards

1. **Read-Only GET Endpoints**:
   - GET endpoints must remain idempotent and side-effect free. Analysis execution must occur via POST trigger endpoints.
2. **Credential Safety**:
   - Never commit API keys, database credentials, or secret tokens.
   - Always verify `.gitignore` blocks `.env`, `uploads/`, `node_modules/`, and `__pycache__/`.
3. **Regression Test Preservation**:
   - Any modifications to backend services must pass the full 129-test pytest suite.
   - Any modifications to the frontend must pass `npm run build` (`tsc -b && vite build`) with zero type errors.

