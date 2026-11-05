export type VivaMode =
  | 'quick_prep'
  | 'complete_viva'
  | 'technical_deep_dive'
  | 'examiner_challenge';

export type VivaDifficulty = 'beginner' | 'intermediate' | 'advanced';

export type VivaCategory =
  | 'Project Fundamentals'
  | 'Technical Architecture'
  | 'Technology Stack'
  | 'Implementation and Coding'
  | 'Innovation and Uniqueness'
  | 'Testing and Validation'
  | 'Critical Thinking and Problem Solving'
  | 'Project-Specific Technical Deep Dive'
  | 'Future Scope and Improvements';

export interface VivaQuestion {
  id: string;
  category: string;
  difficulty: VivaDifficulty;
  question: string;
  examinerRationale: string;
  keyPoints: string[];
  suggestedAnswer: string;
  evidenceReference?: string | null;
  isPracticed: boolean;
  source: 'gemini' | 'deterministic_fallback';
  createdAt: string;
  updatedAt: string;
}

export interface VivaQuestionSet {
  id: number;
  projectId: string;
  mode: VivaMode;
  generationSource: 'gemini' | 'deterministic_fallback';
  modelName?: string | null;
  totalQuestions: number;
  practicedCount: number;
  questions: VivaQuestion[];
  createdAt: string;
  updatedAt: string;
}

export interface VivaGenerateParams {
  mode: VivaMode;
  difficulty?: string;
  questionCount: number;
  forceRegenerate?: boolean;
}

export interface VivaProgress {
  projectId: string;
  totalQuestions: number;
  practicedCount: number;
  percentage: number;
  byCategory: Record<string, { total: number; practiced: number }>;
  byDifficulty: Record<string, { total: number; practiced: number }>;
  generationSource: string;
  lastGeneratedAt?: string | null;
}

