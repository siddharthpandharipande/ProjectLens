# ProjectLens — Future Expansion Modules Specification (Phases 6–11)

This document outlines the architectural blueprints, planned data flows, API specifications, and integration strategies for ProjectLens expansion modules (Phases 6 through 11).

> [!NOTE]
> **Implementation Status**: Phases 1–5 are fully implemented and functional. Phases 6–11 are **planned future modules** whose UI shells are integrated into the frontend interface.

---

## 1. Phase 6 — Git Development Analysis

### Purpose
Evaluates student project development velocity, commit hygiene, contributor balance, and timeline progression over time by parsing raw Git repository commit histories.

### Planned Inputs
- Git repository `.git` directory object graph or shallow clone tree.
- Commit logs (`git log --numstat --date=iso-strict`).
- Author emails and timestamp distributions.

### Planned Outputs
- **Commit Frequency & Distribution**: Daily/weekly commit histogram.
- **Development Span**: First commit to final release duration in days.
- **Contributor Split**: Lines added/deleted per author.
- **Development Pattern Classifier**: Gradual/Organic vs. Bulk/One-shot upload warning.

### Future API Contract
```http
GET /api/projects/{id}/git-analysis
```
```json
{
  "project_id": "99ca0b50-5e98-4b9c-89d3-28ea9457c560",
  "status": "completed",
  "metrics": {
    "total_commits": 42,
    "active_contributors": 2,
    "development_span_days": 47,
    "pattern": "gradual_development",
    "one_shot_commit_warning": false
  },
  "timeline": [
    { "date": "2026-01-10", "commits": 5, "insertions": 420, "deletions": 30 },
    { "date": "2026-01-18", "commits": 12, "insertions": 1150, "deletions": 120 }
  ]
}
```

---

## 2. Phase 7 — AI Assistance & Code Likelihood Analysis

### Purpose
Provides multi-signal evidence regarding the likelihood of significant AI code generation assistance (e.g., ChatGPT, Copilot, Claude) without making ungrounded definitive accusations.

### Planned Inputs
- Code AST structural uniformity vectors.
- Comment density and phrasing patterns.
- Variable/function naming entropy.
- Code-to-documentation claim alignment.

### Planned Signals & Evidence Engine
1. **Style Consistency Delta**: Identifies abrupt shifts in code formatting or complexity within single files.
2. **Generic Pattern Resemblance**: Compares AST subtrees against known boilerplates.
3. **Commit Progression Delta**: Checks if large complex features appeared without incremental commits.

### Future API Contract
```http
GET /api/projects/{id}/ai-assistance
```
```json
{
  "project_id": "99ca0b50-5e98-4b9c-89d3-28ea9457c560",
  "likelihood_level": "medium",
  "confidence_score": 0.74,
  "signals": [
    { "type": "style_inconsistency", "severity": "medium", "description": "Abrupt formatting shift between service layer and controllers" },
    { "type": "boilerplate_resemblance", "severity": "low", "description": "Standard REST controller patterns" }
  ]
}
```

---

## 3. Phase 8 — Innovation DNA Engine

### Purpose
Measures technical distinction, architectural complexity, domain originality, and technology integration depth.

### Planned Evaluation Dimensions
- **Problem Originality (25%)**: Uniqueness of problem statement relative to standard college templates (e.g., Todo app vs. Distributed GeoRisk AI).
- **Technical Approach (20%)**: Custom algorithm design vs. basic wrapper usage.
- **Architecture Uniqueness (20%)**: Microservices, pub/sub, custom state management vs. monolithic single-file.
- **Feature Differentiation (20%)**: Specialized UI/UX workflows and domain features.
- **Technology Integration (15%)**: Interoperability between disparate tech stacks (DB + ML + WebSockets).

### Future API Contract
```http
GET /api/projects/{id}/innovation
```
```json
{
  "project_id": "99ca0b50-5e98-4b9c-89d3-28ea9457c560",
  "innovation_score": 82,
  "dimensions": {
    "problem_originality": 85,
    "technical_approach": 78,
    "architecture_uniqueness": 81,
    "feature_differentiation": 88,
    "technology_integration": 79
  },
  "strengths": [
    "Custom recommendation pipeline implementation",
    "Non-trivial multi-tenant architecture"
  ]
}
```

---

## 4. Phase 9 — Viva Voice & Automated Q&A Engine

### Purpose
Generates intelligent, project-specific viva questions based on actual code ASTs, imported libraries, and documentation claims, supporting interactive text and voice-based student examination.

### Planned Components
1. **Dynamic Question Generator**: Formulates targeted questions on architectural choices, code algorithms, and database designs.
2. **Adaptive Examination Flow**: Adjusts question difficulty based on student responses.
3. **Voice Interface (STT / TTS)**: Browser-native Web Speech API or OpenAI Whisper / ElevenLabs voice interaction.

### Future API Contract
```http
POST /api/projects/{id}/viva/start
POST /api/projects/{id}/viva/submit-answer
```
```json
{
  "session_id": "viva_88f12a",
  "question": "In app/services/similarity_fusion.py, why did you assign a 50% weight to AST similarity over Token similarity?",
  "category": "code_understanding",
  "difficulty": "hard"
}
```

---

## 5. Phase 10 — Final Evaluation Engine

### Purpose
Aggregates weighted evaluation metrics across all implemented evaluation dimensions into a single faculty-configurable grade recommendation.

### Planned Weighted Matrix Formula
$$\text{FinalScore} = w_{\text{quality}} S_{\text{quality}} + w_{\text{sim}} S_{\text{sim}} + w_{\text{doc}} S_{\text{doc}} + w_{\text{git}} S_{\text{git}} + w_{\text{ai}} S_{\text{ai}} + w_{\text{innov}} S_{\text{innov}} + w_{\text{viva}} S_{\text{viva}}$$

### Configurable Weights Default
- Code Quality ($20\%$)
- Documentation ($15\%$)
- Originality / Similarity ($15\%$)
- Development Process ($10\%$)
- AI Assistance ($10\%$)
- Innovation DNA ($15\%$)
- Viva Voice ($15\%$)

### Future API Contract
```http
GET /api/projects/{id}/evaluation
```

---

## 6. Phase 11 — Final Report Generator

### Purpose
Compiles an executive evaluation dossier suitable for college faculty and accreditation boards in Web, PDF, and JSON formats.

### Report Sections
1. Executive Summary & Final Score
2. Student & Project Metadata
3. Technology Stack & AST Code Metrics
4. Code Quality Findings
5. Similarity & Originality Audit
6. Documentation & Claim Consistency Matrix
7. Git Commit Timeline & Velocity
8. AI Assistance Evidence Assessment
9. Innovation DNA Breakdown
10. Viva Question Log & Transcript
11. Faculty Actionable Recommendations

---

## Integration Roadmap
All future modules will hook directly into the existing `AnalysisJob` background runner infrastructure (`backend/app/services/`) and register routes under `backend/app/api/`. The frontend UI components are pre-configured to render these module cards as Phase Preparation previews until backend activation.
