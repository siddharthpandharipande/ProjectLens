/**
 * vivaApi.ts
 *
 * API client functions for Viva Preparation & Viva Question Generator (Phase 8).
 */

import type {
  VivaQuestion,
  VivaQuestionSet,
  VivaGenerateParams,
  VivaProgress,
} from '../types/viva';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const json = await res.json();
      if (json && json.detail) errorDetail = String(json.detail);
    } catch {
      // Ignore json decode error
    }
    throw new Error(errorDetail);
  }
  return res.json() as Promise<T>;
}

/**
 * Trigger viva question generation for a project using Gemini AI or fallback.
 */
export async function generateVivaQuestions(
  projectId: string,
  params: VivaGenerateParams,
): Promise<VivaQuestionSet> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/viva/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      mode: params.mode,
      difficulty: params.difficulty || 'all',
      questionCount: params.questionCount,
      forceRegenerate: params.forceRegenerate ?? true,
    }),
  });
  return handleResponse<VivaQuestionSet>(res);
}

/**
 * Fetch saved viva questions for a project with optional filters.
 */
export async function fetchVivaQuestions(
  projectId: string,
  filters?: {
    category?: string;
    difficulty?: string;
    isPracticed?: boolean;
  },
): Promise<VivaQuestionSet | null> {
  const query = new URLSearchParams();
  if (filters?.category && filters.category !== 'all') {
    query.set('category', filters.category);
  }
  if (filters?.difficulty && filters.difficulty !== 'all') {
    query.set('difficulty', filters.difficulty);
  }
  if (filters?.isPracticed !== undefined) {
    query.set('is_practiced', String(filters.isPracticed));
  }

  const qs = query.toString() ? `?${query.toString()}` : '';
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/viva/questions${qs}`);
  return handleResponse<VivaQuestionSet | null>(res);
}

/**
 * Toggle or update the practiced status for a viva question.
 */
export async function updateVivaPracticeStatus(
  projectId: string,
  questionId: string,
  isPracticed: boolean,
): Promise<VivaQuestion> {
  const res = await fetch(
    `${BASE_URL}/api/projects/${projectId}/viva/questions/${questionId}/practice`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ isPracticed }),
    },
  );
  return handleResponse<VivaQuestion>(res);
}

/**
 * Regenerate an individual viva question.
 */
export async function regenerateVivaQuestion(
  projectId: string,
  questionId: string,
): Promise<VivaQuestion> {
  const res = await fetch(
    `${BASE_URL}/api/projects/${projectId}/viva/questions/${questionId}/regenerate`,
    {
      method: 'POST',
    },
  );
  return handleResponse<VivaQuestion>(res);
}

/**
 * Fetch practice and preparation progress statistics.
 */
export async function fetchVivaProgress(projectId: string): Promise<VivaProgress> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/viva/progress`);
  return handleResponse<VivaProgress>(res);
}

/**
 * Clear viva questions for a project.
 */
export async function clearVivaQuestions(projectId: string): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/api/projects/${projectId}/viva/questions`, {
    method: 'DELETE',
  });
  return handleResponse<{ message: string }>(res);
}

