export interface Project {
  id: string;
  name: string;
  student_name: string;
  course: string;
  status: 'uploaded' | 'analyzing' | 'completed' | 'failed';
  created_at?: string | null;
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
  category: 'language' | 'framework' | 'database' | 'tool';
  evidence: string;
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

export interface Evaluation {
  overall_score: number | null;
  technical_execution: number | null;
  originality: number | null;
  documentation_integrity: number | null;
  development_process: number | null;
}

export interface Strength {
  title: string;
  description: string;
}

export interface Improvement {
  title: string;
  description: string;
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
  technology_stack: Technology[];
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
