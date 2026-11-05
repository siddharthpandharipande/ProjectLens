/**
 * apiClient.ts
 *
 * Centralized HTTP client for all ProjectLens backend calls.
 * Base URL is read from the VITE_API_BASE_URL environment variable.
 *
 * All methods return typed responses or throw ApiError on failure.
 * When the backend is not reachable the error is propagated to the caller —
 * no fake data is returned as a fallback.
 *
 * Documented endpoint assumptions (agreed-upon REST contract):
 *   GET  /api/health
 *   GET  /api/projects
 *   POST /api/projects/upload          (multipart/form-data)
 *   GET  /api/projects/:id
 *   GET  /api/projects/:id/structure
 *   GET  /api/projects/:id/files
 *   POST /api/projects/:id/parse
 *   GET  /api/projects/:id/analysis
 *   GET  /api/projects/:id/similarity
 *   POST /api/projects/:id/viva
 *   POST /api/projects/:id/report
 *   GET  /api/projects/:id/report      (download)
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';

export class ApiError extends Error {
  readonly status: number;
  readonly detail?: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail: unknown;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new ApiError(
      response.status,
      `HTTP ${response.status}: ${response.statusText}`,
      detail,
    );
  }
  return response.json() as Promise<T>;
}

export const apiClient = {
  /** Check that the FastAPI backend is reachable. */
  async health(): Promise<{ status: string }> {
    const res = await fetch(`${BASE_URL}/api/health`);
    return handleResponse<{ status: string }>(res);
  },

  /** List all submitted projects. */
  async getProjects<T>(): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects`);
    return handleResponse<T>(res);
  },

  /** Upload a ZIP file and create a new evaluation project. */
  async uploadProject<T>(formData: FormData): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/upload`, {
      method: 'POST',
      body: formData,
      // Do NOT set Content-Type header — browser sets it with correct boundary.
    });
    return handleResponse<T>(res);
  },

  /** Fetch full project details including current processing status. */
  async getProject<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}`);
    return handleResponse<T>(res);
  },

  /** Fetch project structure summary (languages, frameworks, file counts). */
  async getProjectStructure<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/structure`);
    return handleResponse<T>(res);
  },

  /** Fetch indexed file inventory for a project. */
  async getProjectFiles<T>(projectId: string, category?: string, limit = 100, offset = 0): Promise<T> {
    const params = new URLSearchParams();
    if (category) params.set('category', category);
    params.set('limit', String(limit));
    params.set('offset', String(offset));
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/files?${params.toString()}`);
    return handleResponse<T>(res);
  },

  /** Trigger project structure parsing or re-parsing. */
  async parseProject<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/parse`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Run or refresh Code Quality AST analysis. */
  async analyzeCodeQuality<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/code-quality`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Get saved Code Quality AST analysis results. */
  async getCodeQuality<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/code-quality`);
    return handleResponse<T>(res);
  },

  /** Fetch all available analysis results for a project. */
  async getAnalysis<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analysis`);
    return handleResponse<T>(res);
  },

  /** Fetch the saved AI-Assistance analysis without invoking the LLM. */
  async getAIAssistance<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/ai-assistance`);
    return handleResponse<T>(res);
  },

  /** Explicitly run or re-run AI-Assistance analysis. */
  async analyzeAIAssistance<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/ai-assistance`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Fetch the saved Innovation analysis without invoking the LLM. */
  async getInnovation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/innovation`);
    return handleResponse<T>(res);
  },

  /** Explicitly run or re-run Innovation analysis. */
  async analyzeInnovation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/innovation`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Fetch similarity comparison results. */
  async getSimilarity<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/similarity`);
    return handleResponse<T>(res);
  },

  /** Run or refresh Code Similarity analysis. */
  async analyzeSimilarity<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/similarity`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Fetch saved Documentation Analysis and Consistency findings. */
  async getDocumentation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/documentation`);
    return handleResponse<T>(res);
  },

  /** Run or refresh Documentation Analysis and Consistency checks. */
  async analyzeDocumentation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/documentation`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Fetch saved Git Development History analysis results. */
  async getDevelopmentHistory<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/development-history`);
    return handleResponse<T>(res);
  },

  /** Run or refresh Git Development History analysis. */
  async analyzeDevelopmentHistory<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/analyze/development-history`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Request viva question generation for a project. */
  async requestViva<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/viva`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Request report generation. */
  async requestReport<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/report`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Download the generated PDF report (returns a Blob). */
  async downloadReport(projectId: string): Promise<Blob> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/report`);
    if (!res.ok) throw new ApiError(res.status, `HTTP ${res.status}: ${res.statusText}`);
    return res.blob();
  },

  /** Trigger comprehensive overall project evaluation. */
  async triggerEvaluation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/evaluate`, {
      method: 'POST',
    });
    return handleResponse<T>(res);
  },

  /** Fetch latest evaluation details for a project. */
  async fetchEvaluation<T>(projectId: string): Promise<T> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/evaluation`);
    return handleResponse<T>(res);
  },

  /** Download machine-readable evaluation JSON. */
  async downloadEvaluationJson(projectId: string): Promise<Blob> {
    const res = await fetch(`${BASE_URL}/api/projects/${projectId}/evaluation/export.json`);
    if (!res.ok) throw new ApiError(res.status, `HTTP ${res.status}: ${res.statusText}`);
    return res.blob();
  },
};
