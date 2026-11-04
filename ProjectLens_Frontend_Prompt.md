# ProjectLens — Frontend Rebuild Prompt

## Your task

Rebuild the **frontend only** of ProjectLens using the existing project as the starting point. The current frontend feels too generic, AI-generated, and complicated. Replace that visual direction with a clear **Neo-Brutalist web design** based on the reference screenshots supplied by the user.

Keep the original ProjectLens idea and evaluation features. **Do not build a new product, add extra modules, or change the core project purpose.** The goal is a simple, distinctive, easy-to-explain frontend that can connect to a FastAPI backend as the backend is implemented.

Before changing code, inspect the existing frontend structure and dependencies. Reuse what is useful, remove unnecessary sections and routes, and avoid creating duplicate components or an unnecessary new architecture. Do not modify or invent backend functionality.

---

## 1. Project context

**ProjectLens** helps college faculty evaluate student software projects. A faculty member uploads a project ZIP file, and the backend analyzes the available project files. The system can help assess:

- Code quality and structure
- Similarity between submitted projects
- Documentation and consistency between the report and code
- Development history, when Git history is available
- Signals that may suggest AI assistance
- Project innovation and contribution
- Student understanding through project-specific viva questions
- An overall evaluation and downloadable report

ProjectLens is an **evaluation assistant**, not an automatic judge. Similarity and AI-assistance findings must be presented as signals with supporting evidence—not as definitive proof of plagiarism or AI use. Faculty should remain responsible for the final judgment.

### Main user flow

`Open dashboard → Upload a real project ZIP → Backend processes it → View analysis → Review findings / viva questions → Generate or download the report`

The interface must clearly distinguish between **not started**, **processing**, **completed**, **failed**, and **not available yet**.

---

## 2. Strict page limit: exactly 4 core pages

Do not create extra pages for every individual analysis feature. Use tabs or clearly separated sections inside the Project Workspace.

### Page 1 — Dashboard (`/` or `/dashboard`)

Purpose: give faculty one simple starting point.

Include only:
- ProjectLens title and a short description
- One primary **New Evaluation** button
- A small summary area populated from real backend data, such as total submitted projects or completed evaluations, only if the API provides those values
- A **Recent Projects** list populated from the backend
- A useful empty state when no projects exist, such as: “No projects evaluated yet. Upload a project to begin.”

Rules:
- Do not show invented project names, sample students, placeholder scores, fake charts, or random activity.
- If the backend has no records, show the empty state rather than sample cards.
- Do not add a large analytics dashboard full of graphs and decorative metrics.

### Page 2 — New Evaluation (`/projects/new`)

Purpose: let faculty provide the input that will be analyzed.

Include:
- A clear ZIP upload area with drag-and-drop and a browse button
- Accepted file type and maximum size based on the actual backend configuration; do not invent a limit if it is not defined
- Optional project title and course/class fields only if they are useful to the backend
- A clear **Upload and Analyze** button
- Validation and readable error messages
- Upload/processing states based on real API responses

Behavior:
- Do not create a project or show results before the user supplies a valid input.
- Submit the ZIP to the real FastAPI endpoint using `multipart/form-data`.
- Once the backend returns a project ID, navigate to that project's workspace.
- If analysis runs as a background job, show the real status returned by the backend and refresh/poll it appropriately. Do not simulate progress with a timer or display made-up percentages.
- If upload or analysis fails, explain the error and allow the user to retry.
- Do not execute uploaded code in the browser.

### Page 3 — Project Workspace (`/projects/:projectId`)

Purpose: this is the main evaluation page. Keep every project-specific analysis here instead of making many separate routes.

At the top, show:
- Actual project name and project ID, when returned by the API
- Current processing status
- Overall score only after the backend returns a real score
- A short project summary based on real analysis data

Use a compact tab bar or section navigation inside this page with these sections:

1. **Overview** — summary of completed analyses, main findings, strengths, and areas that need review.
2. **Code Quality** — actual supported metrics such as lines of code, functions/classes, complexity, maintainability, and findings.
3. **Similarity** — comparison results returned by the similarity service, with a clear explanation of what was compared and the evidence behind the result.
4. **Documentation & Development** — report/README findings, code-documentation consistency issues, and Git timeline when available.
5. **AI Assistance & Innovation** — evidence-based AI-assistance signals and the innovation analysis returned by the backend. Show confidence and limitations where provided.
6. **Viva Questions** — project-specific questions returned by the backend, grouped into simple categories if the API supports that.
7. **Evaluation Report** — the overall score breakdown, faculty notes/review controls if supported, and a button to request or download the generated PDF.

