// ─── Analysis ─────────────────────────────────────────────────────────────────

export type ModuleStatus = 'not_started' | 'processing' | 'completed' | 'failed' | 'unavailable';

export interface AnalysisModule {
  name: string;
  status: ModuleStatus;
}

// ─── Code Quality ────────────────────────────────────────────────────────────

export interface CodeIssue {
  severity: 'critical' | 'warning' | 'info' | 'style';
  file: string;
  ruleId: string;
  description: string;
}

export interface CodeQualityResult {
  linesOfCode: number;
  languageBreakdown: Record<string, number>;
  modulesAndClasses: number;
  filesCount: number;
  cyclomaticComplexityAvg: number;
  maintainabilityScore?: string;
  issues: CodeIssue[];
}

// ─── Similarity ──────────────────────────────────────────────────────────────

export interface SimilarityMatch {
  matchedProject: string;
  matchedFile: string;
  currentFile: string;
  currentLines: [number, number];
  matchedLines: [number, number];
  similarityPercent: number;
  identicalStatements: number;
  currentSnippet: string;
  matchedSnippet: string;
}

export interface SimilarityResult {
  overallSimilarity: number;
  matches: SimilarityMatch[];
  advisoryNote: string;
}

// ─── Documentation & Development ─────────────────────────────────────────────

export interface DocCheck {
  section: string;
  claim: string;
  actual: string;
  status: 'verified' | 'discrepancy' | 'partial';
}

export interface CommitWeek {
  week: number;
  count: number;
}

export interface DocumentationResult {
  docChecks: DocCheck[];
  commitHistory?: CommitWeek[];
  totalCommits?: number;
  commitWeeks?: number;
  peakWeek?: number;
  peakCount?: number;
  growthLabel?: string;
  preliminaryScore?: number | null;
  status?: string;
  totalDocuments?: number;
  totalWords?: number;
  recognizedSections?: number;
  metricsSummary?: import('./project').DocumentationQualityMetrics;
  sectionCoverage?: import('./project').SectionCoverageItem[];
  findings?: import('./project').DocumentationFinding[];
  documents?: import('./project').DocumentItem[];
}

// ─── AI Assistance & Innovation ──────────────────────────────────────────────

export interface AIAssistanceResult {
  id?: number;
  projectId: string;
  analysisStatus: string;
  advisoryCategory: string;
  evidenceSummary: AIAssistanceSignal[];
  rulesVersion: string;
  llmProvider?: string | null;
  llmModel?: string | null;
  llmInterpretationStatus?: string | null;
  structuredInterpretation: AIAssistanceInterpretation;
  limitations: string[];
  createdAt: string;
  updatedAt: string;
}

export interface AIAssistanceSignal {
  signalId: string;
  signalCategory: string;
  evidenceSource: string;
  observedValue: string;
  explanation: string;
  confidence?: number | null;
  alternativeExplanations: string[];
  availabilityStatus: string;
}

export interface LLMErrorInfo {
  error_type:
    | 'auth_invalid_key'
    | 'account_quota_exceeded'
    | 'upstream_provider_overloaded'
    | 'service_unavailable'
    | 'network_error'
    | 'timeout'
    | 'configuration_missing'
    | string;
  status_code?: number | null;
  title?: string;
  subtitle?: string;
  user_message?: string;
  recommended_action?: string;
  limit_source?: string | null;
  provider_code?: string | null;
}

export interface AIAssistanceInterpretation {
  interpretation_status?: string;
  executive_summary?: string;
  explanation_of_patterns?: string;
  evidence_references?: Array<{ signal_id: string; observation: string }>;
  alternative_explanations?: string[];
  faculty_follow_up_recommendations?: string[];
  limitations?: string[];
  fact_vs_interpretation?: {
    facts?: string[];
    interpretation?: string[];
    speculation?: string[];
  };
  llm_error?: LLMErrorInfo;
}

// ─── Innovation & Distinction Analysis ────────────────────────────────────────

export type InnovationEvidenceType =
  | 'verified_match'
  | 'documented_feature'
  | 'detected_implementation'
  | 'unverified_claim'
  | 'insufficient_information';

