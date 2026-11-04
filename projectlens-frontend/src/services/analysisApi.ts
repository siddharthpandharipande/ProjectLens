/**
 * analysisApi.ts
 * Service methods for fetching analysis results.
 */
import { apiClient, ApiError } from './apiClient';
import type { ProjectAnalysis, VivaQuestion, EvaluationReport, AIAssistanceResult, InnovationAnalysisResponse } from '../types/analysis';

/** Fetch all analysis results for a project. May be partial if still processing. */
export async function fetchAnalysis(projectId: string): Promise<ProjectAnalysis> {
  return apiClient.getAnalysis<ProjectAnalysis>(projectId);
}

/** Fetch saved AI-Assistance results without making an LLM request. */
export async function fetchAIAssistance(projectId: string): Promise<AIAssistanceResult> {
  return apiClient.getAIAssistance<AIAssistanceResult>(projectId);
}

/** Explicitly run or re-run AI-Assistance analysis. */
export async function triggerAIAssistance(projectId: string): Promise<AIAssistanceResult> {
  return apiClient.analyzeAIAssistance<AIAssistanceResult>(projectId);
}

/** Fetch saved Innovation results without making an LLM request. */
export async function fetchInnovationAnalysis(projectId: string): Promise<InnovationAnalysisResponse> {
  return apiClient.getInnovation<InnovationAnalysisResponse>(projectId);
}

/** Explicitly run or re-run Innovation analysis. */
export async function triggerInnovationAnalysis(projectId: string): Promise<InnovationAnalysisResponse> {
  return apiClient.analyzeInnovation<InnovationAnalysisResponse>(projectId);
}

/**
 * Fetch similarity results. Returns null if the endpoint is not yet implemented
 * (HTTP 404 or 501) rather than throwing.
 */
export async function fetchSimilarity(projectId: string): Promise<ProjectAnalysis['similarity'] | null> {
  try {
    const result = await apiClient.getSimilarity<{ similarity: ProjectAnalysis['similarity'] }>(projectId);
    return result.similarity ?? null;
  } catch (err) {
    if (err instanceof ApiError && (err.status === 404 || err.status === 501)) {
      return null;
    }
    throw err;
  }
}

/** Request viva question generation. Returns questions when ready. */
export async function requestVivaQuestions(projectId: string): Promise<VivaQuestion[]> {
  const result = await apiClient.requestViva<{ questions: VivaQuestion[] }>(projectId);
  return result.questions ?? [];
}

/** Request PDF report generation. */
export async function requestReport(projectId: string): Promise<EvaluationReport> {
  return apiClient.requestReport<EvaluationReport>(projectId);
}

/** Download the PDF report as a Blob and trigger browser download. */
export async function downloadReport(projectId: string, filename: string): Promise<void> {
  const blob = await apiClient.downloadReport(projectId);
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export { ApiError };
