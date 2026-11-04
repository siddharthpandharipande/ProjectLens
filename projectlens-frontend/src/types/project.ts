// ─── Project Status ───────────────────────────────────────────────────────────

export type ProjectStatus =
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'flagged';

// ─── Project (list & detail) ──────────────────────────────────────────────────

export interface Project {
  id: string;
  title: string;
  course?: string;
  team?: string;
  status: ProjectStatus;
  score?: number;          // Only present when status === 'completed'
  createdAt: string;       // ISO 8601
  updatedAt: string;
  processingStage?: string; // e.g. "Structure analyzed"
}

// ─── Upload ───────────────────────────────────────────────────────────────────

export interface UploadPayload {
  file: File;
  course?: string;
  title?: string;
}

export interface UploadResponse {
  projectId: string;
  status: ProjectStatus;
  message?: string;
}

// ─── Statistics summary (dashboard) ──────────────────────────────────────────

export interface DashboardStats {
  totalProjects: number;
  completedProjects: number;
  processingProjects: number;
  flaggedProjects: number;
}

// ─── Phase 2: Project Files & Structure ───────────────────────────────────────

export interface ProjectFile {
  id: number;
  projectId: string;
  relativePath: string;
  filename: string;
  extension: string;
  sizeBytes: number;
  category: string;
  detectedLanguage?: string;
}

export interface FrameworkEvidence {
  name: string;
  category: string;
  evidence: string;
}

export interface LanguageMetric {
  files: number;
  sizeBytes: number;
}

export interface ProjectStructure {
  projectId: string;
  totalFiles: number;
  sourceFilesCount: number;
  totalSourceSizeBytes: number;
  languages: Record<string, LanguageMetric>;
  frameworks: FrameworkEvidence[];
  categoriesSummary: Record<string, number>;
  hasReadme: boolean;
  hasGit: boolean;
  extractedPath?: string;
  createdAt: string;
  updatedAt: string;
}

export interface ProjectFilesResponse {
  projectId: string;
  total: number;
  files: ProjectFile[];
}

// ─── Phase 3: Code Quality Analysis Types ─────────────────────────────────────

export interface QualityFinding {
  ruleId: string;
  title: string;
  explanation: string;
  severity: 'High' | 'Medium' | 'Low' | 'Info';
  filePath: string;
  lineNumber?: number;
  lineRange?: [number, number];
  metricEvidence?: string;
  suggestion?: string;
}

export interface FileMetricItem {
  id?: number;
  relativePath: string;
  language?: string;
  loc: number;
  sloc: number;
  comments: number;
  blank: number;
  functionsCount: number;
  classesCount: number;
  functionNames: string[];
  classNames: string[];
  imports: string[];
  maxNestingDepth?: number;
  avgComplexity?: number;
  maxComplexity?: number;
  maintainabilityIndex?: number;
  hasSyntaxError: boolean;
  syntaxErrorDetails?: string;
}

export interface MetricsSummary {
  totalSourceFiles: number;
  totalLoc: number;
  totalSloc: number;
  totalComments: number;
  totalBlank: number;
  totalFunctions: number;
  totalClasses: number;
  avgComplexity?: number;
  maxComplexity?: number;
  avgMaintainabilityIndex?: number;
  maintainabilityRating?: string;
  syntaxErrorsCount: number;
  totalFindings: number;
}

export interface ScoreFactor {
  name: string;
  weight: number;
  score: number;
  maxScore: number;
  notes: string;
}

export interface ScoreExplanation {
  factors: ScoreFactor[];
  strengths: string[];
  deductions: string[];
  summary: string;
}

export interface LanguageCoverageItem {
  language: string;
  fileCount: number;
  supportedMetrics: string[];
  limitations?: string;
}

export interface CodeQualityResponse {
  id?: number;
  projectId: string;
  status: string;
  score?: number;
  scoreExplanation: ScoreExplanation;
  metricsSummary: MetricsSummary;
  fileMetrics: FileMetricItem[];
  findings: QualityFinding[];
  languageCoverage: LanguageCoverageItem[];
  rulesVersion: string;
  createdAt: string;
  updatedAt: string;
}

// ─── Phase 4: Code Similarity Analysis Types ──────────────────────────────────

export interface FileSimilarityMatchItem {
  currentFile: string;
  matchedFile: string;
  currentLines: [number, number];
  matchedLines: [number, number];
  similarityPercent: number;
  identicalStatements: number;
  currentSnippet: string;
  matchedSnippet: string;
  tokenSimilarity?: number;
  structuralSimilarity?: number;
  semanticSimilarity?: number;
  comparisonMethod: string;
}

export interface ProjectSimilarityMatchItem {
  matchedProjectId: string;
  matchedProjectTitle: string;
  overallSimilarity: number;
  similarityCategory: 'high' | 'moderate' | 'low' | 'minimal';
  tokenSimilarity?: number;
  structuralSimilarity?: number;
  semanticSimilarity?: number;
  sourceCoveragePct: number;
  matchedCoveragePct: number;
  identicalStatements: number;
  matchedFilesCount: number;
  totalComparedFiles: number;
  strongestFileMatches: FileSimilarityMatchItem[];
}