Keep each section straightforward. Use plain-language labels and a short explanation for technical metrics. Hide sections that do not apply only when the backend explicitly says they are unsupported; otherwise show a simple “Not available yet” or “No data returned” state. Do not replace missing backend results with invented content.

Important presentation rules:
- Do not imply that an analysis is complete while the backend is still processing it.
- Show the source/evidence for findings whenever the API provides it, such as a filename, line number, commit, or matched project.
- Clearly label AI-assistance output as an estimate or signal, never as proof.
- Clearly label similarity results as items for faculty review, never as an automatic plagiarism verdict.
- Do not display fake scores or pre-filled viva questions.

### Page 4 — History & Reports (`/history`)

Purpose: let faculty find projects that were actually submitted and revisit their evaluations.

Include:
- A simple table or list of real projects returned by the backend
- Search/filter only for fields that exist in the API, such as project name, status, or date
- Actions to open a project workspace and download an existing report when available
- A proper empty state when there are no projects or reports
- Optional multi-select comparison only if the similarity API supports comparing submitted projects; show results only after the backend returns them

Do not add separate routes for settings, notifications, analytics, help, or other unnecessary sections. Do not create extra pages just to display one metric.

---

## 3. Neo-Brutalist visual direction

Use the supplied screenshots as visual references, not as content to copy. The interface should feel bold, tactile, editorial, and intentionally designed—not like a generic AI SaaS template.

### Visual rules
- Warm off-white or cream page background
- Mostly black text and strong black outlines
- Bright yellow as the main action/accent color
- Small amounts of pink, teal, or cobalt as secondary accents
- Visible borders, roughly 2–3 px where appropriate
- Simple, hard offset shadows on selected cards/buttons to create a printed-paper feel
- Large, confident headings and short copy
- Clear spacing and strong alignment
- Optional subtle dotted or grid background in a few areas, not everywhere
- Simple geometric decorations only when they do not interfere with reading or functionality
- Rounded corners should be restrained; combine mostly square/low-radius panels with a few softer elements

### Avoid
- Purple/pink AI gradients across the whole page
- Glassmorphism, excessive blur, neon glow, or floating gradient blobs
- Robot heads, brains, AI stars, and generic AI illustrations
- Decorative 3D scenes or complex animations
- Too many cards inside cards
- Giant charts that do not help faculty evaluate a project
- Excessive animation or motion effects
- Long, vague marketing copy
- Dense technical jargon without a short explanation

### Typography
- Use a bold, readable sans-serif for headings and a clean sans-serif for body text.
- Use a monospaced font only for code snippets, file paths, and technical identifiers.
- Keep body text comfortable to read and avoid tiny labels.
- If the current project already has suitable fonts, reuse them rather than adding many font dependencies.

### Interaction and responsiveness
- Buttons should have clear hover/focus states and feel tactile.
- Use subtle transitions only where they improve feedback.
- Support desktop and tablet first, while keeping upload, tabs, tables, and actions usable on mobile.
- Ensure keyboard focus, accessible names, readable contrast, and clear validation messages.

---

## 4. Navigation and page simplicity

Use a small, consistent navigation with no more than:
- **Dashboard**
- **New Evaluation**
- **History & Reports**

The Project Workspace opens after a project is selected or uploaded. Its seven analysis sections are tabs on the same page, not separate top-level routes.

Keep the most important action—**New Evaluation**—easy to find. Avoid sidebars containing many nested items. Do not add pages or UI sections unless they support the core project workflow.

---

## 5. Real backend data only — absolutely no demo data

This requirement is critical.

- Do not seed the frontend with fake projects, students, scores, history, similarity matches, metrics, comments, reports, or viva questions.
- Do not add a mock database, fake API, random number generator, hardcoded JSON response, or “demo mode.”
- Do not silently fall back to sample data when the backend is offline or an endpoint is not implemented.
- Do not show example results as if they were real results.
- Static interface text, labels, icons, and empty-state illustrations are allowed; **evaluation data must come from a real user input and a real backend response**.
- Before input is submitted, display the upload form and instructions—not an analysis result.
- If the API returns an empty list, display an empty state.
- If the API is unavailable, show a clear connection error and a retry option.
- If a module endpoint is not implemented yet, show “Not available yet” and keep the rest of the page usable. Do not invent the missing output.
- If the backend returns a processing status, display that status honestly.

The user must be able to trace each displayed project or evaluation result back to an actual backend response.

---

## 6. Frontend and FastAPI integration

Use the existing frontend stack where possible. If a stack needs to be established, prefer:
- **React.js + TypeScript + Vite**
- **Tailwind CSS** for styling
- **Lucide React** for icons
- **Framer Motion** only for small, purposeful transitions

Do not add a heavy state-management, charting, or 3D library unless the existing project genuinely needs it.

### API structure