export interface FeatureEvidence {
  name: string;
  description: string;
  evidence_type: InnovationEvidenceType;
  doc_reference?: string | null;
  code_reference?: string | null;
}

export interface TechnologyStack {
  languages: string[];
  frameworks: string[];
  libraries: string[];
  databases: string[];
  algorithms: string[];
}

export interface ArchitectureInformation {
  frontend_components: string[];
  backend_components: string[];
  database_structure: string[];
  modules: string[];
}

export interface ClaimedContribution {
  claims: string[];
  supporting_evidence: string[];
  verification_needed: string[];
}

export interface InnovationProfile {
  problemStatement: string;
  domain: string;
  targetUsers: string[];
  proposedSolution: string;
  features: FeatureEvidence[];
  technologyStack: TechnologyStack;
  architecture: ArchitectureInformation;
  claimedContribution: ClaimedContribution;
  hasDocumentation: boolean;
  isEmpty: boolean;
  isSufficient: boolean;
}

export interface InnovationMatch {
  comparedProjectId: string;
  comparedProjectTitle: string;
  problemSimilarity: number;
  solutionSimilarity: number;
  featureSimilarity: number;
  technologyOverlap: number;
  technicalApproachSimilarity: number;
  overallSimilarity: number;
  differenceSummary?: string | null;
  evidenceReferences: Array<{ dimension: string; observation: string }>;
}

export interface InnovationDimensionScores {
  problem_distinctiveness?: number;
  solution_distinctiveness?: number;
  feature_differentiation?: number;
  technical_contribution?: number;
  evidence_supporting_claim?: number;
  max_cohort_similarity?: number;
  average_cohort_similarity?: number;
  [key: string]: number | undefined;
}

export interface InnovationInterpretation {
  interpretation_status?: string;
  innovation_summary?: string;
  problem_understanding?: string;
  proposed_solution_understanding?: string;
  potential_contributions?: string[];
  distinctive_elements?: string[];
  cohort_comparison_interpretation?: string;
  evidence_references?: Array<{ evidence_id: string; observation: string }>;
  alternative_explanations?: string[];
  faculty_follow_up_recommendations?: string[];
  limitations?: string[];
  llm_error?: LLMErrorInfo;
}

export type InnovationLimitations = string[];

export interface InnovationAnalysisResponse {
  id?: number;
  projectId: string;
  analysisStatus: string;
  advisoryCategory: string;
  profile: InnovationProfile;
  cohortSize: number;
  comparisonMethod: string;
  matches: InnovationMatch[];
  dimensionScores: InnovationDimensionScores;
  limitations: InnovationLimitations;
  rulesVersion: string;
  llmProvider?: string | null;
  llmModel?: string | null;
  llmInterpretationStatus?: string | null;
  structuredInterpretation: InnovationInterpretation;
  createdAt: string;
  updatedAt: string;
}

// ─── Viva Questions ──────────────────────────────────────────────────────────

export interface VivaQuestion {
  id: string;
  category: string;
  question: string;
  context?: string;
}

// ─── Evaluation Report ───────────────────────────────────────────────────────

export interface ScoreBreakdown {
  dimension: string;
  score: number;
  maxScore: number;
  notes?: string;
}

export interface EvaluationReport {
  overallScore: number;
  grade?: string;
  scoreBreakdown: ScoreBreakdown[];
  facultyNotes?: string;
  reportAvailable: boolean;
  reportUrl?: string;
}

// ─── Full Analysis Bundle ─────────────────────────────────────────────────────

export interface ProjectAnalysis {
  projectId: string;
  modules: AnalysisModule[];
  codeQuality?: CodeQualityResult;
  similarity?: SimilarityResult;
  documentation?: DocumentationResult;
  developmentHistory?: import('./project').GitHistoryResponse | null;
  aiAssistance?: AIAssistanceResult | null;
  innovation?: InnovationAnalysisResponse | null;
  vivaQuestions?: VivaQuestion[];
  evaluationReport?: EvaluationReport;
}