export interface ProjectSimilarityResponse {
  projectId: string;
  status: string;
  overallSimilarity: number;
  similarityCategory: 'high' | 'moderate' | 'low' | 'minimal';
  advisoryNote: string;
  comparedProjectsCount: number;
  comparedFilesCount: number;
  scoringVersion: string;
  methodsUsed: string[];
  limitations: string[];
  matches: ProjectSimilarityMatchItem[];
  createdAt: string;
  updatedAt: string;
}

// ─── Phase 5: Documentation Analysis Types ───────────────────────────────────

export interface DocumentItem {
  id?: number;
  relativePath: string;
  filename: string;
  fileFormat: 'markdown' | 'text' | 'rst' | 'pdf' | 'docx' | string;
  extractedWordCount: number;
  extractedCharCount: number;
  pageCount: number;
  sectionsFound: string[];
  extractionStatus: 'success' | 'partial' | 'empty_scanned_image' | 'corrupt_or_encrypted' | 'unsupported';
  warningMessage?: string;
}

export interface SectionCoverageItem {
  sectionKey: string;
  displayName: string;
  isRequired: boolean;
  isPresent: boolean;
  detectedHeadings: string[];
  foundInFiles: string[];
}

export interface DocumentationQualityMetrics {
  totalDocuments: number;
  totalWords: number;
  recognizedSectionsCount: number;
  requiredSectionsPresent: number;
  requiredSectionsTotal: number;
  hasReadme: boolean;
  hasSetupInstructions: boolean;
  hasTestingSection: boolean;
  pdfPagesExtracted: number;
  repetitionWarnings: string[];
}

export interface DocumentationScoreFactor {
  name: string;
  pointsAwarded: number;
  maxPoints: number;
  notes: string;
}

export interface DocumentationFinding {
  id?: number;
  ruleId: string;
  title: string;
  severity: 'high' | 'medium' | 'low' | 'advisory';
  category: 'technology_consistency' | 'file_reference' | 'implementation_claim' | 'numerical_claim' | 'documentation_quality';
  explanation: string;
  docPath?: string;
  locationRef?: string;
  documentedClaim?: string;
  codeEvidence?: string;
  verificationStatus: 'verified' | 'potential_inconsistency' | 'claim_not_verified' | 'insufficient_evidence';
  facultyGuidance?: string;
}

export interface DocumentationResponse {
  projectId: string;
  status: 'completed' | 'insufficient_evidence' | 'not_started' | 'error' | string;
  preliminaryScore?: number | null;
  scoringVersion: string;
  advisoryNote: string;
  scoreExplanation: {
    status?: string;
    totalScore?: number;
    summary?: string;
    reason?: string;
    factors?: DocumentationScoreFactor[];
  };
  metricsSummary: DocumentationQualityMetrics;
  sectionCoverage: SectionCoverageItem[];
  documents: DocumentItem[];
  findings: DocumentationFinding[];
  extractionWarnings: string[];
  limitations: string[];
  createdAt: string;
  updatedAt: string;
}

// ─── Phase 6: Git Development History Types ─────────────────────────────────

export interface CommitRecord {
  commitHash: string;
  shortHash: string;
  committedAt: string;
  authorName: string;
  authorEmail: string;
  subject: string;
  filesChangedCount: number;
  linesAdded: number;
  linesDeleted: number;
  isMerge: boolean;
  changedFiles: string[];
}

export interface ContributorStat {
  name: string;
  email: string;
  commitCount: number;
  additions: number;
  deletions: number;
  percentage: number;
}

export interface GitFinding {
  id?: number;
  signalId: string;
  title: string;
  severity: 'high' | 'medium' | 'low' | 'advisory' | 'info' | string;
  category: 'commit_concentration' | 'timestamp_anomaly' | 'history_duration' | 'dormancy_gap' | 'contributor_distribution' | string;
  explanation: string;
  evidence: Record<string, unknown>;
  facultyGuidance?: string | null;
}

export interface GitHistorySummary {
  totalCommits: number;
  distinctContributorsCount: number;
  firstCommitAt?: string | null;
  lastCommitAt?: string | null;
  durationDays: number;
  totalFilesChanged: number;
  totalAdditions: number;
  totalDeletions: number;
  avgTimeBetweenCommitsHours?: number | null;
  medianTimeBetweenCommitsHours?: number | null;
  largestCommitSharePercent?: number | null;
  top3CommitSharePercent?: number | null;
  activityByDay: Record<string, number>;
  activityByWeekday: Record<string, number>;
  sizeDistribution: Record<string, number>;
  contributors: ContributorStat[];
}

export interface GitHistoryResponse {
  projectId: string;
  status: 'completed' | 'no_git_repository' | 'empty_repository' | 'corrupt_git_metadata' | 'limit_exceeded' | 'error' | 'not_started' | string;
  availability: 'available' | 'unavailable' | 'empty' | 'corrupt' | string;
  isShallow: boolean;
  analysisVersion: string;
  advisoryNote: string;
  summary?: GitHistorySummary | null;
  timeline: CommitRecord[];
  findings: GitFinding[];
  limitations: string[];
  createdAt: string;
  updatedAt: string;
}