Create one small, centralized API client/service layer. Do not place raw `fetch` calls throughout UI components. Configure the backend base URL through an environment variable such as:

`VITE_API_BASE_URL=http://localhost:8000`

Keep the base URL in an `.env.example` file, not hardcoded in multiple components. Never put secrets or API keys in frontend code.

Use the existing backend API contract if it already exists. If not, prepare the frontend around a clear REST interface such as:

- `GET /api/health` — check backend connection
- `GET /api/projects` — list real projects
- `POST /api/projects/upload` — upload a ZIP and create a project
- `GET /api/projects/{project_id}` — fetch project details and status
- `GET /api/projects/{project_id}/analysis` — fetch available analysis results
- `GET /api/projects/{project_id}/similarity` — fetch similarity results, if implemented
- `POST /api/projects/{project_id}/viva` — request viva questions, if implemented
- `POST /api/projects/{project_id}/report` — request a report, if implemented
- `GET /api/projects/{project_id}/report` — retrieve/download the report, if implemented

These are suggested contracts, not permission to invent backend behavior. If the backend uses different routes or response shapes, follow its actual contract and document the mapping rather than changing it silently.

### API behavior
- Define TypeScript types/interfaces for projects, processing status, analysis results, findings, and reports.
- Handle loading, success, empty, and error states consistently.
- Handle non-success HTTP responses and malformed responses gracefully.
- Prevent duplicate upload submissions while a request is active.
- Show the actual backend error when it is safe and useful; otherwise show a friendly message.
- Do not calculate or manufacture an evaluation score in the frontend. Display the score returned by the backend.
- Refresh project status from the server when analysis is asynchronous. Do not use fake progress percentages.
- Keep upload, analysis display, and PDF download behavior easy to follow for a beginner.

If an endpoint does not exist yet, create a clearly separated service method that reports that the feature is unavailable. Do not return hardcoded data to make the UI look complete.

---

## 7. Suggested code organization

Keep the structure small and understandable. Adapt it to the existing codebase instead of forcing a complete restructure.

```text
src/
  components/
    layout/
    ui/
    project/
  pages/
    DashboardPage.tsx
    NewEvaluationPage.tsx
    ProjectWorkspacePage.tsx
    HistoryReportsPage.tsx
  services/
    apiClient.ts
    projectsApi.ts
    analysisApi.ts
    reportsApi.ts
  types/
    project.ts
    analysis.ts
  hooks/
  utils/
  App.tsx
  main.tsx
```

Use reusable components only when they reduce duplication. Prefer clear names and small files over abstract, overly clever architecture. A student should be able to open a page component and understand its purpose quickly.

---

## 8. Required states to implement

For each data-driven area, handle the states that apply:

- **Initial / no input:** show instructions or a clear empty state.
- **Loading:** show a simple loading indicator and helpful text.
- **Processing:** show the actual server status.
- **Success:** display only results returned by the backend.
- **Empty:** explain that no data or findings were returned.
- **Error:** explain what went wrong and provide a retry action when possible.
- **Unavailable:** clearly mark features whose backend endpoint is not implemented yet.

Do not use fake skeleton content that looks like real project information. Basic skeleton shapes are acceptable only as loading indicators.

---

## 9. Acceptance checklist

The work is complete only when all of the following are true:

- [ ] The design follows the supplied Neo-Brutalist visual references.
- [ ] Exactly four core pages exist: Dashboard, New Evaluation, Project Workspace, and History & Reports.
- [ ] All project-analysis features live inside the Project Workspace tabs, not separate routes.
- [ ] The interface remains easy to explain to a faculty member who is not deeply technical.
- [ ] No fake projects, fake scores, fake charts, fake findings, fake reports, or mock database are present.
- [ ] Uploading a valid ZIP calls the configured FastAPI backend.
- [ ] Project lists and analysis results come only from backend responses.
- [ ] Missing endpoints show an honest unavailable state instead of fabricated results.
- [ ] Upload failures, backend disconnection, empty data, and processing states are handled.
- [ ] Similarity and AI-assistance results are presented as evidence for faculty review, not definitive verdicts.
- [ ] There is one central API client and typed request/response models.
- [ ] The UI works at common desktop and tablet sizes and remains usable on mobile.
- [ ] No unnecessary pages, overly complex navigation, decorative dashboards, or heavy animations were added.
- [ ] Existing backend code and contracts have not been changed as part of this frontend task.

## Final instruction

First inspect the existing frontend, then implement this redesign in the current project. Keep the result **simple, bold, practical, and backend-ready**. At the end, summarize the four pages, list the API endpoints the frontend expects, identify any endpoint that is not yet available, and provide the exact command to run the frontend locally. Do not claim an integration works unless it has actually been tested against the backend.
