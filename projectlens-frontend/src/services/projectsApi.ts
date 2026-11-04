/**
 * projectsApi.ts
 * Service methods for project listing, upload, structure, and files.
 */
import { apiClient, ApiError } from './apiClient';
import type {
  Project,
  UploadPayload,
  UploadResponse,
  DashboardStats,
  ProjectStructure,
  ProjectFilesResponse,
  CodeQualityResponse,
} from '../types/project';

export interface ProjectsResponse {
  projects: Project[];
  stats?: DashboardStats;
}

/** Fetch all projects from the backend. */
export async function fetchProjects(): Promise<ProjectsResponse> {
  return apiClient.getProjects<ProjectsResponse>();
}

/** Fetch a single project by ID. */
export async function fetchProject(projectId: string): Promise<Project> {
  return apiClient.getProject<Project>(projectId);
}

/**
 * Fetch project structure summary (languages, frameworks, file counts).
 * Returns null if the structure has not been parsed yet (HTTP 404).
 */
export async function fetchProjectStructure(projectId: string): Promise<ProjectStructure | null> {
  try {
    return await apiClient.getProjectStructure<ProjectStructure>(projectId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/** Fetch indexed file inventory for a project. */
export async function fetchProjectFiles(
  projectId: string,
  category?: string,
  limit = 100,
  offset = 0,
): Promise<ProjectFilesResponse> {
  return apiClient.getProjectFiles<ProjectFilesResponse>(projectId, category, limit, offset);
}

/** Trigger re-parsing of project structure. */
export async function reparseProject(projectId: string): Promise<ProjectStructure> {
  return apiClient.parseProject<ProjectStructure>(projectId);
}

/**
  * Fetch saved Code Quality analysis results.
  * Returns null if analysis has not been performed yet (HTTP 404).
  */
export async function fetchCodeQuality(projectId: string): Promise<CodeQualityResponse | null> {
  try {
    return await apiClient.getCodeQuality<CodeQualityResponse>(projectId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/**
  * Run or refresh Code Quality AST analysis.
  */
export async function triggerCodeQualityAnalysis(projectId: string): Promise<CodeQualityResponse> {
  return apiClient.analyzeCodeQuality<CodeQualityResponse>(projectId);
}

/**
 * Fetch saved Code Similarity analysis results.
 * Returns null if not performed yet.
 */
export async function fetchSimilarity(projectId: string): Promise<import('../types/project').ProjectSimilarityResponse | null> {
  try {
    return await apiClient.getSimilarity<import('../types/project').ProjectSimilarityResponse>(projectId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/**
 * Run or refresh Code Similarity analysis against cohort submissions.
 */
export async function triggerSimilarityAnalysis(projectId: string): Promise<import('../types/project').ProjectSimilarityResponse> {
  return apiClient.analyzeSimilarity<import('../types/project').ProjectSimilarityResponse>(projectId);
}

/**
 * Fetch saved Documentation Analysis and Consistency findings.
 * Returns null if not performed yet (HTTP 404).
 */
export async function fetchDocumentation(projectId: string): Promise<import('../types/project').DocumentationResponse | null> {
  try {
    return await apiClient.getDocumentation<import('../types/project').DocumentationResponse>(projectId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/**
 * Run or refresh Documentation Analysis and Consistency checks.
 */
export async function triggerDocumentationAnalysis(projectId: string): Promise<import('../types/project').DocumentationResponse> {
  return apiClient.analyzeDocumentation<import('../types/project').DocumentationResponse>(projectId);
}

/**
 * Fetch saved Git Development History analysis results.
 * Returns null if not performed yet (HTTP 404).
 */
export async function fetchDevelopmentHistory(projectId: string): Promise<import('../types/project').GitHistoryResponse | null> {
  try {
    return await apiClient.getDevelopmentHistory<import('../types/project').GitHistoryResponse>(projectId);
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return null;
    }
    throw err;
  }
}

/**
 * Run or refresh Git Development History analysis.
 */
export async function triggerDevelopmentHistoryAnalysis(projectId: string): Promise<import('../types/project').GitHistoryResponse> {
  return apiClient.analyzeDevelopmentHistory<import('../types/project').GitHistoryResponse>(projectId);
}

/**
 * Upload a ZIP file and optionally provide metadata.
 * Returns the new project ID upon success.
 */
export async function uploadProject(payload: UploadPayload): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', payload.file);
  if (payload.course) formData.append('course', payload.course);
  if (payload.title) formData.append('title', payload.title);
  return apiClient.uploadProject<UploadResponse>(formData);
}

/** Check if the backend is reachable. Returns true / false. */
export async function checkHealth(): Promise<boolean> {
  try {
    const result = await apiClient.health();
    return result.status === 'ok' || result.status === 'healthy';
  } catch {
    return false;
  }
}

export { ApiError };
