export interface Project {
  id: string;
  name: string;
  student_name: string;
  course: string;
  status: 'uploaded' | 'analyzing' | 'completed' | 'failed';
  source_type?: 'zip' | 'git_url';
  git_url?: string | null;
  created_at?: string | null;
}

export interface RepositorySubmitRequest {
  git_url: string;
  student_name?: string;
  course?: string;
}

export interface ProjectSummary {
  source_files: number;
  total_loc: number;
  languages: number;
  documentation_files: number;
  test_files: number;
}

export interface Technology {
  name: string;
  category: string;
  confidence?: 'HIGH' | 'MEDIUM' | 'LOW';
  file_count?: number;
  evidence: string | string[];
}

export interface TechnologyStack {
  technologies: Technology[];
  total_count: number;
  category_count: number;
}

export interface CodeMetrics {
  loc: number;
  code_lines: number;
  comment_lines: number;
  average_complexity: number;
  maximum_complexity: number;
  functions: number;
  classes: number;
  test_files: number;
  test_coverage: string;
  ai_assistance: string;
}

export interface EvaluationDetail {
  score: number | null;
  status: string;
  evidence: string[];
  breakdown?: Record<string, number>;
}

export interface Evaluation {
  overall_score: number | null;
  overall_status?: string | null;
  technical_execution: number | null;
  technical_execution_detail?: EvaluationDetail | null;
  originality: number | null;
  originality_detail?: EvaluationDetail | null;
  documentation_integrity: number | null;
  documentation_integrity_detail?: EvaluationDetail | null;
  development_process: number | null;
  development_process_detail?: EvaluationDetail | null;
}

export interface Strength {
  title: string;
  description: string;
  evidence?: string | null;
}

export interface Improvement {
  title: string;
  severity?: 'info' | 'warning' | 'critical';
  description: string;
  evidence?: string | null;
  metric?: string | number | null;
}

export interface AnalysisMeta {
  status: 'uploaded' | 'analyzing' | 'completed' | 'failed';
  files_analyzed: number;
  files_failed: number;
  total_files: number;
}

export interface ProjectOverview {
  project: Project;
  summary: ProjectSummary;
  technology_stack: TechnologyStack | Technology[];
  code_metrics: CodeMetrics;
  evaluation: Evaluation;
  strengths: Strength[];
  improvements: Improvement[];
  analysis: AnalysisMeta;
}

export interface AnalysisStatus {
  project_id: string;
  status: 'queued' | 'analyzing' | 'completed' | 'failed';
  progress: number;
  current_stage?: string | null;
  error?: string | null;
}

export interface UploadResponse {
  project_id: string;
  project_name: string;
  status: string;
  message: string;
}

