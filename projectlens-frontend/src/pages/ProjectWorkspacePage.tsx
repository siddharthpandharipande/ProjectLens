import { useState, useEffect, useCallback, Fragment } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Clock, Download, RefreshCw, CheckCircle, AlertTriangle,
  Edit3, ChevronRight, FileCode, Layers, GitBranch,
  BookOpen, FolderCheck, ChevronDown, ChevronUp, Database,
  Activity, ShieldAlert, Info, SlidersHorizontal, Shield, Sparkles, Lightbulb,
  Award, Cpu, Boxes, Target, Users, HelpCircle, Code2, AlertCircle, FileText,
  Zap, GraduationCap, Flame, Eye, EyeOff, CheckSquare, Square
} from 'lucide-react';
import {
  generateVivaQuestions,
  fetchVivaQuestions,
  updateVivaPracticeStatus,
  regenerateVivaQuestion,
  fetchVivaProgress,
} from '../services/vivaApi';
import type {
  VivaQuestion as FullVivaQuestion,
  VivaQuestionSet,
  VivaMode,
  VivaProgress,
} from '../types/viva';
import {
  fetchProject,
  fetchProjectStructure,
  reparseProject,
  fetchProjectFiles,
  fetchCodeQuality,
  triggerCodeQualityAnalysis,
  fetchSimilarity,
  triggerSimilarityAnalysis,
  fetchDocumentation,
  triggerDocumentationAnalysis,
  fetchDevelopmentHistory,
  triggerDevelopmentHistoryAnalysis,
} from '../services/projectsApi';
import {
  fetchAnalysis,
  downloadReport,
  triggerEvaluation,
  downloadEvaluationJson,
  triggerAIAssistance,
  fetchAIAssistance,
  fetchInnovationAnalysis,
  triggerInnovationAnalysis,
} from '../services/analysisApi';
import type {
  Project,
  ProjectStructure,
  ProjectFile,
  CodeQualityResponse,
  ProjectSimilarityResponse,
  DocumentationResponse,
  GitHistoryResponse,
} from '../types/project';
import type {
  ProjectAnalysis,
  AIAssistanceResult,
  AIAssistanceSignal,
  InnovationAnalysisResponse,
  LLMErrorInfo,
} from '../types/analysis';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorBanner from '../components/ui/ErrorBanner';
import UnavailablePanel from '../components/ui/UnavailablePanel';
import EmptyState from '../components/ui/EmptyState';
import ErrorBoundary from '../components/ui/ErrorBoundary';

// ─── Tab definitions ──────────────────────────────────────────────────────────
const TABS = [
  { id: 'overview', label: '1. Overview' },
  { id: 'code', label: '2. Code Quality' },
  { id: 'similarity', label: '3. Similarity' },
  { id: 'docs', label: '4. Documentation & Development' },
  { id: 'ai', label: '5. AI Assistance & Innovation' },
  { id: 'viva', label: '6. Viva Questions' },
  { id: 'report', label: '7. Evaluation Report' },
] as const;

type TabId = typeof TABS[number]['id'];

// ─── Helpers ──────────────────────────────────────────────────────────────────
function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });
  } catch { return iso; }
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

// ─── Individual tab panels ────────────────────────────────────────────────────

function OverviewTab({
  project,
  analysis,
  structure,
  codeQuality,
  onReparse,
  parsing,
}: {
  project: Project;
  analysis: ProjectAnalysis | null;
  structure: ProjectStructure | null;
  codeQuality: CodeQualityResponse | null;
  onReparse: () => void;
  parsing: boolean;
}) {
  const [showFileInventory, setShowFileInventory] = useState(false);
  const [fileList, setFileList] = useState<ProjectFile[]>([]);
  const [filesLoading, setFilesLoading] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  const loadFiles = useCallback(async () => {
    if (!project.id) return;
    setFilesLoading(true);
    try {
      const res = await fetchProjectFiles(project.id, selectedCategory === 'all' ? undefined : selectedCategory, 200);
      setFileList(res.files);
    } catch {
      // ignore
    } finally {
      setFilesLoading(false);
    }
  }, [project.id, selectedCategory]);

  useEffect(() => {
    if (showFileInventory) {
      loadFiles();
    }
  }, [showFileInventory, loadFiles]);

  const cq = analysis?.codeQuality;
  const sim = analysis?.similarity;
  const ai = analysis?.aiAssistance;

  const totalSourceFiles = structure?.sourceFilesCount || 0;

  return (
    <div className="flex flex-col gap-6">

      {/* ── Phase 2: Codebase Structure & Technology Profile ── */}
      <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="bg-[#ffe600] border-b-2 border-[#121212] px-4 py-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Layers size={18} className="text-[#1c1b1b]" />
            <span className="font-display font-bold uppercase tracking-wide text-sm">
              Codebase Structure &amp; Technology Profile
            </span>
          </div>
          <div className="flex items-center gap-2">
            {structure && (
              <span className="font-mono text-[10px] font-bold bg-white px-2 py-0.5 border border-[#121212]" style={{ boxShadow: '1px 1px 0px #121212' }}>
                {structure.totalFiles} FILES INDEXED
              </span>
            )}
            <button
              onClick={onReparse}
              disabled={parsing}
              className="font-mono text-[10px] font-bold bg-[#F2ECE1] hover:bg-white px-2.5 py-1 border border-[#121212] flex items-center gap-1 cursor-pointer transition-all disabled:opacity-50"
              style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
              title="Re-extract and re-parse repository files"
            >
              <RefreshCw size={11} className={parsing ? 'animate-spin' : ''} />
              {parsing ? 'Parsing...' : 'Re-analyze'}
            </button>
          </div>
        </div>

        <div className="p-6">
          {structure ? (
            <div className="flex flex-col gap-6">
              {/* Summary KPIs */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block">
                    Source Code Files
                  </span>
                  <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
                    {structure.sourceFilesCount}
                  </div>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {formatBytes(structure.totalSourceSizeBytes)}
                  </span>
                </div>

                <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block">
                    Total Indexed Files
                  </span>
                  <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
                    {structure.totalFiles}
                  </div>
                  <span className="font-mono text-[10px] text-[#4b4731]">All categories</span>
                </div>

                <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block">
                    Documentation
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    <BookOpen size={16} className={structure.hasReadme ? 'text-[#006b58]' : 'text-[#7c775f]'} />
                    <span className="font-display font-bold text-sm text-[#1c1b1b]">
                      {structure.hasReadme ? 'README Verified' : 'No README'}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {structure.categoriesSummary['Documentation'] || 0} doc files
                  </span>
                </div>

                <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
                  <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block">
                    Version Control
                  </span>
                  <div className="flex items-center gap-1.5 mt-1">
                    <GitBranch size={16} className={structure.hasGit ? 'text-[#006b58]' : 'text-[#7c775f]'} />
                    <span className="font-display font-bold text-sm text-[#1c1b1b]">
                      {structure.hasGit ? 'Git Active' : 'No .git metadata'}
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {structure.hasGit ? 'Commit logs available' : 'Archive submission'}
                  </span>
                </div>
              </div>

              {/* Detected Languages & Stack */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Languages */}
                <div className="p-4 bg-[#FAF6EE] border-2 border-[#121212]">
                  <div className="flex items-center justify-between mb-3 border-b border-[#121212] pb-2">
                    <span className="font-display font-bold text-sm text-[#1c1b1b] flex items-center gap-1.5">
                      <FileCode size={15} />
                      Detected Programming Languages
                    </span>
                    <span className="font-mono text-[10px] font-bold text-[#4b4731]">
                      {Object.keys(structure.languages).length} DETECTED
                    </span>
                  </div>

                  {Object.keys(structure.languages).length > 0 ? (
                    <div className="flex flex-col gap-2.5">
                      {Object.entries(structure.languages).map(([lang, metric]) => {
                        const pct = totalSourceFiles > 0 ? Math.round((metric.files / totalSourceFiles) * 100) : 0;
                        return (
                          <div key={lang} className="flex flex-col gap-1">
                            <div className="flex items-center justify-between font-mono text-[11px]">
                              <span className="font-bold text-[#1c1b1b]">{lang}</span>
                              <span className="text-[#4b4731]">
                                {metric.files} files ({pct}%) • {formatBytes(metric.sizeBytes)}
                              </span>
                            </div>
                            <div className="w-full h-2 bg-white border border-[#121212] overflow-hidden">
                              <div
                                className="h-full bg-[#ffe600] border-r border-[#121212]"
                                style={{ width: `${Math.max(pct, 4)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="font-sans text-xs text-[#4b4731] italic">
                      No recognized programming language source files detected.
                    </p>
                  )}
                </div>

                {/* Frameworks & Manifest Evidence */}
                <div className="p-4 bg-[#FAF6EE] border-2 border-[#121212]">
                  <div className="flex items-center justify-between mb-3 border-b border-[#121212] pb-2">
                    <span className="font-display font-bold text-sm text-[#1c1b1b] flex items-center gap-1.5">
                      <FolderCheck size={15} />
                      Detected Frameworks &amp; Manifests
                    </span>
                    <span className="font-mono text-[10px] font-bold text-[#4b4731]">
                      {structure.frameworks.length} IDENTIFIED
                    </span>
                  </div>

                  {structure.frameworks.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {structure.frameworks.map((fw, idx) => (
                        <div
                          key={idx}
                          className="bg-white border border-[#121212] p-2 flex flex-col gap-0.5"
                          style={{ boxShadow: '2px 2px 0px #121212' }}
                        >
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-display font-bold text-xs text-[#1c1b1b]">{fw.name}</span>
                            <span className="font-mono text-[9px] bg-[#D8B4FE] text-[#1c1b1b] px-1 border border-[#121212]">
                              {fw.category}
                            </span>
                          </div>
                          <span className="font-mono text-[10px] text-[#4b4731]">
                            Evidence: {fw.evidence}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="font-sans text-xs text-[#4b4731] italic">
                      No known frameworks found in repository manifests.
                    </p>
                  )}
                </div>
              </div>

              {/* Categories summary pills */}
              <div>
                <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#4b4731] block mb-2">
                  File Inventory by Category
                </span>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(structure.categoriesSummary).map(([cat, count]) => (
                    <div
                      key={cat}
                      className="bg-[#F2ECE1] border-[1.5px] border-[#121212] px-3 py-1 flex items-center gap-2 font-mono text-[11px]"
                      style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
                    >
                      <span className="font-bold text-[#1c1b1b]">{cat}:</span>
                      <span className="bg-white px-1.5 py-0.2 border border-[#121212] font-bold">{count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Collapsible File Inventory Explorer */}
              <div className="border-t-2 border-[#121212] pt-4">
                <button
                  onClick={() => setShowFileInventory(!showFileInventory)}
                  className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-2"
                >
                  <Database size={14} />
                  {showFileInventory ? 'Hide File Inventory' : `Explore Extracted File Inventory (${structure.totalFiles} files)`}
                  {showFileInventory ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>

                {showFileInventory && (
                  <div className="mt-4 border-2 border-[#121212] bg-[#FAF6EE] p-4">
                    <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
                      <span className="font-display font-bold text-sm text-[#1c1b1b]">
                        Extracted Repository Files
                      </span>
                      <div className="flex items-center gap-2 font-mono text-[11px]">
                        <span>Filter:</span>
                        <select
                          className="bg-white border border-[#121212] px-2 py-1 font-mono text-[11px] outline-none"
                          value={selectedCategory}
                          onChange={(e) => setSelectedCategory(e.target.value)}
                        >
                          <option value="all">All Categories</option>
                          <option value="Source Code">Source Code</option>
                          <option value="Documentation">Documentation</option>
                          <option value="Configuration">Configuration</option>
                          <option value="Dataset">Dataset</option>
                          <option value="Dependency or Environment File">Dependencies</option>
                        </select>
                      </div>
                    </div>

                    {filesLoading ? (
                      <div className="py-6 flex justify-center">
                        <LoadingSpinner message="Loading files..." />
                      </div>
                    ) : fileList.length > 0 ? (
                      <div className="max-h-80 overflow-y-auto border border-[#121212] bg-white">
                        <table className="w-full text-left border-collapse font-mono text-[11px]">
                          <thead>
                            <tr className="bg-[#ffe600] border-b border-[#121212] font-bold text-[10px] uppercase">
                              <th className="p-2 border-r border-[#121212]">Relative Path</th>
                              <th className="p-2 border-r border-[#121212]">Category</th>
                              <th className="p-2 border-r border-[#121212]">Language</th>
                              <th className="p-2">Size</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-[#121212]">
                            {fileList.map((f) => (
                              <tr key={f.id} className="hover:bg-[#FAF6EE]">
                                <td className="p-2 border-r border-[#121212] font-bold text-[#1c1b1b] break-all">
                                  {f.relativePath}
                                </td>
                                <td className="p-2 border-r border-[#121212]">
                                  <span className="px-1.5 py-0.5 bg-[#F2ECE1] border border-[#121212] text-[10px]">
                                    {f.category}
                                  </span>
                                </td>
                                <td className="p-2 border-r border-[#121212] text-[#4b4731]">
                                  {f.detectedLanguage || '—'}
                                </td>
                                <td className="p-2 text-[#4b4731] whitespace-nowrap">
                                  {formatBytes(f.sizeBytes)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <p className="font-sans text-xs text-[#4b4731] italic">
                        No files matching selected filter.
                      </p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="py-4 text-center">
              <p className="font-sans text-sm text-[#4b4731] mb-3">
                Project structure has not been analyzed yet.
              </p>
              <button
                onClick={onReparse}
                disabled={parsing}
                className="btn-primary text-xs"
              >
                <RefreshCw size={14} className={parsing ? 'animate-spin' : ''} />
                {parsing ? 'Analyzing Codebase Structure...' : 'Analyze Codebase Structure'}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* ── Architecture Strengths & Faculty Review Signals (Only if real analysis exists) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Strengths */}
        <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="bg-[#F2ECE1] border-b-2 border-[#121212] px-4 py-2 flex items-center justify-between">
            <span className="font-mono text-[11px] font-bold uppercase tracking-widest flex items-center gap-1.5">
              <CheckCircle size={14} className="text-[#006b58]" />
              Architecture &amp; Implementation Strengths
            </span>
          </div>
          <div className="p-4">
            {codeQuality ? (
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-sans text-sm font-bold text-[#1c1b1b]">
                    Preliminary Code Quality Score:
                  </span>
                  <span className="font-mono text-sm font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212]">
                    {codeQuality.score !== null ? `${codeQuality.score} / 100` : 'Insufficient Evidence'}
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4b4731]">
                  {codeQuality.scoreExplanation.summary}
                </p>
                {codeQuality.scoreExplanation.strengths.length > 0 && (
                  <ul className="mt-1 flex flex-col gap-1">
                    {codeQuality.scoreExplanation.strengths.slice(0, 3).map((st, i) => (
                      <li key={i} className="font-sans text-xs text-[#006b58] flex items-center gap-1.5">
                        <CheckCircle size={12} className="shrink-0" />
                        <span>{st}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : cq ? (
              <p className="font-sans text-sm text-[#4b4731]">
                Code Quality Score available. {cq.cyclomaticComplexityAvg !== undefined && `Average cyclomatic complexity: ${cq.cyclomaticComplexityAvg}.`}{' '}
                {cq.issues.filter(i => i.severity === 'critical').length === 0 && 'No critical issues found.'}
              </p>
            ) : (
              <p className="font-sans text-sm text-[#4b4731] italic">
                Advanced code complexity analysis scheduled for Phase 3.
              </p>
            )}
          </div>
        </div>

        {/* Review signals */}
        <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="bg-[#FF5C8D] border-b-2 border-[#121212] px-4 py-2 flex items-center justify-between">
            <span className="font-mono text-[11px] font-bold uppercase tracking-widest flex items-center gap-1.5">
              <AlertTriangle size={14} className="text-[#1c1b1b]" />
              Faculty Review Signals
            </span>
          </div>
          <div className="p-4">
            {sim ? (
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <span className="font-sans text-sm text-[#1c1b1b]">Similarity signal detected</span>
                  <span className="font-mono text-sm font-bold text-[#FF5C8D]">{sim.overallSimilarity}%</span>
                </div>
                <p className="font-sans text-xs text-[#4b4731]">{sim.advisoryNote}</p>
              </div>
            ) : ai ? (
              <p className="font-sans text-sm text-[#4b4731]">
                AI-assistance advisory category: {ai.advisoryCategory}. This is an evidence review signal, not an AI-use probability.
              </p>
            ) : (
              <p className="font-sans text-sm text-[#4b4731] italic">
                Similarity and AI assistance review modules scheduled for subsequent phases.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Metrics row (Only if real Code Quality AST data exists) */}
      {(codeQuality || cq) && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            {
              label: 'Lines of Code',
              value: codeQuality
                ? `${codeQuality.metricsSummary.totalSloc.toLocaleString()} SLOC`
                : cq?.linesOfCode.toLocaleString() ?? '—',
              sub: codeQuality ? `${codeQuality.metricsSummary.totalLoc.toLocaleString()} physical lines` : undefined,
            },
            {
              label: 'Modules & Classes',
              value: codeQuality ? codeQuality.metricsSummary.totalClasses : cq?.modulesAndClasses ?? '—',
            },
            {
              label: 'Avg Complexity',
              value: codeQuality
                ? (codeQuality.metricsSummary.avgComplexity ?? 'N/A')
                : cq?.cyclomaticComplexityAvg ?? '—',
              sub: codeQuality ? `Max CC: ${codeQuality.metricsSummary.maxComplexity ?? 'N/A'}` : undefined,
            },
            {
              label: 'Issues Found',
              value: codeQuality ? codeQuality.findings.length : cq?.issues.length ?? 0,
              highlight: codeQuality
                ? codeQuality.findings.some(f => f.severity === 'High')
                : cq?.issues.some(i => i.severity === 'critical'),
            },
          ].map(({ label, value, sub, highlight }) => (
            <div key={label} className="p-4 bg-[#FAF6EE] border-2 border-[#121212]">
              <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block">{label}</span>
              <div className={`font-display font-bold text-2xl ${highlight ? 'text-[#FF5C8D]' : 'text-[#1c1b1b]'}`}>{value}</div>
              {sub && <span className="font-mono text-[10px] text-[#4b4731]">{sub}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CodeQualityTab({
  codeQuality,
  loading,
  analyzing,
  onAnalyze,
  error,
}: {
  codeQuality: CodeQualityResponse | null;
  loading: boolean;
  analyzing: boolean;
  onAnalyze: () => void;
  error: string | null;
}) {
  const [selectedLanguage, setSelectedLanguage] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [showScoreFactors, setShowScoreFactors] = useState(false);

  if (loading) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-10 flex justify-center items-center">
        <LoadingSpinner message="Loading code quality metrics..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <ErrorBanner
          title="Code Quality Analysis Failed"
          message={error}
          onRetry={onAnalyze}
        />
      </div>
    );
  }

  if (!codeQuality) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-8 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="max-w-xl mx-auto flex flex-col items-center">
          <div className="w-14 h-14 bg-[#ffe600] border-2 border-[#121212] flex items-center justify-center mb-4" style={{ boxShadow: '3px 3px 0px #121212' }}>
            <Activity size={28} className="text-[#1c1b1b]" />
          </div>
          <h2 className="font-display font-bold text-2xl text-[#1c1b1b] mb-2">
            Static AST &amp; Code Quality Analysis
          </h2>
          <p className="font-sans text-sm text-[#4b4731] mb-6">
            Inspect source code structure, functions, classes, cyclomatic complexity, and maintainability index
            using Python's built-in AST and Radon, plus Tree-sitter for TypeScript and Java.
            Code is analyzed safely without compiling or running student scripts.
          </p>
          <button
            onClick={onAnalyze}
            disabled={analyzing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Running Code Quality Analysis...' : 'Run Code Quality Analysis'}
          </button>
        </div>
      </div>
    );
  }

  const { metricsSummary, scoreExplanation, findings, fileMetrics, languageCoverage } = codeQuality;

  // Filtered files
  const filteredFiles = fileMetrics.filter((f) => {
    if (selectedLanguage === 'all') return true;
    return f.language === selectedLanguage;
  });

  // Filtered findings
  const filteredFindings = findings.filter((f) => {
    if (severityFilter === 'all') return true;
    return f.severity === severityFilter;
  });

  const languagesList = Array.from(new Set(fileMetrics.map((f) => f.language || 'Unknown')));

  return (
    <div className="flex flex-col gap-6">

      {/* ── Top Header Card with Preliminary Score ── */}
      <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="bg-[#ffe600] border-b-2 border-[#121212] px-4 py-3 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <Activity size={18} className="text-[#1c1b1b]" />
            <h2 className="font-display font-bold text-base uppercase tracking-wide text-[#1c1b1b]">
              Static Code Quality &amp; AST Analysis
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onAnalyze}
              disabled={analyzing}
              className="font-mono text-[10px] font-bold bg-[#F2ECE1] hover:bg-white px-2.5 py-1 border border-[#121212] flex items-center gap-1 cursor-pointer transition-all disabled:opacity-50"
              style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
              title="Refresh static analysis"
            >
              <RefreshCw size={11} className={analyzing ? 'animate-spin' : ''} />
              {analyzing ? 'Analyzing...' : 'Re-analyze'}
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6 pb-6 border-b-2 border-[#121212]">
            <div className="flex-1">
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block mb-1">
                Analytical Code Quality Score
              </span>
              <div className="flex items-baseline gap-2">
                {codeQuality.score !== null ? (
                  <>
                    <span className="font-display font-bold text-5xl md:text-6xl text-[#1c1b1b] leading-none">
                      {codeQuality.score}
                    </span>
                    <span className="font-display font-bold text-2xl text-[#4b4731]">/100</span>
                  </>
                ) : (
                  <span className="font-display font-bold text-3xl text-[#7c775f]">
                    Insufficient Evidence
                  </span>
                )}
              </div>
              <p className="font-sans text-sm text-[#4b4731] mt-2">
                {scoreExplanation.summary}
              </p>
              <div className="flex flex-wrap items-center gap-2 mt-3 font-mono text-[10px]">
                <span className="bg-[#FAF6EE] px-2 py-0.5 border border-[#121212] font-bold">
                  RULES: {codeQuality.rulesVersion}
                </span>
                <span className="bg-[#FAF6EE] px-2 py-0.5 border border-[#121212]">
                  Updated: {formatDate(codeQuality.updatedAt)}
                </span>
              </div>
            </div>

            <div className="w-full lg:w-80 bg-[#FAF6EE] border-2 border-[#121212] p-3 text-xs font-mono">
              <div className="flex items-center gap-1.5 font-bold mb-1 text-[#1c1b1b]">
                <Info size={14} />
                <span>Faculty Evaluation Notice</span>
              </div>
              <p className="text-[11px] font-sans text-[#4b4731] leading-relaxed">
                This preliminary score evaluates static code health, syntax, cyclomatic complexity,
                and maintainability. It does not determine the final project evaluation grade.
              </p>
              <button
                onClick={() => setShowScoreFactors(!showScoreFactors)}
                className="mt-2 text-[10px] font-bold uppercase text-[#1c1b1b] underline hover:text-[#006b58] cursor-pointer flex items-center gap-1"
              >
                {showScoreFactors ? 'Hide Scoring Factors' : 'View Scoring Factors Breakdown'}
                {showScoreFactors ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
            </div>
          </div>

          {/* Collapsible Score Factors Breakdown */}
          {showScoreFactors && (
            <div className="mt-6 pt-4 border-t border-[#121212] space-y-4">
              <h3 className="font-display font-bold text-sm uppercase text-[#1c1b1b]">
                Deterministic Scoring Factors
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                {scoreExplanation.factors.map((factor, i) => (
                  <div key={i} className="p-3 bg-[#FAF6EE] border border-[#121212] flex flex-col justify-between">
                    <div>
                      <div className="flex justify-between items-start font-mono text-[10px] text-[#4b4731]">
                        <span>{factor.name}</span>
                        <span className="font-bold">{factor.weight}% max</span>
                      </div>
                      <div className="font-display font-bold text-xl text-[#1c1b1b] mt-1">
                        {factor.score} <span className="text-xs font-normal text-[#4b4731]">/ {factor.maxScore}</span>
                      </div>
                    </div>
                    <p className="font-sans text-[11px] text-[#4b4731] mt-2 border-t border-[#121212] pt-1">
                      {factor.notes}
                    </p>
                  </div>
                ))}
              </div>

              {/* Strengths & Deductions split */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                {scoreExplanation.strengths.length > 0 && (
                  <div className="p-3 bg-white border border-[#121212]">
                    <span className="font-mono text-[10px] font-bold uppercase text-[#006b58] block mb-2 flex items-center gap-1">
                      <CheckCircle size={13} />
                      Observed Strengths
                    </span>
                    <ul className="space-y-1 font-sans text-xs text-[#1c1b1b]">
                      {scoreExplanation.strengths.map((s, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-[#006b58] font-bold">•</span>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {scoreExplanation.deductions.length > 0 && (
                  <div className="p-3 bg-white border border-[#121212]">
                    <span className="font-mono text-[10px] font-bold uppercase text-[#FF5C8D] block mb-2 flex items-center gap-1">
                      <AlertTriangle size={13} />
                      Deductions &amp; Observations
                    </span>
                    <ul className="space-y-1 font-sans text-xs text-[#1c1b1b]">
                      {scoreExplanation.deductions.map((d, idx) => (
                        <li key={idx} className="flex items-start gap-1.5">
                          <span className="text-[#FF5C8D] font-bold">•</span>
                          <span>{d}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Key Metrics Summary KPI Grid ── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Source Lines (SLOC)
          </span>
          <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
            {metricsSummary.totalSloc.toLocaleString()}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">
            {metricsSummary.totalLoc.toLocaleString()} physical LOC
          </span>
        </div>

        <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Functions &amp; Methods
          </span>
          <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
            {metricsSummary.totalFunctions}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">AST parsed</span>
        </div>

        <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Classes &amp; Modules
          </span>
          <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
            {metricsSummary.totalClasses}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">Declarations</span>
        </div>

        <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Avg Complexity
          </span>
          <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
            {metricsSummary.avgComplexity !== undefined && metricsSummary.avgComplexity !== null
              ? metricsSummary.avgComplexity
              : 'N/A'}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">
            Max CC: {metricsSummary.maxComplexity ?? 'N/A'}
          </span>
        </div>

        <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Maintainability
          </span>
          <div className="font-display font-bold text-2xl text-[#1c1b1b] mt-0.5">
            {metricsSummary.maintainabilityRating ? `Rank ${metricsSummary.maintainabilityRating}` : 'N/A'}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">
            {metricsSummary.avgMaintainabilityIndex !== undefined && metricsSummary.avgMaintainabilityIndex !== null
              ? `${metricsSummary.avgMaintainabilityIndex} / 100`
              : 'Radon metric'}
          </span>
        </div>

        <div className={`p-3 border-2 border-[#121212] ${findings.some((f) => f.severity === 'High') ? 'bg-[#ffd9df]' : 'bg-[#FAF6EE]'
          }`}>
          <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block">
            Quality Findings
          </span>
          <div className={`font-display font-bold text-2xl mt-0.5 ${findings.some((f) => f.severity === 'High') ? 'text-[#FF5C8D]' : 'text-[#1c1b1b]'
            }`}>
            {findings.length}
          </div>
          <span className="font-mono text-[10px] text-[#4b4731]">
            {findings.filter((f) => f.severity === 'High').length} High severity
          </span>
        </div>
      </div>

      {/* ── Language Coverage & Analysis Limitations Matrix ── */}
      <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="bg-[#F2ECE1] border-b-2 border-[#121212] px-4 py-2 flex items-center justify-between">
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest flex items-center gap-1.5">
            <SlidersHorizontal size={14} />
            Supported Language Coverage &amp; Parser Capabilities
          </span>
          <span className="font-mono text-[10px] text-[#4b4731]">
            {languageCoverage.length} LANGUAGES ANALYZED
          </span>
        </div>
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
          {languageCoverage.map((cov, idx) => (
            <div key={idx} className="p-3 bg-[#FAF6EE] border border-[#121212]">
              <div className="flex items-center justify-between mb-1.5">
                <span className="font-display font-bold text-sm text-[#1c1b1b]">{cov.language}</span>
                <span className="font-mono text-[10px] bg-white px-2 py-0.5 border border-[#121212] font-bold">
                  {cov.fileCount} {cov.fileCount === 1 ? 'file' : 'files'}
                </span>
              </div>
              <div className="flex flex-wrap gap-1 mb-2">
                {cov.supportedMetrics.map((met, mIdx) => (
                  <span
                    key={mIdx}
                    className="font-mono text-[9px] bg-[#D8B4FE] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]"
                  >
                    {met}
                  </span>
                ))}
              </div>
              {cov.limitations && (
                <p className="font-sans text-[11px] text-[#4b4731] border-t border-[#121212] pt-1.5 mt-1.5">
                  <span className="font-bold">Coverage note:</span> {cov.limitations}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Per-File Metrics Table ── */}
      <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="bg-[#F2ECE1] border-b-2 border-[#121212] px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest flex items-center gap-1.5">
            <FileCode size={14} />
            Per-File Code Metrics ({fileMetrics.length} Source Files)
          </span>

          {languagesList.length > 1 && (
            <div className="flex items-center gap-1.5 font-mono text-[11px]">
              <span>Filter:</span>
              <select
                className="bg-white border border-[#121212] px-2 py-0.5 font-mono text-[11px] outline-none"
                value={selectedLanguage}
                onChange={(e) => setSelectedLanguage(e.target.value)}
              >
                <option value="all">All Languages</option>
                {languagesList.map((l) => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="overflow-x-auto max-h-96">
          <table className="w-full text-left border-collapse font-mono text-[11px]">
            <thead>
              <tr className="bg-[#ffe600] border-b-2 border-[#121212] font-bold text-[10px] uppercase">
                <th className="p-2.5 border-r border-[#121212]">File Path</th>
                <th className="p-2.5 border-r border-[#121212]">Language</th>
                <th className="p-2.5 border-r border-[#121212]">Lines (SLOC/LOC)</th>
                <th className="p-2.5 border-r border-[#121212]">Fn / Class</th>
                <th className="p-2.5 border-r border-[#121212]">Complexity (Avg/Max)</th>
                <th className="p-2.5 border-r border-[#121212]">Maintainability</th>
                <th className="p-2.5">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#121212] bg-white">
              {filteredFiles.map((f, i) => (
                <tr key={i} className="hover:bg-[#FAF6EE]">
                  <td className="p-2.5 border-r border-[#121212] font-bold text-[#1c1b1b] break-all">
                    {f.relativePath}
                  </td>
                  <td className="p-2.5 border-r border-[#121212]">
                    <span className="px-1.5 py-0.5 bg-[#FAF6EE] border border-[#121212] text-[10px]">
                      {f.language || 'Unknown'}
                    </span>
                  </td>
                  <td className="p-2.5 border-r border-[#121212] text-[#4b4731]">
                    <strong>{f.sloc}</strong> / {f.loc}
                  </td>
                  <td className="p-2.5 border-r border-[#121212] text-[#4b4731]">
                    {f.functionsCount} / {f.classesCount}
                  </td>
                  <td className="p-2.5 border-r border-[#121212]">
                    {f.avgComplexity !== undefined && f.avgComplexity !== null ? (
                      <span className={`px-1.5 py-0.5 border border-[#121212] font-bold text-[10px] ${f.avgComplexity > 10 ? 'bg-[#FF5C8D] text-white' :
                        f.avgComplexity > 5 ? 'bg-[#ffe600] text-[#1c1b1b]' :
                          'bg-[#00E5BE] text-[#1c1b1b]'
                        }`}>
                        {f.avgComplexity} (max {f.maxComplexity ?? f.avgComplexity})
                      </span>
                    ) : (
                      <span className="text-[#7c775f]">—</span>
                    )}
                  </td>
                  <td className="p-2.5 border-r border-[#121212]">
                    {f.maintainabilityIndex !== undefined && f.maintainabilityIndex !== null ? (
                      <span className="font-bold text-[#1c1b1b]">
                        {f.maintainabilityIndex.toFixed(1)} / 100
                      </span>
                    ) : (
                      <span className="text-[#7c775f]">—</span>
                    )}
                  </td>
                  <td className="p-2.5">
                    {f.hasSyntaxError ? (
                      <span className="px-1.5 py-0.5 bg-[#FF5C8D] text-white border border-[#121212] font-bold text-[9px]">
                        SYNTAX ERROR
                      </span>
                    ) : (
                      <span className="px-1.5 py-0.5 bg-[#00E5BE] text-[#1c1b1b] border border-[#121212] font-bold text-[9px]">
                        VALID
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Flagged Code Quality Findings ── */}
      <div className="bg-white border-[2.5px] border-[#121212]" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="bg-[#ffe600] border-b-2 border-[#121212] px-4 py-2.5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <ShieldAlert size={16} className="text-[#1c1b1b]" />
            <h3 className="font-display font-bold text-sm uppercase text-[#1c1b1b]">
              Flagged Code Quality Findings ({findings.length})
            </h3>
          </div>

          <div className="flex items-center gap-1 font-mono text-[10px]">
            {['all', 'High', 'Medium', 'Low', 'Info'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSeverityFilter(sev)}
                className={`px-2 py-0.5 border border-[#121212] cursor-pointer font-bold ${severityFilter === sev ? 'bg-[#1c1b1b] text-white' : 'bg-white text-[#1c1b1b]'
                  }`}
              >
                {sev.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {filteredFindings.length > 0 ? (
            <div className="flex flex-col gap-3">
              {filteredFindings.map((finding, idx) => (
                <div
                  key={idx}
                  className="p-4 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col gap-2"
                  style={{ boxShadow: '2px 2px 0px #121212' }}
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 border border-[#121212] font-mono text-[10px] font-bold uppercase ${finding.severity === 'High' ? 'bg-[#FF5C8D] text-white' :
                        finding.severity === 'Medium' ? 'bg-[#ffe600] text-[#1c1b1b]' :
                          finding.severity === 'Low' ? 'bg-[#D8B4FE] text-[#1c1b1b]' :
                            'bg-[#F2ECE1] text-[#1c1b1b]'
                        }`}>
                        {finding.severity}
                      </span>
                      <span className="font-mono text-[11px] bg-white px-2 py-0.5 border border-[#121212] font-bold">
                        {finding.ruleId}
                      </span>
                      <span className="font-mono text-[11px] text-[#4b4731]">
                        {finding.filePath}
                        {finding.lineNumber ? `:${finding.lineNumber}` : ''}
                      </span>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                      {finding.title}
                    </h4>
                    <p className="font-sans text-sm text-[#4b4731] mt-0.5">
                      {finding.explanation}
                    </p>
                  </div>

                  {finding.metricEvidence && (
                    <div className="bg-white border border-[#121212] px-2.5 py-1 font-mono text-[11px] text-[#1c1b1b]">
                      <strong>Evidence:</strong> {finding.metricEvidence}
                    </div>
                  )}

                  {finding.suggestion && (
                    <div className="font-sans text-xs text-[#006b58] bg-[#E8F8F5] border border-[#006b58] px-2.5 py-1">
                      <strong>Suggestion:</strong> {finding.suggestion}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-6">
              <CheckCircle size={32} className="mx-auto text-[#006b58] mb-2" />
              <p className="font-display font-bold text-base text-[#1c1b1b]">
                No findings matching filter
              </p>
              <p className="font-sans text-xs text-[#4b4731]">
                {findings.length === 0
                  ? 'All analyzed source code meets baseline structural and complexity thresholds.'
                  : 'Try selecting "All" severities to view other review signals.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function SimilarityTab({
  similarity,
  loading,
  analyzing,
  error,
  onAnalyze,
}: {
  similarity: ProjectSimilarityResponse | null;
  loading: boolean;
  analyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
}) {
  if (loading) {
    return <LoadingSpinner message="Loading code similarity analysis..." />;
  }

  const matches = similarity?.matches || [];
  const status = similarity?.status || 'not_started';
  const hasAnalysis = similarity && status !== 'not_started';

  return (
    <div className="flex flex-col gap-6">
      {/* ── Top Header & Actions ── */}
      <div
        className="bg-white border-[2.5px] border-[#121212] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-[10px] font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212] uppercase">
              Phase 4 Engine
            </span>
            <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
              {similarity?.scoringVersion || 'v1.0-hierarchical-ast-tokens'}
            </span>
          </div>
          <h2 className="font-display font-bold text-xl text-[#1c1b1b]">
            Cohort Code Similarity Analysis
          </h2>
          <p className="font-sans text-sm text-[#4b4731]">
            Cross-checking submitted source files against existing project submissions in the ProjectLens database.
          </p>
        </div>

        <button
          className="btn-primary flex items-center justify-center gap-2 cursor-pointer shrink-0 disabled:opacity-50"
          onClick={onAnalyze}
          disabled={analyzing}
        >
          <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
          {analyzing ? 'Comparing Codebase...' : hasAnalysis ? 'Re-run Similarity Analysis' : 'Run Similarity Analysis'}
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={onAnalyze} />}

      {/* ── 4-Card Comparison Stats Row ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div className="bg-white border-2 border-[#121212] p-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
          <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">Cohort Projects</span>
          <span className="font-display font-bold text-2xl text-[#1c1b1b]">
            {similarity?.comparedProjectsCount ?? 0}
          </span>
          <span className="font-mono text-[10px] text-[#4b4731] block">Eligible in Database</span>
        </div>

        <div className="bg-white border-2 border-[#121212] p-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
          <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">Files Compared</span>
          <span className="font-display font-bold text-2xl text-[#1c1b1b]">
            {similarity?.comparedFilesCount ?? 0}
          </span>
          <span className="font-mono text-[10px] text-[#4b4731] block">Compatible Source Files</span>
        </div>

        <div className="bg-white border-2 border-[#121212] p-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
          <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">Max Similarity</span>
          <div className="flex items-baseline gap-1">
            <span className="font-display font-bold text-2xl text-[#1c1b1b]">
              {similarity?.overallSimilarity !== undefined ? similarity.overallSimilarity : 0}
            </span>
            <span className="font-display font-bold text-xs text-[#4b4731]">%</span>
          </div>
          <span className="font-mono text-[10px] text-[#4b4731] block">Strongest Cohort Match</span>
        </div>

        <div className="bg-white border-2 border-[#121212] p-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
          <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">Signal Category</span>
          <div className="mt-1">
            <span
              className={`font-mono text-[11px] font-bold px-2 py-0.5 border border-[#121212] uppercase ${similarity?.similarityCategory === 'high'
                ? 'bg-[#FF5C8D] text-white'
                : similarity?.similarityCategory === 'moderate'
                  ? 'bg-[#ffe600] text-[#1c1b1b]'
                  : similarity?.similarityCategory === 'low'
                    ? 'bg-[#00E5BE] text-[#1c1b1b]'
                    : 'bg-[#F2ECE1] text-[#4b4731]'
                }`}
            >
              {similarity?.similarityCategory ? similarity.similarityCategory.toUpperCase() : 'NONE'}
            </span>
          </div>
          <span className="font-mono text-[10px] text-[#4b4731] block mt-1">Review Guidance Signal</span>
        </div>
      </div>

      {/* ── State: Not Started ── */}
      {!hasAnalysis && (
        <EmptyState
          title="Similarity Analysis Not Executed"
          description="Click 'Run Similarity Analysis' above to compare this submission against other eligible student projects in the database using token shingles and hierarchical AST trees."
          actionLabel={analyzing ? 'Analyzing...' : 'Run Similarity Analysis'}
          onAction={onAnalyze}
        />
      )}

      {/* ── State: No Candidates ── */}
      {hasAnalysis && status === 'no_candidates' && (
        <div
          className="bg-white border-[2.5px] border-[#121212] p-6 text-center"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <Database size={36} className="mx-auto text-[#4b4731] mb-2" />
          <h3 className="font-display font-bold text-lg text-[#1c1b1b] mb-1">
            No Other Cohort Projects Available
          </h3>
          <p className="font-sans text-sm text-[#4b4731] max-w-lg mx-auto mb-4">
            Code similarity analysis compares against other student submissions stored in this ProjectLens database.
            Currently, no other projects with indexed source files exist. Once additional projects are uploaded for this course,
            cohort comparisons can be run immediately.
          </p>
          <p className="font-mono text-[10px] text-[#7c775f] uppercase tracking-wide">
            Self-comparison and external internet scraping are strictly disabled by design.
          </p>
        </div>
      )}

      {/* ── State: Completed with results ── */}
      {hasAnalysis && status === 'completed' && (
        <>
          {/* Advisory Signal Banner */}
          <div
            className="bg-[#ffd9df] border-[2.5px] border-[#121212] p-4 flex items-start gap-4"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <AlertTriangle size={28} className="text-[#1c1b1b] shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <h3 className="font-display font-bold text-base text-[#1c1b1b]">
                  Advisory Signal: {similarity.overallSimilarity}% Highest Cohort Similarity
                </h3>
                <span className="bg-[#FF5C8D] text-white font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212]">
                  ADVISORY EVIDENCE ONLY
                </span>
              </div>
              <p className="font-sans text-sm text-[#1c1b1b]">{similarity.advisoryNote}</p>
            </div>
          </div>

          {/* Matched Projects List */}
          {matches.length === 0 ? (
            <EmptyState
              title="No Notable Similarity Matches"
              description="The similarity engine evaluated all comparable files and detected no significant overlap with other cohort submissions (all matches below the 15% notable threshold)."
            />
          ) : (
            <div className="flex flex-col gap-6">
              {matches.map((m) => (
                <div
                  key={m.matchedProjectId}
                  className="bg-white border-[2.5px] border-[#121212] p-6"
                  style={{ boxShadow: '4px 4px 0px #121212' }}
                >
                  {/* Cohort project match header */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b-2 border-[#121212] mb-4 gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-[10px] font-bold bg-[#F2ECE1] px-1.5 py-0.5 border border-[#121212] uppercase">
                          MATCHED SUBMISSION
                        </span>
                        <span className="font-mono text-[10px] text-[#4b4731]">
                          ID: {m.matchedProjectId}
                        </span>
                      </div>
                      <h3 className="font-display font-bold text-lg text-[#1c1b1b] mt-0.5">
                        {m.matchedProjectTitle || m.matchedProjectId}
                      </h3>
                    </div>

                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`font-mono text-[11px] font-bold px-2.5 py-1 border border-[#121212] uppercase ${m.similarityCategory === 'high'
                          ? 'bg-[#FF5C8D] text-white'
                          : m.similarityCategory === 'moderate'
                            ? 'bg-[#ffe600] text-[#1c1b1b]'
                            : m.similarityCategory === 'low'
                              ? 'bg-[#00E5BE] text-[#1c1b1b]'
                              : 'bg-[#F2ECE1] text-[#4b4731]'
                          }`}
                      >
                        {m.similarityCategory.toUpperCase()} SIGNAL
                      </span>
                      <span className="font-mono text-[12px] font-bold bg-[#ffe600] text-[#1c1b1b] px-3 py-1 border border-[#121212]">
                        {m.overallSimilarity}% Overall Similarity
                      </span>
                    </div>
                  </div>

                  {/* Component Breakdown Pills */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-5">
                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Token Match</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">
                        {m.tokenSimilarity !== null && m.tokenSimilarity !== undefined ? `${m.tokenSimilarity}%` : 'N/A'}
                      </span>
                    </div>

                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Structural (AST)</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">
                        {m.structuralSimilarity !== null && m.structuralSimilarity !== undefined
                          ? `${m.structuralSimilarity}%`
                          : 'Unsupported'}
                      </span>
                    </div>

                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Semantic Cosine</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">
                        {m.semanticSimilarity !== null && m.semanticSimilarity !== undefined
                          ? `${m.semanticSimilarity}%`
                          : 'Unavailable'}
                      </span>
                    </div>

                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Project Coverage</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">{m.sourceCoveragePct}%</span>
                    </div>

                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Cohort Coverage</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">{m.matchedCoveragePct}%</span>
                    </div>

                    <div className="p-2 bg-[#FAF6EE] border border-[#121212] text-center">
                      <span className="font-mono text-[9px] text-[#4b4731] block uppercase">Shared Statements</span>
                      <span className="font-mono text-xs font-bold text-[#1c1b1b]">{m.identicalStatements}</span>
                    </div>
                  </div>

                  {/* Strongest File-Pair Matches with Side-by-Side Diff */}
                  {m.strongestFileMatches.length > 0 && (
                    <div className="flex flex-col gap-4">
                      <h4 className="font-display font-bold text-sm text-[#1c1b1b] flex items-center gap-1.5">
                        <FileCode size={15} />
                        Strongest File Matches &amp; Snippet Evidence ({m.strongestFileMatches.length} pairs)
                      </h4>

                      {m.strongestFileMatches.map((fm, idx) => (
                        <div key={idx} className="border-2 border-[#121212] bg-[#FAF6EE]">
                          {/* File match subheader */}
                          <div className="bg-[#F2ECE1] border-b-2 border-[#121212] px-3 py-2 flex flex-wrap items-center justify-between gap-2">
                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[11px] font-bold text-[#1c1b1b]">
                                {fm.currentFile}
                              </span>
                              <span className="font-mono text-[10px] text-[#4b4731]">vs</span>
                              <span className="font-mono text-[11px] font-bold text-[#1c1b1b]">
                                {fm.matchedFile}
                              </span>
                            </div>

                            <div className="flex items-center gap-2">
                              <span className="font-mono text-[10px] font-bold bg-white px-2 py-0.5 border border-[#121212]">
                                {fm.similarityPercent}% Match
                              </span>
                              <span className="font-mono text-[10px] bg-[#FAF6EE] text-[#4b4731] px-1.5 py-0.5 border border-[#121212]">
                                Method: {fm.comparisonMethod}
                              </span>
                            </div>
                          </div>

                          {/* Side-by-side snippet preview */}
                          <div className="grid grid-cols-1 md:grid-cols-2">
                            <div className="border-b-2 md:border-b-0 md:border-r-2 border-[#121212] bg-white">
                              <div className="bg-[#FAF6EE] border-b border-[#121212] px-3 py-1 flex justify-between font-mono text-[10px]">
                                <span className="font-bold text-[#1c1b1b]">Current Project File</span>
                                <span className="text-[#4b4731]">Lines {fm.currentLines[0]}–{fm.currentLines[1]}</span>
                              </div>
                              <pre className="p-3 font-mono text-xs leading-5 overflow-x-auto text-[#1c1b1b] max-h-56">
                                {fm.currentSnippet || '// No preview available'}
                              </pre>
                            </div>

                            <div className="bg-[#FAF6EE]">
                              <div className="bg-[#ffe600] border-b border-[#121212] px-3 py-1 flex justify-between font-mono text-[10px]">
                                <span className="font-bold text-[#1c1b1b]">Matched Cohort File</span>
                                <span className="text-[#1c1b1b]">Lines {fm.matchedLines[0]}–{fm.matchedLines[1]}</span>
                              </div>
                              <pre className="p-3 font-mono text-xs leading-5 overflow-x-auto text-[#1c1b1b] max-h-56">
                                {fm.matchedSnippet || '// No preview available'}
                              </pre>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* ── Methodology & Capabilities Matrix ── */}
      <div
        className="bg-white border-[2.5px] border-[#121212] p-5"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div className="flex items-center gap-2 mb-3 pb-2 border-b-2 border-[#121212]">
          <SlidersHorizontal size={18} className="text-[#1c1b1b]" />
          <h3 className="font-display font-bold text-base text-[#1c1b1b]">
            Similarity Methodology, Capabilities &amp; Limitations
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
            <span className="font-display font-bold text-xs text-[#1c1b1b] block mb-1">
              Token Shingles ($k=4$)
            </span>
            <p className="font-sans text-xs text-[#4b4731]">
              Strips comments and normalizes formatting, then constructs token shingles and evaluates Jaccard set containment.
            </p>
          </div>

          <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
            <span className="font-display font-bold text-xs text-[#1c1b1b] block mb-1">
              Hierarchical AST Analysis
            </span>
            <p className="font-sans text-xs text-[#4b4731]">
              Preserves syntax-tree nesting, directed parent-child edges, and branch signatures using Python `ast` and Tree-sitter.
            </p>
          </div>

          <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
            <span className="font-display font-bold text-xs text-[#1c1b1b] block mb-1">
              Local Semantic Baseline
            </span>
            <p className="font-sans text-xs text-[#4b4731]">
              Optional local Sentence Transformer chunks without auto-downloading. Re-normalizes weights when unavailable.
            </p>
          </div>
        </div>

        {similarity?.limitations && similarity.limitations.length > 0 && (
          <div className="bg-[#FAF6EE] border border-[#121212] p-3">
            <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block mb-1">
              Active Comparison Constraints
            </span>
            <ul className="flex flex-col gap-1 font-sans text-xs text-[#4b4731]">
              {similarity.limitations.map((lim, idx) => (
                <li key={idx} className="flex items-start gap-1.5">
                  <span className="w-1.5 h-1.5 bg-[#4b4731] border border-[#121212] shrink-0 mt-1" />
                  {lim}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

function GitDevelopmentHistorySection({
  gitHistory,
  loading,
  analyzing,
  error,
  onAnalyze,
}: {
  gitHistory: GitHistoryResponse | null;
  loading: boolean;
  analyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
}) {
  const [showAllCommits, setShowAllCommits] = useState(false);

  const status = gitHistory?.status || 'not_started';
  const availability = gitHistory?.availability || 'unavailable';
  const hasAnalysis = gitHistory !== null && status !== 'not_started';
  const summary = gitHistory?.summary;
  const timeline = gitHistory?.timeline || [];
  const findings = gitHistory?.findings || [];
  const limitations = gitHistory?.limitations || [];

  const formatCommitDate = (iso?: string | null) => {
    if (!iso) return 'N/A';
    try {
      return new Date(iso).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });
    } catch {
      return iso;
    }
  };

  const getStatusBadge = () => {
    if (analyzing) {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-2 py-0.5 border border-[#121212] animate-pulse">
          ANALYZING...
        </span>
      );
    }
    if (!hasAnalysis) {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
          NOT STARTED
        </span>
      );
    }
    if (availability === 'available' && status === 'completed') {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#00E5BE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">
          GIT HISTORY AVAILABLE
        </span>
      );
    }
    if (availability === 'empty' || status === 'empty_repository') {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">
          EMPTY REPOSITORY (0 COMMITS)
        </span>
      );
    }
    if (availability === 'corrupt' || status === 'corrupt_git_metadata') {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#FF5C8D] text-white px-2 py-0.5 border border-[#121212]">
          CORRUPT GIT METADATA
        </span>
      );
    }
    if (availability === 'unavailable' || status === 'no_git_repository') {
      return (
        <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
          NO GIT REPOSITORY
        </span>
      );
    }
    return (
      <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">
        {status.toUpperCase()}
      </span>
    );
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev.toLowerCase();
    if (s === 'high') return <span className="font-mono text-[10px] font-bold bg-[#FF5C8D] text-white px-1.5 py-0.5 border border-[#121212]">HIGH</span>;
    if (s === 'medium') return <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">MEDIUM</span>;
    if (s === 'low') return <span className="font-mono text-[10px] font-bold bg-[#D8B4FE] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">LOW</span>;
    return <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">ADVISORY</span>;
  };

  // Weekday activity data
  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
  const weekdayCounts = weekdays.map(day => ({
    day,
    shortDay: day.slice(0, 3).toUpperCase(),
    count: summary?.activityByWeekday?.[day] || 0,
  }));
  const maxWeekdayCount = Math.max(...weekdayCounts.map(w => w.count), 1);

  // Daily activity sorted entries
  const dailyEntries = summary?.activityByDay ? Object.entries(summary.activityByDay).sort(([a], [b]) => a.localeCompare(b)) : [];

  const displayedCommits = showAllCommits ? timeline : timeline.slice(0, 10);

  return (
    <div className="bg-white border-[2.5px] border-[#121212] p-6 space-y-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
      {/* ── Section Header & Actions ── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b-2 border-[#121212] gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-mono text-[10px] font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212] uppercase">
              Phase 6 Engine
            </span>
            <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
              {gitHistory?.analysisVersion || 'v1.0-git-analysis'}
            </span>
            {getStatusBadge()}
            {gitHistory?.isShallow && (
              <span className="font-mono text-[10px] font-bold bg-[#D8B4FE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">
                SHALLOW REPO
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <GitBranch size={20} className="text-[#1c1b1b]" />
            <h3 className="font-display font-bold text-xl text-[#1c1b1b]">
              Git Development History &amp; Commit Velocity
            </h3>
          </div>
          <p className="font-sans text-xs text-[#4b4731] mt-0.5">
            Analyzes commit cadence, developer intervals, code churn concentration, and observable development signals.
          </p>
        </div>

        <button
          className="btn-primary flex items-center justify-center gap-2 cursor-pointer shrink-0 disabled:opacity-50"
          onClick={onAnalyze}
          disabled={analyzing}
        >
          <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
          {analyzing
            ? 'Analyzing Git History...'
            : hasAnalysis
              ? 'Re-analyze Development History'
              : 'Run Development History Analysis'}
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={onAnalyze} />}

      {loading ? (
        <LoadingSpinner message="Loading Git development history..." />
      ) : !hasAnalysis ? (
        <div className="bg-[#FAF6EE] border-2 border-[#121212] p-8 text-center flex flex-col items-center justify-center gap-2">
          <Clock size={36} className="text-[#4b4731]" />
          <h4 className="font-display font-bold text-base text-[#1c1b1b]">
            Development History Analysis Not Yet Run
          </h4>
          <p className="font-sans text-xs text-[#4b4731] max-w-md">
            Click &ldquo;Run Development History Analysis&rdquo; to inspect the project archive for Git metadata, extract commit timeline statistics, and generate evidence-based development cadence signals.
          </p>
        </div>
      ) : availability === 'unavailable' || status === 'no_git_repository' ? (
        <div className="bg-[#FAF6EE] border-2 border-[#121212] p-6">
          <div className="flex items-start gap-3">
            <Info size={24} className="text-[#4b4731] shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                No Git History Available in Submission
              </h4>
              <p className="font-sans text-sm text-[#4b4731]">
                No Git repository (<code className="bg-white px-1 py-0.5 border border-[#121212] font-mono text-xs">.git</code>) was found in this project archive. Development timeline and commit velocity analysis cannot be performed.
              </p>
              <div className="bg-white border border-[#121212] p-3 text-xs text-[#4b4731] font-sans">
                <strong>Advisory Note:</strong> A submission without Git history is not necessarily an invalid project. Students may have packaged source files directly without including Git metadata. In accordance with ProjectLens guidelines, no synthetic commit data or file timestamps are substituted.
              </div>
              {limitations.length > 0 && (
                <ul className="list-disc list-inside font-mono text-[11px] text-[#4b4731] pt-1">
                  {limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : availability === 'empty' || status === 'empty_repository' ? (
        <div className="bg-[#FAF6EE] border-2 border-[#121212] p-6">
          <div className="flex items-start gap-3">
            <AlertTriangle size={24} className="text-[#ffe600] shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                Empty Git Repository (0 Commits)
              </h4>
              <p className="font-sans text-sm text-[#4b4731]">
                A Git repository structure exists in the submission archive, but contains no recorded commits (unborn branch / empty repository).
              </p>
              {limitations.length > 0 && (
                <ul className="list-disc list-inside font-mono text-[11px] text-[#4b4731] pt-1">
                  {limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : availability === 'corrupt' || status === 'corrupt_git_metadata' ? (
        <div className="bg-[#FAF6EE] border-2 border-[#121212] p-6">
          <div className="flex items-start gap-3">
            <ShieldAlert size={24} className="text-[#FF5C8D] shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                Corrupt or Unreadable Git Metadata
              </h4>
              <p className="font-sans text-sm text-[#4b4731]">
                Git metadata was detected, but repository objects or references could not be parsed safely by the engine.
              </p>
              {limitations.length > 0 && (
                <ul className="list-disc list-inside font-mono text-[11px] text-[#4b4731] pt-1">
                  {limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      ) : summary ? (
        <>
          {/* ── Summary Metrics 6-Card Grid ── */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">Total Commits</span>
              <div className="mt-1">
                <span className="font-display font-bold text-2xl text-[#1c1b1b]">{summary.totalCommits}</span>
                <span className="font-mono text-[10px] text-[#4b4731] block">{summary.durationDays} day(s) span</span>
              </div>
            </div>

            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">First Commit</span>
              <div className="mt-1">
                <span className="font-mono font-bold text-xs text-[#1c1b1b] block">
                  {formatCommitDate(summary.firstCommitAt)}
                </span>
              </div>
            </div>

            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">Last Commit</span>
              <div className="mt-1">
                <span className="font-mono font-bold text-xs text-[#1c1b1b] block">
                  {formatCommitDate(summary.lastCommitAt)}
                </span>
              </div>
            </div>

            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">Code Churn</span>
              <div className="mt-1">
                <div className="font-mono text-xs font-bold text-[#006b58]">+{summary.totalAdditions.toLocaleString()}</div>
                <div className="font-mono text-xs font-bold text-[#FF5C8D]">-{summary.totalDeletions.toLocaleString()}</div>
                <span className="font-mono text-[10px] text-[#4b4731] block">{summary.totalFilesChanged} files</span>
              </div>
            </div>

            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">Commit Cadence</span>
              <div className="mt-1">
                <span className="font-display font-bold text-lg text-[#1c1b1b]">
                  {summary.avgTimeBetweenCommitsHours !== null && summary.avgTimeBetweenCommitsHours !== undefined ? `${summary.avgTimeBetweenCommitsHours}h` : 'N/A'}
                </span>
                <span className="font-mono text-[10px] text-[#4b4731] block">
                  {summary.medianTimeBetweenCommitsHours !== null && summary.medianTimeBetweenCommitsHours !== undefined ? `Median ${summary.medianTimeBetweenCommitsHours}h` : 'interval'}
                </span>
              </div>
            </div>

            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-3 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase">Concentration</span>
              <div className="mt-1">
                <span className="font-display font-bold text-lg text-[#1c1b1b]">
                  {summary.largestCommitSharePercent !== null && summary.largestCommitSharePercent !== undefined ? `${summary.largestCommitSharePercent}%` : 'N/A'}
                </span>
                <span className="font-mono text-[10px] text-[#4b4731] block">
                  {summary.top3CommitSharePercent !== null && summary.top3CommitSharePercent !== undefined ? `Top-3: ${summary.top3CommitSharePercent}%` : 'largest commit'}
                </span>
              </div>
            </div>
          </div>

          {/* ── Activity Visualization & Contributor Breakdown Grid ── */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Weekday Distribution Chart */}
            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-[#121212]/20 mb-3">
                  <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                    Commit Activity by Day of Week
                  </h4>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {summary.totalCommits} total commit(s)
                  </span>
                </div>
                <p className="font-sans text-xs text-[#4b4731] mb-3">
                  Distribution of commits across weekdays based on recorded commit timestamps.
                </p>

                <div className="space-y-2">
                  {weekdayCounts.map(w => {
                    const pct = Math.round((w.count / maxWeekdayCount) * 100);
                    return (
                      <div key={w.day} className="flex items-center gap-2">
                        <span className="font-mono text-[11px] font-bold w-9 text-[#1c1b1b]">{w.shortDay}</span>
                        <div className="flex-1 bg-white border border-[#121212] h-5 relative overflow-hidden">
                          {w.count > 0 && (
                            <div
                              className="h-full bg-[#ffe600] border-r border-[#121212] transition-all"
                              style={{ width: `${pct}%` }}
                            />
                          )}
                        </div>
                        <span className="font-mono text-[11px] font-bold w-6 text-right text-[#1c1b1b]">
                          {w.count}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {dailyEntries.length > 0 && (
                <div className="mt-4 pt-3 border-t border-[#121212]/20">
                  <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-1">
                    Recorded Active Dates ({dailyEntries.length} day(s))
                  </span>
                  <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                    {dailyEntries.map(([d, cnt]) => (
                      <span key={d} className="font-mono text-[10px] bg-white px-2 py-0.5 border border-[#121212] text-[#1c1b1b]">
                        {d}: <strong>{cnt}</strong>
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Contributors & Size Distribution */}
            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <div className="flex items-center justify-between pb-2 border-b border-[#121212]/20 mb-3">
                  <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                    Contributors &amp; Commit Size Distribution
                  </h4>
                  <span className="font-mono text-[10px] text-[#4b4731]">
                    {summary.distinctContributorsCount} author(s)
                  </span>
                </div>

                <div className="mb-4">
                  <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-2">
                    Distinct Commit Authors ({summary.contributors.length})
                  </span>
                  {summary.contributors.length > 0 ? (
                    <div className="space-y-2">
                      {summary.contributors.map((c, ci) => (
                        <div key={ci} className="bg-white border border-[#121212] p-2 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-display font-bold text-[#1c1b1b]">{c.name}</span>
                            {c.email && <span className="font-mono text-[10px] text-[#4b4731] block">{c.email}</span>}
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-bold bg-[#FAF6EE] px-1.5 py-0.5 border border-[#121212]">
                              {c.commitCount} commit(s) ({c.percentage}%)
                            </span>
                            <span className="font-mono text-[10px] text-[#006b58]">+{c.additions}</span>
                            <span className="font-mono text-[10px] text-[#FF5C8D]">-{c.deletions}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="font-mono text-xs text-[#4b4731]">Author metadata unavailable.</span>
                  )}
                </div>

                <div>
                  <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-2">
                    Commit Churn Size Breakdown
                  </span>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(summary.sizeDistribution || {}).map(([category, count]) => (
                      <div key={category} className="bg-white border border-[#121212] p-2 text-center">
                        <span className="font-mono text-[10px] text-[#4b4731] block truncate">{category}</span>
                        <span className="font-display font-bold text-lg text-[#1c1b1b]">{count}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ── Evidence-Based Development Signals ── */}
          <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4" style={{ boxShadow: '2px 2px 0px #121212' }}>
            <div className="flex items-center justify-between pb-2 border-b border-[#121212]/20 mb-3">
              <div>
                <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                  Evidence-Based Development Signals ({findings.length})
                </h4>
                <p className="font-sans text-xs text-[#4b4731]">
                  Observable commit cadence anomalies for faculty review. Signals are advisory indicators, not plagiarism verdicts.
                </p>
              </div>
            </div>

            {findings.length > 0 ? (
              <div className="space-y-3">
                {findings.map((f, fi) => (
                  <div key={fi} className="bg-white border-2 border-[#121212] p-3 space-y-2">
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <div className="flex items-center gap-2">
                        {getSeverityBadge(f.severity)}
                        <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] px-1.5 py-0.5 border border-[#121212]">
                          {f.category.replace(/_/g, ' ').toUpperCase()}
                        </span>
                        <span className="font-mono text-[10px] text-[#4b4731]">
                          {f.signalId}
                        </span>
                      </div>
                    </div>

                    <div>
                      <h5 className="font-display font-bold text-sm text-[#1c1b1b]">{f.title}</h5>
                      <p className="font-sans text-xs text-[#4b4731] mt-0.5">{f.explanation}</p>
                    </div>

                    {f.evidence && Object.keys(f.evidence).length > 0 && (
                      <div className="bg-[#FAF6EE] border border-[#121212] p-2">
                        <span className="font-mono text-[10px] font-bold uppercase text-[#1c1b1b] block mb-1">
                          Supporting Evidence:
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(f.evidence).map(([ek, ev]) => (
                            <span key={ek} className="font-mono text-[10px] bg-white px-2 py-0.5 border border-[#121212]">
                              {ek}: <strong>{String(ev)}</strong>
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {f.facultyGuidance && (
                      <div className="bg-[#EBF7F5] border border-[#00A389] p-2 text-xs text-[#004d40] flex items-start gap-1.5">
                        <AlertTriangle size={14} className="text-[#00A389] shrink-0 mt-0.5" />
                        <div>
                          <strong>Faculty Advisory:</strong> {f.facultyGuidance}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-white border border-[#121212] p-4 text-center">
                <CheckCircle size={24} className="mx-auto text-[#006b58] mb-1" />
                <span className="font-display font-bold text-sm text-[#1c1b1b] block">
                  No Anomalous Development Signals Detected
                </span>
                <span className="font-sans text-xs text-[#4b4731]">
                  All inspected commit intervals and churn distribution metrics conform to expected advisory thresholds.
                </span>
              </div>
            )}
          </div>

          {/* ── Chronological Commit Timeline ── */}
          <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4" style={{ boxShadow: '2px 2px 0px #121212' }}>
            <div className="flex items-center justify-between pb-2 border-b border-[#121212]/20 mb-3">
              <div>
                <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                  Commit History Timeline ({timeline.length})
                </h4>
                <p className="font-sans text-xs text-[#4b4731]">
                  Chronological record of commits inspected within the safely extracted project repository.
                </p>
              </div>
              {timeline.length > 10 && (
                <button
                  className="font-mono text-[11px] font-bold bg-white px-3 py-1 border border-[#121212] cursor-pointer hover:bg-[#FAF6EE]"
                  onClick={() => setShowAllCommits(!showAllCommits)}
                >
                  {showAllCommits ? 'Show First 10' : `Show All ${timeline.length} Commits`}
                </button>
              )}
            </div>

            {timeline.length > 0 ? (
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-[#121212] text-xs font-sans bg-white">
                  <thead>
                    <tr className="bg-[#FAF6EE] border-b border-[#121212] font-mono text-[10px] uppercase text-left">
                      <th className="p-2 border-r border-[#121212]">Hash</th>
                      <th className="p-2 border-r border-[#121212]">Date &amp; Time</th>
                      <th className="p-2 border-r border-[#121212]">Author</th>
                      <th className="p-2 border-r border-[#121212]">Commit Message</th>
                      <th className="p-2 border-r border-[#121212] text-center">Files</th>
                      <th className="p-2 text-right">Churn</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayedCommits.map((c, ci) => (
                      <tr key={c.commitHash || ci} className="border-b border-[#121212]/20 hover:bg-[#FAF6EE]/50">
                        <td className="p-2 border-r border-[#121212]/20 font-mono font-bold text-[#1c1b1b]">
                          <span className="bg-[#FAF6EE] px-1.5 py-0.5 border border-[#121212] text-[11px]">
                            {c.shortHash}
                          </span>
                          {c.isMerge && (
                            <span className="ml-1 font-mono text-[9px] font-bold bg-[#D8B4FE] text-[#1c1b1b] px-1 py-0.2 border border-[#121212]">
                              MERGE
                            </span>
                          )}
                        </td>
                        <td className="p-2 border-r border-[#121212]/20 font-mono text-[11px] text-[#4b4731] whitespace-nowrap">
                          {formatCommitDate(c.committedAt)}
                        </td>
                        <td className="p-2 border-r border-[#121212]/20 text-[#1c1b1b] font-medium whitespace-nowrap">
                          {c.authorName}
                        </td>
                        <td className="p-2 border-r border-[#121212]/20 text-[#1c1b1b]">
                          <div className="font-semibold text-xs">{c.subject || '(no message)'}</div>
                          {c.changedFiles && c.changedFiles.length > 0 && (
                            <div className="flex items-center gap-1 flex-wrap mt-1">
                              {c.changedFiles.slice(0, 3).map((f, fi) => (
                                <span key={fi} className="font-mono text-[9px] bg-[#FAF6EE] px-1 border border-[#121212]/40 text-[#4b4731]">
                                  {f}
                                </span>
                              ))}
                              {c.changedFiles.length > 3 && (
                                <span className="font-mono text-[9px] text-[#4b4731]">
                                  +{c.changedFiles.length - 3} more
                                </span>
                              )}
                            </div>
                          )}
                        </td>
                        <td className="p-2 border-r border-[#121212]/20 text-center font-mono text-xs">
                          {c.filesChangedCount}
                        </td>
                        <td className="p-2 text-right font-mono text-xs whitespace-nowrap">
                          <span className="text-[#006b58] font-bold">+{c.linesAdded}</span>
                          <span className="text-[#4b4731] mx-0.5">/</span>
                          <span className="text-[#FF5C8D] font-bold">-{c.linesDeleted}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="bg-white border border-[#121212] p-4 text-center">
                <p className="font-sans text-xs text-[#4b4731]">No commit records available to display.</p>
              </div>
            )}
          </div>

          {/* ── Limitations & Faculty Advisory Notice ── */}
          <div className="bg-white border border-[#121212] p-4 space-y-2">
            <div className="flex items-center gap-2">
              <ShieldAlert size={16} className="text-[#1c1b1b]" />
              <span className="font-display font-bold text-xs uppercase tracking-wide">
                Faculty Advisory &amp; Methodological Limitations
              </span>
            </div>
            <p className="font-sans text-xs text-[#4b4731]">
              {gitHistory.advisoryNote}
            </p>
            {limitations.length > 0 && (
              <div className="pt-2 border-t border-[#121212]/10">
                <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-1">
                  Analysis Boundary Conditions:
                </span>
                <ul className="list-disc list-inside font-mono text-[11px] text-[#4b4731] space-y-0.5">
                  {limitations.map((lim, i) => (
                    <li key={i}>{lim}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </>
      ) : null}
    </div>
  );
}

function DocumentationTab({
  documentation,
  loading,
  analyzing,
  error,
  onAnalyze,
  gitHistory,
  gitLoading,
  gitAnalyzing,
  gitError,
  onAnalyzeGit,
}: {
  documentation: DocumentationResponse | null;
  loading: boolean;
  analyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
  gitHistory: GitHistoryResponse | null;
  gitLoading: boolean;
  gitAnalyzing: boolean;
  gitError: string | null;
  onAnalyzeGit: () => void;
}) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [showFactorModal, setShowFactorModal] = useState(false);

  if (loading) {
    return <LoadingSpinner message="Loading documentation analysis..." />;
  }

  const status = documentation?.status || 'not_started';
  const hasAnalysis = documentation && status !== 'not_started';
  const findings = documentation?.findings || [];
  const metrics = documentation?.metricsSummary;
  const sections = documentation?.sectionCoverage || [];
  const documents = documentation?.documents || [];
  const scoreExpl = documentation?.scoreExplanation;
  const factors = scoreExpl?.factors || [];

  const filteredFindings = selectedCategory === 'all'
    ? findings
    : findings.filter(f => f.category === selectedCategory);

  const getStatusBadge = (s: string) => {
    switch (s) {
      case 'completed':
        return <span className="font-mono text-[10px] font-bold bg-[#00E5BE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">COMPLETED</span>;
      case 'insufficient_evidence':
        return <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">INSUFFICIENT EVIDENCE</span>;
      default:
        return <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">NOT STARTED</span>;
    }
  };

  const getVerificationStatusPill = (vStatus: string) => {
    switch (vStatus) {
      case 'verified':
        return <span className="font-mono text-[10px] font-bold bg-[#00E5BE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">VERIFIED IN CODEBASE</span>;
      case 'potential_inconsistency':
        return <span className="font-mono text-[10px] font-bold bg-[#FF5C8D] text-white px-2 py-0.5 border border-[#121212]">POTENTIAL INCONSISTENCY</span>;
      case 'claim_not_verified':
        return <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">CLAIM UNVERIFIED</span>;
      case 'insufficient_evidence':
        return <span className="font-mono text-[10px] font-bold bg-[#D8B4FE] text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">INSUFFICIENT EVIDENCE</span>;
      default:
        return <span className="font-mono text-[10px] font-bold bg-white text-[#4b4731] px-2 py-0.5 border border-[#121212]">{vStatus.toUpperCase()}</span>;
    }
  };

  const getSeverityBadge = (sev: string) => {
    const s = sev.toLowerCase();
    if (s === 'high') return <span className="font-mono text-[10px] font-bold bg-[#FF5C8D] text-white px-1.5 py-0.5 border border-[#121212]">HIGH</span>;
    if (s === 'medium') return <span className="font-mono text-[10px] font-bold bg-[#ffe600] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">MEDIUM</span>;
    if (s === 'low') return <span className="font-mono text-[10px] font-bold bg-[#D8B4FE] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">LOW</span>;
    return <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#1c1b1b] px-1.5 py-0.5 border border-[#121212]">ADVISORY</span>;
  };

  return (
    <div className="flex flex-col gap-6">
      {/* ── Top Header & Actions ── */}
      <div
        className="bg-white border-[2.5px] border-[#121212] p-5 flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div>
          <div className="flex items-center gap-2 mb-1 flex-wrap">
            <span className="font-mono text-[10px] font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212] uppercase">
              Phase 5 Engine
            </span>
            <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
              {documentation?.scoringVersion || 'v1.0-deterministic-rubric'}
            </span>
            {getStatusBadge(status)}
          </div>
          <h2 className="font-display font-bold text-xl text-[#1c1b1b]">
            Documentation Analysis & Code Consistency
          </h2>
          <p className="font-sans text-sm text-[#4b4731]">
            Deterministic report extraction, section recognition, operational readiness, and codebase consistency verification.
          </p>
        </div>

        <button
          className="btn-primary flex items-center justify-center gap-2 cursor-pointer shrink-0 disabled:opacity-50"
          onClick={onAnalyze}
          disabled={analyzing}
        >
          <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
          {analyzing
            ? 'Analyzing Documentation...'
            : hasAnalysis
              ? 'Re-run Documentation Analysis'
              : 'Run Documentation Analysis'}
        </button>
      </div>

      {error && <ErrorBanner message={error} onRetry={onAnalyze} />}

      {!hasAnalysis ? (
        <div
          className="bg-white border-[2.5px] border-[#121212] p-10 text-center flex flex-col items-center justify-center gap-3"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <BookOpen size={48} className="text-[#1c1b1b]" />
          <h3 className="font-display font-bold text-lg text-[#1c1b1b]">
            No Documentation Analysis Executed Yet
          </h3>
          <p className="font-sans text-sm text-[#4b4731] max-w-md">
            Click below to extract text from README, PDF project reports, or Word documents, analyze standard section completeness, and verify technology claims against the source code.
          </p>
          <button
            className="btn-primary flex items-center gap-2 mt-2 cursor-pointer"
            onClick={onAnalyze}
            disabled={analyzing}
          >
            <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing Documentation...' : 'Run Documentation Analysis'}
          </button>
        </div>
      ) : (
        <>
          {/* ── 4-Card Top Metrics Row ── */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {/* Card 1: Preliminary Doc Quality Score */}
            <div className="bg-white border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">
                  Documentation Quality Score
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  {documentation.preliminaryScore !== null && documentation.preliminaryScore !== undefined ? (
                    <>
                      <span className="font-display font-bold text-3xl text-[#1c1b1b]">
                        {documentation.preliminaryScore}
                      </span>
                      <span className="font-mono text-sm text-[#4b4731]">/ 100</span>
                    </>
                  ) : (
                    <span className="font-display font-bold text-xl text-[#FF5C8D]">
                      Insufficient Evidence
                    </span>
                  )}
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-[#121212]/20 flex items-center justify-between">
                <span className="font-mono text-[10px] text-[#4b4731]">
                  {documentation.preliminaryScore !== null ? 'Advisory preliminary score' : 'Word count < 50; score withheld'}
                </span>
                {factors.length > 0 && (
                  <button
                    onClick={() => setShowFactorModal(!showFactorModal)}
                    className="font-mono text-[10px] underline font-bold text-[#1c1b1b] cursor-pointer"
                  >
                    {showFactorModal ? 'Hide breakdown' : 'View rubric'}
                  </button>
                )}
              </div>
            </div>

            {/* Card 2: Documents & Words */}
            <div className="bg-white border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">
                  Documentation Volume
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="font-display font-bold text-3xl text-[#1c1b1b]">
                    {metrics?.totalWords?.toLocaleString() ?? 0}
                  </span>
                  <span className="font-mono text-sm text-[#4b4731]">words</span>
                </div>
              </div>
              <span className="font-mono text-[10px] text-[#4b4731] mt-2 pt-2 border-t border-[#121212]/20 block">
                Across {metrics?.totalDocuments ?? 0} discovered document(s)
              </span>
            </div>

            {/* Card 3: Recognized Sections */}
            <div className="bg-white border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">
                  Required Section Coverage
                </span>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="font-display font-bold text-3xl text-[#1c1b1b]">
                    {metrics?.requiredSectionsPresent ?? 0}
                  </span>
                  <span className="font-mono text-sm text-[#4b4731]">
                    / {metrics?.requiredSectionsTotal ?? 5} Core
                  </span>
                </div>
              </div>
              <span className="font-mono text-[10px] text-[#4b4731] mt-2 pt-2 border-t border-[#121212]/20 block">
                {metrics?.recognizedSectionsCount ?? 0} total standard sections recognized
              </span>
            </div>

            {/* Card 4: Operational Readiness */}
            <div className="bg-white border-2 border-[#121212] p-4 flex flex-col justify-between" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div>
                <span className="font-mono text-[10px] font-bold text-[#4b4731] uppercase block">
                  Operational Readiness
                </span>
                <div className="mt-1 flex items-center gap-2">
                  <span className={`font-mono text-[11px] font-bold px-2 py-0.5 border border-[#121212] ${metrics?.hasSetupInstructions ? 'bg-[#00E5BE] text-[#1c1b1b]' : 'bg-[#FF5C8D] text-white'
                    }`}>
                    {metrics?.hasSetupInstructions ? 'SETUP GUIDE DETECTED' : 'SETUP GUIDE MISSING'}
                  </span>
                </div>
              </div>
              <span className="font-mono text-[10px] text-[#4b4731] mt-2 pt-2 border-t border-[#121212]/20 block">
                README: {metrics?.hasReadme ? 'Present' : 'Absent'} | Tests: {metrics?.hasTestingSection ? 'Documented' : 'Undocumented'}
              </span>
            </div>
          </div>

          {/* ── Scoring Factor Breakdown (Toggleable) ── */}
          {showFactorModal && factors.length > 0 && (
            <div
              className="bg-[#FAF6EE] border-2 border-[#121212] p-5"
              style={{ boxShadow: '3px 3px 0px #121212' }}
            >
              <div className="flex items-center justify-between pb-2 border-b-2 border-[#121212] mb-3">
                <h3 className="font-display font-bold text-base text-[#1c1b1b]">
                  Deterministic Scoring Rubric Breakdown ({documentation.scoringVersion})
                </h3>
                <span className="font-mono text-[11px] font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212]">
                  {documentation.preliminaryScore} / 100 PTS
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {factors.map((f, i) => (
                  <div key={i} className="bg-white border border-[#121212] p-3 flex flex-col justify-between">
                    <div className="flex items-baseline justify-between mb-1">
                      <span className="font-display font-bold text-sm text-[#1c1b1b]">{f.name}</span>
                      <span className="font-mono text-xs font-bold text-[#006b58]">
                        {f.pointsAwarded} / {f.maxPoints} pts
                      </span>
                    </div>
                    <p className="font-sans text-xs text-[#4b4731]">{f.notes}</p>
                  </div>
                ))}
              </div>
              {scoreExpl?.summary && (
                <p className="font-mono text-[11px] text-[#4b4731] mt-3 pt-2 border-t border-[#121212]/20">
                  {scoreExpl.summary}
                </p>
              )}
            </div>
          )}

          {/* ── Document Inventory ── */}
          <div
            className="bg-white border-[2.5px] border-[#121212] p-6"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex items-center justify-between pb-3 border-b-2 border-[#121212] mb-4">
              <div>
                <h3 className="font-display font-bold text-lg text-[#1c1b1b]">
                  Discovered Documentation Inventory ({documents.length})
                </h3>
                <p className="font-sans text-xs text-[#4b4731]">
                  Safely extracted text and structural metadata without executing submitted code.
                </p>
              </div>
            </div>

            {documents.length > 0 ? (
              <div className="flex flex-col gap-3">
                {documents.map((doc, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col md:flex-row md:items-center justify-between gap-3"
                    style={{ boxShadow: '2px 2px 0px #121212' }}
                  >
                    <div className="flex flex-col gap-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-mono text-[10px] font-bold bg-[#1c1b1b] text-white px-2 py-0.5 border border-[#121212] uppercase">
                          .{doc.fileFormat}
                        </span>
                        <span className="font-mono font-bold text-sm text-[#1c1b1b]">
                          {doc.relativePath}
                        </span>
                        <span className={`font-mono text-[10px] font-bold px-1.5 py-0.5 border border-[#121212] ${doc.extractionStatus === 'success' ? 'bg-[#00E5BE] text-[#1c1b1b]' :
                          doc.extractionStatus === 'partial' ? 'bg-[#ffe600] text-[#1c1b1b]' :
                            doc.extractionStatus === 'empty_scanned_image' ? 'bg-[#D8B4FE] text-[#1c1b1b]' :
                              'bg-[#FF5C8D] text-white'
                          }`}>
                          {doc.extractionStatus.replace(/_/g, ' ').toUpperCase()}
                        </span>
                      </div>
                      {doc.warningMessage && (
                        <p className="font-sans text-xs text-[#FF5C8D] font-bold">
                          Warning: {doc.warningMessage}
                        </p>
                      )}
                      {doc.sectionsFound && doc.sectionsFound.length > 0 && (
                        <div className="flex items-center gap-1.5 flex-wrap mt-1">
                          <span className="font-mono text-[10px] text-[#4b4731]">Headings:</span>
                          {doc.sectionsFound.slice(0, 5).map((h, hi) => (
                            <span key={hi} className="font-mono text-[9px] bg-white px-1.5 py-0.5 border border-[#121212] text-[#1c1b1b]">
                              {h}
                            </span>
                          ))}
                          {doc.sectionsFound.length > 5 && (
                            <span className="font-mono text-[9px] text-[#4b4731]">
                              +{doc.sectionsFound.length - 5} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-4 shrink-0 font-mono text-xs text-[#4b4731]">
                      {doc.fileFormat === 'pdf' && (
                        <div>
                          <strong className="text-[#1c1b1b]">{doc.pageCount}</strong> page(s)
                        </div>
                      )}
                      <div>
                        <strong className="text-[#1c1b1b]">{doc.extractedWordCount.toLocaleString()}</strong> words
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="font-sans text-sm text-[#4b4731]">No documentation files found in project archive.</p>
            )}
          </div>

          {/* ── Standard Section Coverage Matrix ── */}
          <div
            className="bg-white border-[2.5px] border-[#121212] p-6"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex items-center justify-between pb-3 border-b-2 border-[#121212] mb-4">
              <div>
                <h3 className="font-display font-bold text-lg text-[#1c1b1b]">
                  Standard Report & Documentation Sections ({sections.filter(s => s.isPresent).length} / {sections.length})
                </h3>
                <p className="font-sans text-xs text-[#4b4731]">
                  Identifies structural report components using heading-aware parsing and synonyms.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {sections.map((sec) => (
                <div
                  key={sec.sectionKey}
                  className={`p-3 border-2 border-[#121212] flex flex-col justify-between ${sec.isPresent ? 'bg-[#FAF6EE]' : 'bg-[#f4efe6]/50 opacity-75'
                    }`}
                  style={{ boxShadow: '2px 2px 0px #121212' }}
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={`font-mono text-[9px] font-bold px-1.5 py-0.2 border border-[#121212] ${sec.isRequired ? 'bg-[#ffe600] text-[#1c1b1b]' : 'bg-white text-[#4b4731]'
                        }`}>
                        {sec.isRequired ? 'REQUIRED' : 'OPTIONAL'}
                      </span>
                      <span className={`font-mono text-[9px] font-bold px-1.5 py-0.2 border border-[#121212] ${sec.isPresent ? 'bg-[#00E5BE] text-[#1c1b1b]' : 'bg-[#F2ECE1] text-[#4b4731]'
                        }`}>
                        {sec.isPresent ? 'PRESENT' : 'MISSING'}
                      </span>
                    </div>
                    <h4 className="font-display font-bold text-xs text-[#1c1b1b]">
                      {sec.displayName}
                    </h4>
                  </div>

                  <div className="mt-2 pt-2 border-t border-[#121212]/20 font-mono text-[10px] text-[#4b4731]">
                    {sec.isPresent && sec.foundInFiles.length > 0 ? (
                      <span className="truncate block" title={sec.foundInFiles.join(', ')}>
                        In: {sec.foundInFiles.join(', ')}
                      </span>
                    ) : (
                      <span className="italic text-[#9c9383]">Not detected in documents</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Code–Documentation Consistency Findings ── */}
          <div
            className="bg-white border-[2.5px] border-[#121212] p-6"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between pb-3 border-b-2 border-[#121212] mb-4 gap-3">
              <div>
                <h3 className="font-display font-bold text-lg text-[#1c1b1b]">
                  Code–Documentation Consistency Findings ({findings.length})
                </h3>
                <p className="font-sans text-xs text-[#4b4731]">
                  Evidence-based verification cross-checking documented statements against actual manifests and code.
                </p>
              </div>

              {/* Category Filter Pills */}
              <div className="flex items-center gap-1.5 flex-wrap">
                {[
                  { id: 'all', label: 'All', count: findings.length },
                  { id: 'technology_consistency', label: 'Technology', count: findings.filter(f => f.category === 'technology_consistency').length },
                  { id: 'implementation_claim', label: 'Claims', count: findings.filter(f => f.category === 'implementation_claim').length },
                  { id: 'numerical_claim', label: 'Numerical', count: findings.filter(f => f.category === 'numerical_claim').length },
                  { id: 'file_reference', label: 'File Refs', count: findings.filter(f => f.category === 'file_reference').length },
                  { id: 'documentation_quality', label: 'Quality', count: findings.filter(f => f.category === 'documentation_quality').length },
                ].map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`font-mono text-[10px] font-bold px-2 py-1 border border-[#121212] cursor-pointer ${selectedCategory === cat.id ? 'bg-[#1c1b1b] text-white' : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-white'
                      }`}
                  >
                    {cat.label} ({cat.count})
                  </button>
                ))}
              </div>
            </div>

            {filteredFindings.length > 0 ? (
              <div className="flex flex-col gap-4">
                {filteredFindings.map((finding, idx) => (
                  <div
                    key={idx}
                    className="p-4 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col gap-2.5"
                    style={{ boxShadow: '2px 2px 0px #121212' }}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2 flex-wrap">
                        {getVerificationStatusPill(finding.verificationStatus)}
                        {getSeverityBadge(finding.severity)}
                        <span className="font-mono text-[11px] bg-white px-2 py-0.5 border border-[#121212] font-bold">
                          {finding.ruleId}
                        </span>
                        {finding.docPath && (
                          <span className="font-mono text-[11px] text-[#4b4731]">
                            {finding.docPath}
                            {finding.locationRef ? ` (${finding.locationRef})` : ''}
                          </span>
                        )}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                        {finding.title}
                      </h4>
                      <p className="font-sans text-xs text-[#4b4731] mt-0.5">
                        {finding.explanation}
                      </p>
                    </div>

                    {/* Evidence Comparison Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                      {finding.documentedClaim && (
                        <div className="bg-white border border-[#121212] p-2.5 font-mono text-[11px]">
                          <span className="font-bold text-[#1c1b1b] block mb-1 uppercase text-[10px]">Documented Claim / Excerpt:</span>
                          <span className="text-[#4b4731]">{finding.documentedClaim}</span>
                        </div>
                      )}

                      <div className="bg-white border border-[#121212] p-2.5 font-mono text-[11px]">
                        <span className="font-bold text-[#1c1b1b] block mb-1 uppercase text-[10px]">Codebase / Manifest Evidence:</span>
                        {finding.codeEvidence ? (
                          <span className="text-[#006b58] font-semibold">{finding.codeEvidence}</span>
                        ) : (
                          <span className="text-[#FF5C8D] italic">No matching evidence found in inspected files</span>
                        )}
                      </div>
                    </div>

                    {/* Faculty Advisory Note */}
                    {finding.facultyGuidance && (
                      <div className="bg-[#EBF7F5] border border-[#00A389] p-2 font-sans text-xs text-[#004d40] flex items-start gap-1.5">
                        <AlertTriangle size={14} className="shrink-0 mt-0.5 text-[#00A389]" />
                        <div>
                          <strong>Faculty Advisory:</strong> {finding.facultyGuidance}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <CheckCircle size={32} className="mx-auto text-[#006b58] mb-2" />
                <p className="font-display font-bold text-sm text-[#1c1b1b]">
                  No findings in this category
                </p>
                <p className="font-sans text-xs text-[#4b4731]">
                  All inspected technology and documentation items satisfied verification criteria.
                </p>
              </div>
            )}
          </div>
        </>
      )}

      {/* ── Phase 6: Git Development History & Commit Velocity ── */}
      <GitDevelopmentHistorySection
        gitHistory={gitHistory}
        loading={gitLoading}
        analyzing={gitAnalyzing}
        error={gitError}
        onAnalyze={onAnalyzeGit}
      />
    </div>
  );
}

interface EvidenceSourceDef {
  id: string;
  name: string;
  label: string;
  description: string;
  icon: typeof FileCode;
  badgeBg: string;
}

const EVIDENCE_SOURCES: EvidenceSourceDef[] = [
  {
    id: 'code_quality',
    name: 'Code Quality',
    label: '1. Code Quality Evidence',
    description: 'Complexity metrics, class/function structure, and AST quality findings.',
    icon: FileCode,
    badgeBg: 'bg-[#ffe600] text-[#121212]',
  },
  {
    id: 'similarity',
    name: 'Code Similarity',
    label: '2. Code Similarity Evidence',
    description: 'Token Jaccard overlap, syntax tree similarity, and candidate peer matches.',
    icon: Layers,
    badgeBg: 'bg-[#FF5C8D] text-white',
  },
  {
    id: 'documentation',
    name: 'Documentation',
    label: '3. Documentation & Consistency Evidence',
    description: 'Documented claims, section coverage, tech stack consistency, and code-doc mismatches.',
    icon: BookOpen,
    badgeBg: 'bg-[#D8B4FE] text-[#121212]',
  },
  {
    id: 'git_history',
    name: 'Git History',
    label: '4. Git Development History Evidence',
    description: 'Commit tempo, author distribution, batch commits, timeline continuity, and shallow history.',
    icon: GitBranch,
    badgeBg: 'bg-[#00E5BE] text-[#121212]',
  },
];

function formatAnalysisStatus(status: string) {
  switch (status.toLowerCase()) {
    case 'completed':
      return { label: 'Deterministic: Completed', bg: 'bg-[#00E5BE] text-[#121212]' };
    case 'processing':
      return { label: 'Deterministic: Processing', bg: 'bg-[#ffe600] text-[#121212]' };
    case 'insufficient_evidence':
      return { label: 'Deterministic: Insufficient Evidence', bg: 'bg-[#FFF4D6] text-[#b43b5b]' };
    case 'failed':
    case 'error':
      return { label: 'Deterministic: Failed', bg: 'bg-[#FF5C8D] text-white' };
    case 'not_started':
    default:
      return { label: 'Deterministic: Not Started', bg: 'bg-[#FAF6EE] text-[#4b4731]' };
  }
}

function formatLLMStatus(status?: string | null) {
  switch ((status || 'not_requested').toLowerCase()) {
    case 'completed':
      return { label: 'LLM: Completed', bg: 'bg-[#00E5BE] text-[#121212]' };
    case 'error':
      return { label: 'LLM: Unavailable / Rate-Limited', bg: 'bg-[#FF5C8D] text-white' };
    case 'disabled':
      return { label: 'LLM: Disabled by Config', bg: 'bg-[#FAF6EE] text-[#4b4731]' };
    case 'insufficient_evidence':
      return { label: 'LLM: Insufficient Evidence', bg: 'bg-[#FFF4D6] text-[#b43b5b]' };
    case 'partial':
      return { label: 'LLM: Partial', bg: 'bg-[#ffe600] text-[#121212]' };
    case 'not_requested':
    default:
      return { label: 'LLM: Not Requested', bg: 'bg-[#FAF6EE] text-[#4b4731]' };
  }
}

function getAdvisoryStyle(category: string) {
  switch (category) {
    case 'Multiple Observable Signals Requiring Faculty Review':
      return {
        bg: 'bg-[#FFF4D6]',
        badgeBg: 'bg-[#FF5C8D] text-white',
        border: 'border-[#121212]',
        icon: AlertTriangle,
        iconColor: 'text-[#b43b5b]',
        tag: 'Advisory Review Flagged',
      };
    case 'Some Observable Signals':
      return {
        bg: 'bg-[#FFF9E6]',
        badgeBg: 'bg-[#ffe600] text-[#1c1b1b]',
        border: 'border-[#121212]',
        icon: Info,
        iconColor: 'text-[#1c1b1b]',
        tag: 'Observable Signals Detected',
      };
    case 'Few Observable Signals':
      return {
        bg: 'bg-[#FAF6EE]',
        badgeBg: 'bg-[#00E5BE] text-[#1c1b1b]',
        border: 'border-[#121212]',
        icon: CheckCircle,
        iconColor: 'text-[#006b58]',
        tag: 'Low Advisory Signals',
      };
    case 'Insufficient Evidence':
    default:
      return {
        bg: 'bg-[#FAF6EE]',
        badgeBg: 'bg-[#E2DDD3] text-[#4b4731]',
        border: 'border-[#121212]',
        icon: Info,
        iconColor: 'text-[#4b4731]',
        tag: 'Baseline Evidence',
      };
  }
}

function getInnovationAdvisoryStyle(category: string) {
  switch (category) {
    case 'Strong Distinctive Elements':
      return {
        bg: 'bg-[#C7F9EE]',
        border: 'border-[#00876c]',
        iconColor: 'text-[#006b58]',
        badgeBg: 'bg-[#00E5BE] text-[#121212]',
        tag: 'Strong Distinction',
        icon: Award,
      };
    case 'Some Distinctive Elements':
      return {
        bg: 'bg-[#E6FAF5]',
        border: 'border-[#00a887]',
        iconColor: 'text-[#00876c]',
        badgeBg: 'bg-[#70EFDE] text-[#121212]',
        tag: 'Moderate Distinction',
        icon: Sparkles,
      };
    case 'Limited Differentiation':
      return {
        bg: 'bg-[#FFF9E6]',
        border: 'border-[#d4a000]',
        iconColor: 'text-[#7a5c00]',
        badgeBg: 'bg-[#FFE600] text-[#121212]',
        tag: 'Standard / Conventional',
        icon: Layers,
      };
    case 'Faculty Review Required':
      return {
        bg: 'bg-[#FFE8EF]',
        border: 'border-[#e02050]',
        iconColor: 'text-[#b30030]',
        badgeBg: 'bg-[#FF5C8D] text-white',
        tag: 'Review Discrepancies',
        icon: AlertTriangle,
      };
    case 'Insufficient Evidence':
    default:
      return {
        bg: 'bg-[#FAF6EE]',
        border: 'border-[#121212]',
        iconColor: 'text-[#4b4731]',
        badgeBg: 'bg-[#E2DDD3] text-[#4b4731]',
        tag: 'Insufficient Baseline',
        icon: AlertCircle,
      };
  }
}

function getFeatureEvidenceBadge(type: string) {
  switch (type) {
    case 'verified_match':
      return {
        label: 'Verified Match (Doc + Code)',
        bg: 'bg-[#00E5BE] text-[#121212]',
        icon: CheckCircle,
      };
    case 'documented_feature':
      return {
        label: 'Documented Feature Claim',
        bg: 'bg-[#FFE600] text-[#121212]',
        icon: BookOpen,
      };
    case 'detected_implementation':
      return {
        label: 'Detected Code Component',
        bg: 'bg-[#D4F0FF] text-[#004d80]',
        icon: Code2,
      };
    case 'unverified_claim':
      return {
        label: 'Unverified Feature Claim',
        bg: 'bg-[#FFDEE7] text-[#990033]',
        icon: AlertCircle,
      };
    case 'proposed_future':
      return {
        label: 'Proposed / Roadmap Feature',
        bg: 'bg-[#D8B4FE] text-[#121212]',
        icon: Sparkles,
      };
    case 'insufficient_information':
    default:
      return {
        label: 'Insufficient Information',
        bg: 'bg-[#E2DDD3] text-[#4b4731]',
        icon: HelpCircle,
      };
  }
}

function getEvidenceStrengthBadge(confidence: number | null | undefined): { label: string; bg: string } {
  if (confidence === undefined || confidence === null) {
    return { label: 'Direct Metric', bg: 'bg-[#FAF6EE] text-[#4b4731] border-[#121212]' };
  }
  const val = Number(confidence);
  if (val >= 1.0) {
    return { label: 'Direct Metric', bg: 'bg-[#EBF7F5] text-[#006b58] border-[#006b58]' };
  }
  if (val >= 0.8) {
    return { label: 'Strong Heuristic', bg: 'bg-[#FFF9E6] text-[#7a5c00] border-[#7a5c00]' };
  }
  if (val >= 0.6) {
    return { label: 'Moderate Heuristic', bg: 'bg-[#FAF6EE] text-[#4b4731] border-[#121212]' };
  }
  return { label: 'Indirect Signal', bg: 'bg-[#FAF6EE] text-[#7c775f] border-[#7c775f]' };
}

function formatComparisonMethod(method?: string) {
  if (method === 'tfidf_cosine') return 'TF-IDF + Cosine Similarity';
  if (method === 'embedding_cosine') return 'Embeddings + Cosine Similarity';
  return method || 'Unavailable';
}

function getSignalsForSource(signals: AIAssistanceSignal[], sourceId: string): AIAssistanceSignal[] {
  if (!Array.isArray(signals)) return [];
  return signals.filter((sig) => {
    if (!sig) return false;
    const src = (sig.evidenceSource || (sig as any).evidence_source || (sig as any).source || '').toLowerCase();
    const cat = (sig.signalCategory || (sig as any).signal_category || (sig as any).category || '').toLowerCase();
    if (sourceId === 'code_quality') {
      return src.includes('quality') || src.includes('code') || cat.includes('quality') || cat.includes('code');
    }
    if (sourceId === 'similarity') {
      return src.includes('similar') || cat.includes('similar');
    }
    if (sourceId === 'documentation') {
      return src.includes('doc') || cat.includes('doc');
    }
    if (sourceId === 'git_history') {
      return src.includes('git') || src.includes('history') || cat.includes('git') || cat.includes('history');
    }
    return false;
  });
}

function OpenRouterUnavailableBanner({
  errorInfo,
  limitations,
  onRetry,
  analyzing,
}: {
  errorInfo?: LLMErrorInfo;
  limitations?: string[];
  onRetry?: () => void;
  analyzing?: boolean;
}) {
  const [showDetails, setShowDetails] = useState(false);
  const errorType = errorInfo?.error_type;
  const statusCode = errorInfo?.status_code;

  let explanation = errorInfo?.user_message;
  let action = errorInfo?.recommended_action;

  if (errorType === 'auth_invalid_key' || statusCode === 401) {
    explanation = explanation || 'Your AI API key is invalid or unauthorized.';
    action = action || 'Update the key in backend/.env configuration.';
  } else if (
    errorType === 'account_quota_exceeded' ||
    statusCode === 402 ||
    errorInfo?.limit_source === 'platform'
  ) {
    explanation =
      explanation ||
      'AI account quota has been exceeded or credits are depleted.';
    action =
      action ||
      'You can configure another authorized AI account or wait for quota reset.';
  } else if (errorType === 'upstream_provider_overloaded' || statusCode === 429) {
    explanation =
      explanation ||
      'The selected model provider is temporarily overloaded (HTTP 429).';
    action =
      action ||
      'The upstream model is temporarily overloaded. You can retry in a few moments.';
  } else if (
    errorType === 'service_unavailable' ||
    statusCode === 502 ||
    statusCode === 503
  ) {
    explanation =
      explanation ||
      'AI service or upstream provider is temporarily unavailable.';
    action =
      action ||
      'AI service is temporarily unavailable. Please try again later.';
  } else if (errorType === 'network_error') {
    explanation = explanation || 'Unable to connect to AI provider network.';
    action =
      action ||
      'Unable to connect to AI provider. Please check your internet connection or backend network settings.';
  } else if (errorType === 'timeout' || statusCode === 504) {
    explanation = explanation || 'AI request timed out.';
    action = action || 'AI request timed out. Please try again later.';
  } else {
    explanation =
      explanation ||
      limitations?.[0] ||
      'The AI service encountered a temporary communication issue.';
    action =
      action ||
      'Your deterministic project analysis is still available and authoritative.';
  }

  const bannerTitle = errorInfo?.title || 'AI interpretation is temporarily unavailable. Deterministic findings are still available.';

  return (
    <div
      className="p-3 bg-[#FFF9E6] border-2 border-[#121212] flex flex-col gap-2"
      style={{ boxShadow: '2.5px 2.5px 0px #121212' }}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <AlertCircle size={16} className="text-[#996500] shrink-0" />
          <span className="font-sans text-xs font-semibold text-[#1c1b1b]">
            {bannerTitle}
          </span>
          {statusCode && (
            <span className="font-mono text-[9px] font-bold bg-white border border-[#121212] px-1.5 py-0.2 shrink-0">
              HTTP {statusCode}
            </span>
          )}
          {errorType && (
            <span className="font-mono text-[9px] bg-[#FAF6EE] text-[#4b4731] border border-[#121212] px-1.5 py-0.2 shrink-0">
              {errorType}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="font-mono text-[10px] font-bold text-[#4b4731] hover:text-[#1c1b1b] underline cursor-pointer"
          >
            {showDetails ? 'Hide Details' : 'Details'}
          </button>
          {onRetry && (
            <button
              onClick={onRetry}
              disabled={analyzing}
              className="btn-secondary text-[10px] py-0.5 px-2 flex items-center gap-1 cursor-pointer"
            >
              <RefreshCw size={10} className={analyzing ? 'animate-spin' : ''} />
              {analyzing ? 'Retrying...' : 'Retry'}
            </button>
          )}
        </div>
      </div>

      {showDetails && (
        <div className="bg-white border border-[#121212] p-2.5 flex flex-col gap-1 text-[11px] font-sans mt-1">
          <div>
            <strong className="font-mono uppercase text-[9px] text-[#4b4731] mr-1.5">Cause:</strong>
            <span className="text-[#1c1b1b]">{explanation}</span>
          </div>
          <div>
            <strong className="font-mono uppercase text-[9px] text-[#7a5c00] mr-1.5">Action:</strong>
            <span className="text-[#4b4731]">{action}</span>
          </div>
        </div>
      )}
    </div>
  );
}

function InnovationSection({
  innovation,
  analyzing,
  error,
  onAnalyze,
}: {
  innovation?: InnovationAnalysisResponse | null;
  analyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
}) {
  const [expandedFeature, setExpandedFeature] = useState<string | null>(null);
  const [expandedMatch, setExpandedMatch] = useState<string | null>(null);

  const inno = innovation;
  const isNotStarted = !inno || inno.analysisStatus === 'not_started' || inno.advisoryCategory === 'Not Started';

  // State B: Running with no prior data
  if (isNotStarted && analyzing) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-10 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <LoadingSpinner message="Analyzing project..." />
        <p className="font-mono text-xs text-[#4b4731] mt-3">Extracting profile, comparing cohort projects, and assessing distinctiveness...</p>
      </div>
    );
  }

  // State D: Failed with no prior data
  if (isNotStarted && error) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-8 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="max-w-md mx-auto flex flex-col items-center">
          <div className="w-14 h-14 bg-[#FF5C8D] border-2 border-[#121212] flex items-center justify-center mb-4" style={{ boxShadow: '3px 3px 0px #121212' }}>
            <AlertTriangle size={28} className="text-white" />
          </div>
          <h3 className="font-display font-bold text-2xl text-[#1c1b1b] mb-2">
            Analysis could not be completed
          </h3>
          <p className="font-sans text-sm text-[#4b4731] mb-6">
            {error}
          </p>
          <button
            onClick={onAnalyze}
            disabled={analyzing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing project...' : 'Retry Analysis'}
          </button>
        </div>
      </div>
    );
  }

  // State A: Not yet executed
  if (isNotStarted) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-8 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="max-w-md mx-auto flex flex-col items-center">
          <div className="w-14 h-14 bg-[#ffe600] border-2 border-[#121212] flex items-center justify-center mb-4" style={{ boxShadow: '3px 3px 0px #121212' }}>
            <Lightbulb size={28} className="text-[#1c1b1b]" />
          </div>
          <h3 className="font-display font-bold text-2xl text-[#1c1b1b] mb-2">
            Innovation &amp; Distinctiveness Analyzer
          </h3>
          <p className="font-sans text-sm text-[#4b4731] mb-6">
            Innovation analysis has not been run yet.
          </p>
          <button
            onClick={onAnalyze}
            disabled={analyzing}
            className="btn-primary flex items-center gap-2"
          >
            <RefreshCw size={16} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing project...' : 'Run Innovation Analysis'}
          </button>
        </div>
      </div>
    );
  }

  // State C: Analysis successful
  const profile = inno.profile;
  const features = profile?.features || [];
  const matches = inno.matches || [];
  const scores = inno.dimensionScores || {};
  const interpretation = inno.structuredInterpretation || {};
  const hasInterpretation = Boolean(
    interpretation.innovation_summary ||
    interpretation.problem_understanding ||
    interpretation.proposed_solution_understanding
  );

  const advisoryCategory = inno.advisoryCategory || 'Insufficient Evidence';
  const advisoryStyle = getInnovationAdvisoryStyle(advisoryCategory);

  const verifiedCount = features.filter((f) => f.evidence_type === 'verified_match').length;
  const detectedCount = features.filter((f) => f.evidence_type === 'detected_implementation').length;
  const docOnlyCount = features.filter((f) => f.evidence_type === 'documented_feature').length;
  const unverifiedCount = features.filter((f) => f.evidence_type === 'unverified_claim').length;
  const proposedCount = features.filter((f) => f.evidence_type === 'proposed_future').length;

  return (
    <div className="flex flex-col gap-6 pt-6 border-t-2 border-[#121212]">
      {/* ── Top Header Card ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b-2 border-[#121212] mb-4 gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <span className="font-mono text-[10px] font-bold bg-[#ffe600] px-2 py-0.5 border border-[#121212] uppercase">
                {inno.llmProvider === 'gemini' ? 'Google Gemini 2.5 Flash' : 'Phase 7B Engine'}
              </span>
              <span className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] ${advisoryStyle.badgeBg}`}>
                {advisoryCategory}
              </span>
              {inno.confidenceClassification && (
                <span className="font-mono text-[10px] font-bold bg-[#EBF7F5] text-[#006b58] px-2 py-0.5 border border-[#006b58]">
                  Confidence: {inno.confidenceClassification}
                </span>
              )}
              <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] text-[#4b4731] px-2 py-0.5 border border-[#121212]">
                Cohort: {inno.cohortSize} projects
              </span>
            </div>
            <h2 className="font-display font-bold text-xl text-[#1c1b1b] flex items-center gap-2">
              <Lightbulb size={20} className="text-[#1c1b1b]" />
              Innovation &amp; Distinctiveness Analysis
            </h2>
            <p className="font-sans text-xs text-[#4b4731] mt-0.5">
              Assesses distinctive technical contributions and compares features against peer projects with transparent confidence ratings.
            </p>
          </div>
          <button
            className="btn-primary flex items-center gap-1.5 cursor-pointer disabled:opacity-50 shrink-0 text-xs py-2 px-3"
            onClick={onAnalyze}
            disabled={analyzing}
          >
            <RefreshCw size={13} className={analyzing ? 'animate-spin' : ''} />
            {analyzing ? 'Analyzing project...' : 'Re-analyze Innovation'}
          </button>
        </div>

        {inno.confidenceRationale && (
          <div className="mb-4 p-2.5 bg-[#FAF6EE] border border-[#121212] text-xs font-sans text-[#4b4731] flex items-center gap-2">
            <Info size={14} className="shrink-0 text-[#006b58]" />
            <span><strong className="font-mono text-[10px] text-[#1c1b1b] uppercase">Confidence Rationale:</strong> {inno.confidenceRationale}</span>
          </div>
        )}

        {/* Re-analysis error banner */}
        {error && (
          <div className="mb-4 p-3 bg-[#FFE8EF] border-2 border-[#121212] text-xs font-sans text-[#b30030] flex items-center justify-between">
            <span>Re-analysis failed: {error}. Showing previous analysis results.</span>
          </div>
        )}

        {/* State F: LLM Unavailable Banner */}
        {inno.llmInterpretationStatus === 'error' ? (
          <OpenRouterUnavailableBanner
            errorInfo={interpretation?.llm_error}
            limitations={inno.limitations}
            onRetry={onAnalyze}
            analyzing={analyzing}
          />
        ) : inno.llmInterpretationStatus === 'disabled' ? (
          <div className="p-3 bg-[#FAF6EE] border-2 border-[#121212] text-xs font-sans text-[#4b4731] flex items-center gap-2">
            <Info size={16} className="shrink-0 text-[#4b4731]" />
            <span>AI interpretation is disabled in system configuration (LLM_ENABLED=false). Deterministic analysis is active.</span>
          </div>
        ) : null}
      </div>

      {/* ── Section A: Project Profile ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
          <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
            <Cpu size={15} />
            A. Project Profile
          </span>
          <span className="font-mono text-[10px] text-[#4b4731]">
            Domain: {profile?.domain || 'General Software'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Problem */}
          <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
            <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-1">
              Problem Being Solved
            </span>
            <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed">
              {((profile as any)?.problem_statement || profile?.problemStatement) &&
                ((profile as any)?.problem_statement || profile?.problemStatement) !== 'Not identified from the available project documents.' ? (
                (profile as any)?.problem_statement || profile?.problemStatement
              ) : (
                <span className="text-[#7c775f] italic">Not identified from the available project documents.</span>
              )}
            </p>
          </div>

          {/* Solution */}
          <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
            <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-1">
              Proposed Solution
            </span>
            <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed">
              {((profile as any)?.proposed_solution || profile?.proposedSolution) &&
                ((profile as any)?.proposed_solution || profile?.proposedSolution) !== 'Not identified from the available project documents.' ? (
                (profile as any)?.proposed_solution || profile?.proposedSolution
              ) : (
                <span className="text-[#7c775f] italic">Not identified from the available project documents.</span>
              )}
            </p>
          </div>
        </div>

        {/* Tech Stack Pills */}
        <div className="mt-4 pt-3 border-t border-[#121212]">
          <span className="font-mono text-[10px] font-bold uppercase text-[#4b4731] block mb-2">
            Technologies Used
          </span>
          <div className="flex flex-wrap gap-1.5">
            {(() => {
              const techObj = profile?.technologyStack || (profile as any)?.technology_stack;
              const techItems = [
                ...(Array.isArray(techObj?.languages) ? techObj.languages : []),
                ...(Array.isArray(techObj?.frameworks) ? techObj.frameworks : []),
                ...(Array.isArray(techObj?.databases) ? techObj.databases : []),
                ...(Array.isArray(techObj?.libraries) ? techObj.libraries : []),
              ];
              if (techItems.length === 0) {
                return <span className="font-mono text-[11px] text-[#7c775f] italic">None detected</span>;
              }
              return techItems.map((tech, idx) => (
                <span key={idx} className="font-mono text-[11px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                  {tech}
                </span>
              ));
            })()}
          </div>
        </div>
      </div>

      {/* ── Section B: Feature Verification ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="border-b-2 border-[#121212] pb-2 mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
              <Boxes size={15} />
              B. Feature Verification
            </span>
            <span className="font-sans text-xs text-[#4b4731]">
              Verification of declared features against source code implementations.
            </span>
          </div>
          {/* Quick counts */}
          <div className="flex items-center gap-2 font-mono text-[10px] flex-wrap">
            <span className="bg-[#00E5BE] text-[#121212] px-2 py-0.5 border border-[#121212] font-bold">{verifiedCount} Verified</span>
            <span className="bg-[#D4F0FF] text-[#004d80] px-2 py-0.5 border border-[#121212] font-bold">{detectedCount} Code</span>
            <span className="bg-[#FFE600] text-[#121212] px-2 py-0.5 border border-[#121212] font-bold">{docOnlyCount} Doc</span>
            <span className="bg-[#FFDEE7] text-[#990033] px-2 py-0.5 border border-[#121212] font-bold">{unverifiedCount} Unverified</span>
            {proposedCount > 0 && (
              <span className="bg-[#D8B4FE] text-[#121212] px-2 py-0.5 border border-[#121212] font-bold">{proposedCount} Roadmap</span>
            )}
          </div>
        </div>

        {features.length > 0 ? (
          <div className="overflow-x-auto border border-[#121212]">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-[#FFE600] border-b border-[#121212] font-bold text-[10px] uppercase">
                  <th className="p-2.5 border-r border-[#121212]">Feature</th>
                  <th className="p-2.5 border-r border-[#121212]">Evidence Source</th>
                  <th className="p-2.5 border-r border-[#121212]">Status</th>
                  <th className="p-2.5">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#121212] bg-white">
                {features.map((feat, idx) => {
                  const badge = getFeatureEvidenceBadge(feat.evidence_type);
                  const isExp = expandedFeature === feat.name;
                  return (
                    <Fragment key={feat.name || idx}>
                      <tr className="hover:bg-[#FAF6EE]">
                        <td className="p-2.5 border-r border-[#121212] font-bold text-[#1c1b1b]">
                          {feat.name}
                        </td>
                        <td className="p-2.5 border-r border-[#121212] text-[#4b4731] max-w-xs truncate">
                          {feat.code_reference || feat.doc_reference || 'Manifest detection'}
                        </td>
                        <td className="p-2.5 border-r border-[#121212]">
                          <span className={`px-2 py-0.5 text-[10px] font-bold border border-[#121212] inline-block ${badge.bg}`}>
                            {badge.label}
                          </span>
                        </td>
                        <td className="p-2.5 whitespace-nowrap">
                          <button
                            onClick={() => setExpandedFeature(isExp ? null : feat.name)}
                            className="font-mono text-[10px] font-bold text-[#1c1b1b] underline hover:text-[#00876c]"
                          >
                            {isExp ? 'Hide Evidence' : 'View Evidence'}
                          </button>
                        </td>
                      </tr>
                      {isExp && (
                        <tr className="bg-[#FAF6EE] border-b border-[#121212]">
                          <td colSpan={4} className="p-3 text-xs font-sans space-y-1">
                            {feat.description && (
                              <p className="text-[#1c1b1b]"><strong className="font-mono text-[10px]">Description:</strong> {feat.description}</p>
                            )}
                            {feat.code_reference && (
                              <p className="font-mono text-[11px] text-[#006b58]"><strong className="text-[10px]">Code:</strong> {feat.code_reference}</p>
                            )}
                            {feat.doc_reference && (
                              <p className="font-mono text-[11px] text-[#4b4731]"><strong className="text-[10px]">Doc:</strong> {feat.doc_reference}</p>
                            )}
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="font-sans text-xs text-[#7c775f] italic">
            No discrete features extracted from codebase structure.
          </p>
        )}
      </div>

      {/* ── Section C: Similarity With Other Projects ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
          <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
            <Users size={15} />
            C. Similarity With Other Projects ({inno.cohortSize} compared)
          </span>
          <span className="font-mono text-[10px] text-[#4b4731]">
            Method: {formatComparisonMethod(inno.comparisonMethod)}
          </span>
        </div>

        {inno.cohortSize === 0 || matches.length === 0 ? (
          <div className="p-4 bg-[#FAF6EE] border border-[#121212] text-center">
            <p className="font-sans text-xs text-[#4b4731]">
              No other student submissions are available for comparison.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto border border-[#121212]">
            <table className="w-full text-left font-mono text-xs border-collapse">
              <thead>
                <tr className="bg-[#FFE600] border-b border-[#121212] font-bold text-[10px] uppercase">
                  <th className="p-2.5 border-r border-[#121212]">Matching Project</th>
                  <th className="p-2.5 border-r border-[#121212]">Overall Similarity</th>
                  <th className="p-2.5 border-r border-[#121212]">Important Differences</th>
                  <th className="p-2.5">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#121212] bg-white">
                {matches.slice(0, 5).map((m: any, idx) => {
                  const simPct = Math.round((m.overall_similarity ?? m.overallSimilarity ?? 0) * 100);
                  const isExp = expandedMatch === (m.compared_project_id ?? m.comparedProjectId);
                  return (
                    <Fragment key={(m.compared_project_id ?? m.comparedProjectId) || idx}>
                      <tr className="hover:bg-[#FAF6EE]">
                        <td className="p-2.5 border-r border-[#121212] font-bold text-[#1c1b1b]">
                          {m.compared_project_title || m.comparedProjectTitle || m.compared_project_id || m.comparedProjectId}
                        </td>
                        <td className="p-2.5 border-r border-[#121212]">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-2 bg-[#FAF6EE] border border-[#121212] overflow-hidden">
                              <div
                                className="h-full bg-[#FF5C8D]"
                                style={{ width: `${Math.min(simPct, 100)}%` }}
                              />
                            </div>
                            <span className="font-bold text-[11px]">{simPct}%</span>
                          </div>
                          <span className="font-mono text-[9px] text-[#7c775f] block mt-0.5">Screening Signal</span>
                        </td>
                        <td className="p-2.5 border-r border-[#121212] text-[#4b4731] font-sans text-xs max-w-xs">
                          <p className="line-clamp-2">{m.difference_summary || m.differenceSummary || 'Distinct implementation architectures.'}</p>
                        </td>
                        <td className="p-2.5 whitespace-nowrap">
                          <button
                            onClick={() => setExpandedMatch(isExp ? null : (m.compared_project_id ?? m.comparedProjectId))}
                            className="font-mono text-[10px] font-bold text-[#1c1b1b] underline hover:text-[#00876c] cursor-pointer"
                          >
                            {isExp ? 'Hide Details' : 'View Details'}
                          </button>
                        </td>
                      </tr>
                      {isExp && (
                        <tr className="bg-[#FAF6EE] border-b border-[#121212]">
                          <td colSpan={4} className="p-3 text-xs font-mono space-y-2">
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                              <div className="bg-white border border-[#121212] p-1.5">Problem Sim: {Math.round((m.problem_similarity ?? m.problemSimilarity ?? 0) * 100)}%</div>
                              <div className="bg-white border border-[#121212] p-1.5">Solution Sim: {Math.round((m.solution_similarity ?? m.solutionSimilarity ?? 0) * 100)}%</div>
                              <div className="bg-white border border-[#121212] p-1.5">Tech Overlap: {Math.round((m.technology_overlap ?? m.technologyOverlap ?? 0) * 100)}%</div>
                            </div>
                            <p className="font-sans text-[11px] text-[#4b4731] italic">
                              Notice: Similarity indices are automated screening signals intended for viva preparation, not plagiarism determinations.
                            </p>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Section D: Innovation Assessment ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
          <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
            <Target size={15} />
            D. Innovation Assessment
          </span>
          <span className="font-mono text-[10px] text-[#4b4731]">
            Multi-dimensional deterministic evaluation
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {[
            { key: 'problem_distinctiveness', label: 'Problem Distinctiveness', desc: 'Distinctness of problem scope from cohort' },
            { key: 'solution_distinctiveness', label: 'Solution Distinctiveness', desc: 'Distinctness of technical approach from cohort' },
            { key: 'feature_differentiation', label: 'Feature Differentiation', desc: 'Non-standard features distinct from peers' },
            { key: 'technical_contribution', label: 'Technical Contribution', desc: 'Engineering complexity & component depth' },
            { key: 'evidence_supporting_claim', altKey: 'evidence_quality', label: 'Supporting Evidence', desc: 'Proportion of features verified in code' },
          ].map(({ key, altKey, label, desc }) => {
            const rawScore = (scores as any)[key]?.score ?? (scores as any)[key] ?? (altKey ? ((scores as any)[altKey]?.score ?? (scores as any)[altKey]) : undefined);
            const isInsufficient = rawScore === null || rawScore === undefined;
            const pct = isInsufficient ? 0 : Math.round(Number(rawScore) * 100);

            return (
              <div key={key} className="p-3 bg-[#FAF6EE] border border-[#121212] flex flex-col justify-between">
                <div>
                  <span className="font-mono text-[10px] font-bold text-[#1c1b1b] block leading-tight">
                    {label}
                  </span>
                  <span className="font-sans text-[10px] text-[#7c775f] block mt-0.5">
                    {desc}
                  </span>
                </div>
                <div className="mt-3">
                  {isInsufficient ? (
                    <div className="flex flex-col gap-1">
                      <span className="font-mono text-[9px] font-bold bg-[#E2DDD3] text-[#4b4731] px-1.5 py-0.5 border border-[#121212] inline-block w-fit">
                        Insufficient Evidence
                      </span>
                      <span className="font-sans text-[9px] text-[#7c775f] leading-tight">
                        Not enough data or cohort peers to evaluate.
                      </span>
                    </div>
                  ) : (
                    <div>
                      <div className="w-full h-2 bg-white border border-[#121212] overflow-hidden mb-1">
                        <div
                          className="h-full bg-[#00E5BE]"
                          style={{ width: `${Math.max(pct, 4)}%` }}
                        />
                      </div>
                      <div className="flex justify-between font-mono text-[10px] font-bold">
                        <span>{pct}%</span>
                        <span className="text-[#4b4731]">
                          {pct >= 70 ? 'High' : pct >= 40 ? 'Moderate' : 'Baseline'}
                        </span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Section E: AI Interpretation (Optional / Advisory) ── */}
      {hasInterpretation ? (
        <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
              <Sparkles size={15} />
              E. AI Advisory Interpretation
            </span>
            <span className="font-mono text-[10px] bg-[#FFE600] px-2 py-0.5 border border-[#121212] font-bold">
              Advisory Only
            </span>
          </div>

          <div className="space-y-4 font-sans text-xs">
            {/* Executive Summary */}
            {interpretation.innovation_summary && (
              <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
                <strong className="font-mono text-[10px] uppercase text-[#4b4731] block mb-1">Summary</strong>
                <p className="text-[#1c1b1b] leading-relaxed">{interpretation.innovation_summary}</p>
              </div>
            )}

            {/* Distinctive Features */}
            {interpretation.distinctive_elements && interpretation.distinctive_elements.length > 0 && (
              <div>
                <strong className="font-mono text-[10px] uppercase text-[#4b4731] block mb-1">Distinctive Elements</strong>
                <ul className="list-disc list-inside space-y-0.5 text-[#1c1b1b]">
                  {interpretation.distinctive_elements.map((el: string, i: number) => (
                    <li key={i}>{el}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Innovation Strengths */}
            {interpretation.innovation_strengths && interpretation.innovation_strengths.length > 0 && (
              <div className="p-3 bg-[#EBF7F5] border border-[#006b58]">
                <strong className="font-mono text-[10px] uppercase text-[#006b58] block mb-1">Innovation Strengths</strong>
                <ul className="list-disc list-inside space-y-0.5 text-[#1c1b1b]">
                  {interpretation.innovation_strengths.map((str: string, i: number) => (
                    <li key={i}>{str}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Missing Evidence / Deficits */}
            {interpretation.missing_evidence && interpretation.missing_evidence.length > 0 && (
              <div className="p-3 bg-[#FFF0F5] border border-[#b43b5b]">
                <strong className="font-mono text-[10px] uppercase text-[#b43b5b] block mb-1">Identified Evidence Deficits &amp; Unverified Claims</strong>
                <ul className="list-disc list-inside space-y-0.5 text-[#1c1b1b]">
                  {interpretation.missing_evidence.map((me: string, i: number) => (
                    <li key={i}>{me}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Improvement Recommendations */}
            {interpretation.improvement_recommendations && interpretation.improvement_recommendations.length > 0 && (
              <div className="p-3 bg-[#FAF6EE] border border-[#121212]">
                <strong className="font-mono text-[10px] uppercase text-[#7a5c00] block mb-1">Engineering Recommendations</strong>
                <ul className="list-disc list-inside space-y-0.5 text-[#1c1b1b]">
                  {interpretation.improvement_recommendations.map((rec: string, i: number) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Viva Questions */}
            {(() => {
              const questions = interpretation.faculty_follow_up_recommendations || (interpretation as any).recommended_viva_questions || [];
              if (!Array.isArray(questions) || questions.length === 0) return null;
              return (
                <div>
                  <strong className="font-mono text-[10px] uppercase text-[#4b4731] block mb-1">Suggested Faculty Viva Questions</strong>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-1">
                    {questions.map((q: any, i: number) => (
                      <div key={i} className="p-2.5 bg-[#FAF6EE] border border-[#121212]">
                        <span className="font-mono text-[10px] font-bold text-[#006b58] block mb-0.5">Q{i + 1}</span>
                        <p className="font-medium text-[#1c1b1b]">{typeof q === 'string' ? q : q?.question || String(q)}</p>
                        {q?.context && <p className="font-mono text-[10px] text-[#7c775f] mt-1">{q.context}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        </div>
      ) : inno.llmInterpretationStatus === 'error' ? (
        <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b] flex items-center gap-1.5">
              <Sparkles size={15} />
              E. AI Advisory Interpretation
            </span>
            <span className="font-mono text-[10px] bg-[#FF5C8D] text-white px-2 py-0.5 border border-[#121212] font-bold">
              Service Unavailable
            </span>
          </div>
          <OpenRouterUnavailableBanner
            errorInfo={interpretation?.llm_error}
            limitations={inno.limitations}
            onRetry={onAnalyze}
            analyzing={analyzing}
          />
        </div>
      ) : null}
    </div>
  );
}

function AIAssistanceTab({
  analysis,
  aiAssistance,
  analyzing,
  error,
  onAnalyze,
  innovation,
  innovAnalyzing,
  innovError,
  onAnalyzeInnovation,
}: {
  analysis: ProjectAnalysis | null;
  aiAssistance?: AIAssistanceResult | null;
  analyzing: boolean;
  error: string | null;
  onAnalyze: () => void;
  innovation?: InnovationAnalysisResponse | null;
  innovAnalyzing: boolean;
  innovError: string | null;
  onAnalyzeInnovation: () => void;
}) {
  const ai = aiAssistance ?? analysis?.aiAssistance ?? null;
  const inno = innovation ?? analysis?.innovation ?? null;

  if (!analysis && !ai && !inno) return <UnavailablePanel featureName="AI Assistance & Innovation" />;

  const isNotStarted = !ai || ai.analysisStatus === 'not_started';
  const interpretation = ai?.structuredInterpretation || {};
  const hasInterpretation = Boolean(
    interpretation.executive_summary || interpretation.explanation_of_patterns,
  );
  const evidenceSignals: AIAssistanceSignal[] = Array.isArray(ai?.evidenceSummary) ? ai.evidenceSummary : [];
  const availableSignals = evidenceSignals.filter((signal) => (signal.availabilityStatus || (signal as any).availability_status) === 'available');
  const unavailableSignals = evidenceSignals.filter((signal) => (signal.availabilityStatus || (signal as any).availability_status) !== 'available');
  const list = (items?: any) => (Array.isArray(items) && items.length > 0 ? items : ['None recorded.']);

  const [filter, setFilter] = useState<'all' | 'available' | 'unavailable' | 'code_quality' | 'similarity' | 'documentation' | 'git_history'>('all');
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({
    code_quality: false,
    similarity: false,
    documentation: false,
    git_history: false,
    other: false,
  });
  const [expandedSignals, setExpandedSignals] = useState<Record<string, boolean>>({});

  const findings = Array.isArray(interpretation?.findings) ? interpretation.findings : [];
  const [findingCategoryFilter, setFindingCategoryFilter] = useState<string>('all');
  const [findingPriorityFilter, setFindingPriorityFilter] = useState<string>('all');
  const [expandedFindings, setExpandedFindings] = useState<Record<number, boolean>>({});

  const toggleFinding = (idx: number) => {
    setExpandedFindings((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  const findingCategories = Array.from(new Set(findings.map((f: any) => f.category).filter(Boolean)));

  const filteredFindings = findings.filter((f: any) => {
    if (findingCategoryFilter !== 'all' && f.category !== findingCategoryFilter) return false;
    if (findingPriorityFilter !== 'all' && (f.priority || '').toLowerCase() !== findingPriorityFilter.toLowerCase()) return false;
    return true;
  });

  const getPriorityStyle = (priority?: string) => {
    const p = (priority || 'medium').toLowerCase();
    switch (p) {
      case 'critical':
        return { label: 'CRITICAL', bg: 'bg-[#FF5C8D] text-white border-[#121212]' };
      case 'high':
        return { label: 'HIGH', bg: 'bg-[#FFF4D6] text-[#b43b5b] border-[#b43b5b]' };
      case 'medium':
        return { label: 'MEDIUM', bg: 'bg-[#FFE600] text-[#121212] border-[#121212]' };
      case 'low':
        return { label: 'LOW', bg: 'bg-[#EBF7F5] text-[#006b58] border-[#006b58]' };
      case 'informational':
      default:
        return { label: 'INFO', bg: 'bg-[#FAF6EE] text-[#4b4731] border-[#121212]' };
    }
  };

  const toggleSource = (sourceId: string) => {
    setExpandedSources((prev) => ({ ...prev, [sourceId]: !prev[sourceId] }));
  };

  const toggleSignal = (signalId: string) => {
    setExpandedSignals((prev) => ({ ...prev, [signalId]: !prev[signalId] }));
  };

  const assignedSignals = new Set<string>();
  EVIDENCE_SOURCES.forEach((s) => {
    getSignalsForSource(evidenceSignals, s.id).forEach((sig, idx) => {
      const sigId = sig.signalId || (sig as any).signal_id || `${s.id}-${idx}`;
      assignedSignals.add(sigId);
    });
  });
  const otherSignals = evidenceSignals.filter((sig, idx) => {
    const sigId = sig.signalId || (sig as any).signal_id || `other-${idx}`;
    return !assignedSignals.has(sigId);
  });

  const advisoryCategory = ai?.advisoryCategory || 'Insufficient Evidence';
  const advisoryStyle = getAdvisoryStyle(advisoryCategory);
  const AdvisoryIcon = advisoryStyle.icon;

  const detStatus = formatAnalysisStatus(ai?.analysisStatus || 'not_started');
  const llmStatus = formatLLMStatus(ai?.llmInterpretationStatus);

  const activeSourcesCount = EVIDENCE_SOURCES.filter((s) =>
    getSignalsForSource(evidenceSignals, s.id).some((sig) => (sig.availabilityStatus || (sig as any).availability_status) === 'available')
  ).length;

  // Prioritize key main findings (one per source module)
  const mainFindings = (() => {
    const findings: Array<{
      signal: AIAssistanceSignal;
      sourceLabel: string;
      badgeBg: string;
    }> = [];

    for (const s of EVIDENCE_SOURCES) {
      const sigs = getSignalsForSource(availableSignals, s.id);
      if (sigs.length > 0) {
        findings.push({
          signal: sigs[0],
          sourceLabel: s.name,
          badgeBg: s.badgeBg,
        });
      }
    }
    return findings;
  })();

  const getFilteredSignalsForSource = (sourceId: string) => {
    const sourceSignals = getSignalsForSource(evidenceSignals, sourceId);
    if (filter === 'available') return sourceSignals.filter((s) => (s.availabilityStatus || (s as any).availability_status) === 'available');
    if (filter === 'unavailable') return sourceSignals.filter((s) => (s.availabilityStatus || (s as any).availability_status) !== 'available');
    return sourceSignals;
  };

  const displayedSources = EVIDENCE_SOURCES.filter((s) => {
    if (filter === 'all' || filter === 'available' || filter === 'unavailable') return true;
    return filter === s.id;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* ── Top Header Card & Action Controls ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="flex flex-col md:flex-row md:items-start justify-between pb-4 border-b-2 border-[#121212] mb-4 gap-4">
          <div>
            <h2 className="font-display font-bold text-2xl text-[#1c1b1b] flex items-center gap-2">
              <ShieldAlert size={24} className="text-[#1c1b1b]" />
              AI Assistance &amp; Advisory Review
            </h2>
            <p className="font-sans text-sm text-[#4b4731] mt-1 leading-relaxed">
              Deterministic multi-module evidence collection across Code Quality, Similarity, Documentation, and Git History, with optional OpenRouter Gemma LLM interpretation.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              className="btn-primary flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              onClick={onAnalyze}
              disabled={analyzing}
            >
              <RefreshCw size={13} className={analyzing ? 'animate-spin' : ''} />
              {analyzing
                ? 'Analyzing AI-Assistance...'
                : isNotStarted
                  ? 'Run AI-Assistance Analysis'
                  : 'Re-analyze AI-Assistance'}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-4">
            <ErrorBanner
              message={
                error.toLowerCase().includes('429') || error.toLowerCase().includes('rate')
                  ? 'Upstream OpenRouter free model (google/gemma-4-26b-a4b-it:free) is temporarily rate limited. Deterministic evidence collection remains fully operational and intact. Please try re-analyzing in a few moments.'
                  : error
              }
            />
          </div>
        )}

        {ai?.llmInterpretationStatus === 'error' && (
          <div className="mb-4">
            <OpenRouterUnavailableBanner
              errorInfo={interpretation?.llm_error}
              limitations={ai.limitations}
              onRetry={onAnalyze}
              analyzing={analyzing}
            />
          </div>
        )}

        {/* ── Compact Analysis Summary Bar ── */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2 mb-4">
          <div className="bg-[#FAF6EE] border border-[#121212] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#4b4731] block">Analysis Status</span>
            <span className="font-mono text-[11px] font-bold text-[#1c1b1b]">{detStatus.label}</span>
          </div>
          <div className="bg-[#FAF6EE] border border-[#121212] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#4b4731] block">Total Signals</span>
            <span className="font-mono text-sm font-bold text-[#1c1b1b]">{evidenceSignals.length}</span>
          </div>
          <div className="bg-[#EBF7F5] border border-[#006b58] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#006b58] block">Available</span>
            <span className="font-mono text-sm font-bold text-[#006b58]">{availableSignals.length}</span>
          </div>
          <div className="bg-[#FFF0F5] border border-[#b43b5b] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#b43b5b] block">Unavailable</span>
            <span className="font-mono text-sm font-bold text-[#b43b5b]">{unavailableSignals.length}</span>
          </div>
          <div className="bg-[#FAF6EE] border border-[#121212] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#4b4731] block">Evidence Sources</span>
            <span className="font-mono text-sm font-bold text-[#1c1b1b]">{activeSourcesCount} / {EVIDENCE_SOURCES.length}</span>
          </div>
          <div className="bg-[#FAF6EE] border border-[#121212] p-2 text-center">
            <span className="font-mono text-[9px] uppercase tracking-wider text-[#4b4731] block">LLM Interpretation</span>
            <span className="font-mono text-[11px] font-bold text-[#1c1b1b]">{llmStatus.label}</span>
          </div>
        </div>

        {/* ── Deterministic Advisory Assessment Banner ── */}
        <div className={`${advisoryStyle.bg} border-2 ${advisoryStyle.border} p-5`} style={{ boxShadow: '2px 2px 0px #121212' }}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#121212] pb-3 mb-3">
            <div className="flex items-center gap-2">
              <AdvisoryIcon size={20} className={advisoryStyle.iconColor} />
              <span className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#1c1b1b]">
                Deterministic Advisory Assessment
              </span>
            </div>
            <span className={`font-mono text-[10px] font-bold px-2.5 py-0.5 border border-[#121212] self-start sm:self-auto ${advisoryStyle.badgeBg}`}>
              {advisoryStyle.tag}
            </span>
          </div>
          <h3 className="font-display font-bold text-2xl text-[#1c1b1b] leading-tight">
            {advisoryCategory}
          </h3>
          <div className="mt-3 bg-white border border-[#121212] p-3 text-xs text-[#4b4731] leading-relaxed">
            <span className="font-bold text-[#1c1b1b] font-mono uppercase text-[10px] block mb-0.5">
              Faculty Advisory Evaluation Notice (No AI Probability)
            </span>
            Evidence signals and advisory categories are screening indicators synthesized strictly from deterministic artifact analysis. They do NOT constitute proof of AI authorship or academic misconduct. ProjectLens does not compute or display a fabricated AI probability score.
          </div>
        </div>
      </div>

      {/* ── Main Findings (Prioritized Highlights) ── */}
      {mainFindings.length > 0 && (
        <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="border-b-2 border-[#121212] pb-2 mb-4 flex items-center justify-between">
            <div>
              <h3 className="font-display font-bold text-base text-[#1c1b1b] flex items-center gap-1.5">
                <Activity size={16} />
                Key Main Findings
              </h3>
              <p className="font-sans text-xs text-[#4b4731]">
                Prioritized deterministic observations across evaluated modules.
              </p>
            </div>
            <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
              {mainFindings.length} Highlighted
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {mainFindings.map((item, idx) => {
              const sig = item.signal;
              const sigId = sig.signalId || (sig as any).signal_id || `main-${idx}`;
              const sigObserved = sig.observedValue || (sig as any).observed_value || 'None';
              const sigExplanation = sig.explanation || 'No explanation provided.';
              const strength = getEvidenceStrengthBadge(sig.confidence);
              return (
                <div key={sigId} className="p-3 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col justify-between gap-2" style={{ boxShadow: '2px 2px 0px #121212' }}>
                  <div>
                    <div className="flex items-center justify-between gap-2 mb-1.5 flex-wrap">
                      <span className={`font-mono text-[9px] font-bold uppercase px-2 py-0.5 border border-[#121212] ${item.badgeBg}`}>
                        {item.sourceLabel}
                      </span>
                      <span className={`font-mono text-[9px] font-bold px-2 py-0.5 border ${strength.bg}`}>
                        {strength.label}
                      </span>
                    </div>
                    <div className="font-mono text-[11px] font-bold text-[#1c1b1b] mb-1">
                      {sigId}
                    </div>
                    <p className="font-sans text-xs text-[#1c1b1b] font-medium leading-snug line-clamp-2">
                      {sigExplanation}
                    </p>
                  </div>
                  <div className="bg-white border border-[#121212] px-2.5 py-1.5 font-mono text-[11px] text-[#4b4731] truncate">
                    <strong className="text-[#1c1b1b] mr-1">Observed:</strong>
                    {String(sigObserved)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Deterministic Evidence Signals by Source ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="flex flex-col md:flex-row md:items-start justify-between pb-3 border-b-2 border-[#121212] mb-4 gap-2">
          <div>
            <h3 className="font-display font-bold text-xl">Deterministic Evidence Signals by Source</h3>
            <p className="font-sans text-xs text-[#4b4731] mt-0.5">
              Compact expandable modules with honest heuristic strength ratings.
            </p>
          </div>
          <div className="font-mono text-[11px] text-[#4b4731] bg-[#FAF6EE] border border-[#121212] px-3 py-1">
            {availableSignals.length} Available • {unavailableSignals.length} Unavailable
          </div>
        </div>

        {/* Evidence Filter Bar */}
        <div className="flex flex-wrap items-center gap-1.5 p-2.5 bg-[#FAF6EE] border-2 border-[#121212] mb-5">
          <span className="font-mono text-[10px] uppercase font-bold text-[#4b4731] mr-1">Filter:</span>
          {[
            { id: 'all', label: `All (${evidenceSignals.length})` },
            { id: 'available', label: `Available (${availableSignals.length})` },
            { id: 'unavailable', label: `Unavailable (${unavailableSignals.length})` },
            { id: 'code_quality', label: 'Code Quality' },
            { id: 'similarity', label: 'Similarity' },
            { id: 'documentation', label: 'Documentation' },
            { id: 'git_history', label: 'Git History' },
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setFilter(tab.id as any)}
              className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] transition-colors cursor-pointer ${filter === tab.id
                  ? 'bg-[#121212] text-white'
                  : 'bg-white text-[#1c1b1b] hover:bg-[#FAF6EE]'
                }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Expandable Source Accordions */}
        <div className="flex flex-col gap-4">
          {displayedSources.map((source) => {
            const sourceSignals = getFilteredSignalsForSource(source.id);
            const SourceIcon = source.icon;
            const isExpanded = expandedSources[source.id] || false;
            const allSourceSignals = getSignalsForSource(evidenceSignals, source.id);
            const srcAvailable = allSourceSignals.filter((s) => (s.availabilityStatus || (s as any).availability_status) === 'available').length;
            const srcUnavailable = allSourceSignals.length - srcAvailable;

            return (
              <div key={source.id} className="bg-white border-2 border-[#121212]" style={{ boxShadow: '2px 2px 0px #121212' }}>
                {/* Accordion Toggle Header */}
                <button
                  type="button"
                  onClick={() => toggleSource(source.id)}
                  className="w-full p-3.5 bg-white flex items-center justify-between text-left hover:bg-[#FAF6EE] transition-colors cursor-pointer"
                >
                  <div className="flex items-center gap-2.5">
                    <div className={`p-1.5 border border-[#121212] ${source.badgeBg}`}>
                      <SourceIcon size={16} />
                    </div>
                    <div>
                      <h4 className="font-display font-bold text-sm text-[#1c1b1b]">{source.label}</h4>
                      <p className="font-sans text-[11px] text-[#4b4731]">{source.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2.5 shrink-0">
                    <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                      {allSourceSignals.length === 0
                        ? 'Unavailable'
                        : `${srcAvailable} Available / ${srcUnavailable} Unavailable`}
                    </span>
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                </button>

                {/* Collapsible Accordion Body */}
                {isExpanded && (
                  <div className="border-t-2 border-[#121212] p-4 bg-[#FAF6EE] flex flex-col gap-3">
                    {sourceSignals.length === 0 ? (
                      <div className="bg-white border border-dashed border-[#121212] p-4 text-center">
                        <p className="font-sans text-xs text-[#4b4731]">
                          No signals match the current filter for this module.
                        </p>
                      </div>
                    ) : (
                      sourceSignals.map((sig, sigIdx) => {
                        const sigId = sig.signalId || (sig as any).signal_id || `sig-${sigIdx}`;
                        const sigCategory = sig.signalCategory || (sig as any).category || (sig as any).signal_category || 'General';
                        const sigObserved = sig.observedValue || (sig as any).observed_value || 'None';
                        const sigExplanation = sig.explanation || 'No explanation provided.';
                        const sigAvail = (sig.availabilityStatus || (sig as any).availability_status || 'unavailable').toUpperCase();
                        const strength = getEvidenceStrengthBadge(sig.confidence);
                        const isSigExpanded = expandedSignals[sigId] || false;
                        const altList = Array.isArray(sig.alternativeExplanations)
                          ? sig.alternativeExplanations
                          : Array.isArray((sig as any).alternative_explanations)
                            ? (sig as any).alternative_explanations
                            : [];

                        return (
                          <div key={sigId} className="bg-white border-2 border-[#121212] p-3.5 flex flex-col gap-2">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-1.5">
                                <span className="font-mono text-[11px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                                  {sigId}
                                </span>
                                <span className="font-mono text-[10px] uppercase font-bold text-[#4b4731]">
                                  {sigCategory}
                                </span>
                                <span className={`font-mono text-[9px] font-bold px-2 py-0.5 border ${strength.bg}`}>
                                  {strength.label}
                                </span>
                              </div>
                              <span
                                className={`font-mono text-[9px] font-bold px-2 py-0.5 border ${sigAvail === 'AVAILABLE'
                                    ? 'bg-[#EBF7F5] text-[#006b58] border-[#006b58]'
                                    : 'bg-[#FFF0F5] text-[#b43b5b] border-[#b43b5b]'
                                  }`}
                              >
                                {sigAvail}
                              </span>
                            </div>

                            <div className="bg-[#FAF6EE] border border-[#121212] p-2 font-mono text-xs text-[#1c1b1b] break-words">
                              <strong className="text-[10px] text-[#4b4731] font-normal uppercase block mb-0.5">
                                Observed Value:
                              </strong>
                              {String(sigObserved)}
                            </div>

                            <p className="font-sans text-xs text-[#4b4731] leading-relaxed">
                              {sigExplanation}
                            </p>

                            {altList.length > 0 && (
                              <div className="mt-1">
                                <button
                                  type="button"
                                  onClick={() => toggleSignal(sigId)}
                                  className="font-mono text-[10px] font-bold text-[#006b58] flex items-center gap-1 hover:underline cursor-pointer"
                                >
                                  <Info size={12} />
                                  {isSigExpanded ? 'Hide Alternative Explanations' : `View Alternative Explanations (${altList.length})`}
                                </button>
                                {isSigExpanded && (
                                  <div className="bg-[#FAF6EE] border border-dashed border-[#121212] p-2.5 mt-1.5">
                                    <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#006b58] block mb-1">
                                      Plausible Alternative Explanations (Benign / Academic Context):
                                    </span>
                                    <ul className="flex flex-col gap-1 pl-4 list-disc text-xs text-[#4b4731]">
                                      {altList.map((alt: any, idx: number) => (
                                        <li key={idx}>{alt}</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}

          {otherSignals.length > 0 && (filter === 'all' || filter === 'available') && (
            <div className="bg-white border-2 border-[#121212]" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <button
                type="button"
                onClick={() => toggleSource('other')}
                className="w-full p-3.5 bg-white flex items-center justify-between text-left hover:bg-[#FAF6EE] transition-colors cursor-pointer"
              >
                <div>
                  <h4 className="font-display font-bold text-sm text-[#1c1b1b]">5. Additional Evidence Signals</h4>
                  <p className="font-sans text-[11px] text-[#4b4731]">Uncategorized or auxiliary signals</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                    {otherSignals.length} Signal(s)
                  </span>
                  {expandedSources.other ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </button>
              {expandedSources.other && (
                <div className="border-t-2 border-[#121212] p-4 bg-[#FAF6EE] flex flex-col gap-2">
                  {otherSignals.map((sig, sigIdx) => {
                    const sigId = sig.signalId || (sig as any).signal_id || `other-${sigIdx}`;
                    const sigObserved = sig.observedValue || (sig as any).observed_value || 'None';
                    const sigExplanation = sig.explanation || 'No explanation provided.';
                    const sigAvail = sig.availabilityStatus || (sig as any).availability_status || 'available';
                    return (
                      <div key={sigId} className="bg-white border-2 border-[#121212] p-3 flex flex-col gap-1.5">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-mono text-[10px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                            {sigId}
                          </span>
                          <span className="font-mono text-[10px] font-bold text-[#006b58]">{sigAvail}</span>
                        </div>
                        <p className="font-mono text-xs font-bold text-[#1c1b1b]">{sigObserved}</p>
                        <p className="font-sans text-xs text-[#4b4731]">{sigExplanation}</p>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* ── Actionable Guidance & Assistance Findings (10 Key Areas) ── */}
      {findings.length > 0 && (
        <div className="bg-white border-[2.5px] border-[#121212] p-6 flex flex-col gap-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="flex flex-col md:flex-row md:items-start justify-between pb-3 border-b-2 border-[#121212] gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1 flex-wrap">
                <span className="font-mono text-[10px] font-bold bg-[#FFE600] text-[#121212] px-2 py-0.5 border border-[#121212] uppercase">
                  {ai?.llmProvider === 'gemini' ? 'Google Gemini 2.5 Flash' : 'AI Guidance'}
                </span>
                <span className="font-mono text-[10px] font-bold bg-[#EBF7F5] text-[#006b58] px-2 py-0.5 border border-[#006b58]">
                  {findings.length} Assistance Areas Analyzed
                </span>
              </div>
              <h3 className="font-display font-bold text-xl flex items-center gap-2 text-[#1c1b1b]">
                <Sparkles size={20} className="text-[#1c1b1b]" />
                Actionable Findings &amp; Viva Recommendations
              </h3>
              <p className="font-sans text-xs text-[#4b4731] mt-0.5">
                Evidence-grounded project guidance across architecture, code maintainability, test coverage, and oral defense readiness.
              </p>
            </div>
            {/* Priority Filter */}
            <div className="flex items-center gap-1 flex-wrap shrink-0">
              <span className="font-mono text-[10px] text-[#4b4731] mr-1">Priority:</span>
              {['all', 'critical', 'high', 'medium', 'low', 'informational'].map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => setFindingPriorityFilter(p)}
                  className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] cursor-pointer transition-colors ${
                    findingPriorityFilter === p
                      ? 'bg-[#121212] text-white'
                      : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-[#FFE600]'
                  }`}
                >
                  {p.toUpperCase()}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter Buttons */}
          {findingCategories.length > 1 && (
            <div className="flex items-center gap-1.5 flex-wrap pb-1">
              <button
                type="button"
                onClick={() => setFindingCategoryFilter('all')}
                className={`font-mono text-[10px] font-bold px-2.5 py-1 border border-[#121212] cursor-pointer ${
                  findingCategoryFilter === 'all'
                    ? 'bg-[#121212] text-white'
                    : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-[#FFE600]'
                }`}
              >
                All Areas ({findings.length})
              </button>
              {findingCategories.map((cat: any) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setFindingCategoryFilter(cat)}
                  className={`font-mono text-[10px] font-bold px-2 py-1 border border-[#121212] cursor-pointer ${
                    findingCategoryFilter === cat
                      ? 'bg-[#121212] text-white'
                      : 'bg-white text-[#4b4731] hover:bg-[#FAF6EE]'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>
          )}

          {/* Findings Cards */}
          <div className="flex flex-col gap-4">
            {filteredFindings.map((finding: any, idx: number) => {
              const priorityStyle = getPriorityStyle(finding.priority);
              const isExpanded = expandedFindings[idx] ?? true;
              const whyMatters = finding.why_it_matters || finding.whyItMatters;
              const supporting = finding.supporting_evidence || finding.supportingEvidence;
              const action = finding.recommended_action || finding.recommendedAction;
              const benefit = finding.expected_benefit || finding.expectedBenefit;
              const sourceRef = finding.source_reference || finding.sourceReference;

              return (
                <div
                  key={idx}
                  className="bg-[#FAF6EE] border-2 border-[#121212] p-4 flex flex-col gap-3"
                  style={{ boxShadow: '2px 2px 0px #121212' }}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#121212] pb-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`font-mono text-[9px] font-bold px-2 py-0.5 border ${priorityStyle.bg}`}>
                        {priorityStyle.label}
                      </span>
                      <span className="font-mono text-[10px] font-bold bg-white text-[#1c1b1b] px-2 py-0.5 border border-[#121212]">
                        {finding.category}
                      </span>
                      {sourceRef && (
                        <span className="font-mono text-[9px] text-[#4b4731]">
                          Ref: {sourceRef}
                        </span>
                      )}
                    </div>
                    <button
                      type="button"
                      onClick={() => toggleFinding(idx)}
                      className="font-mono text-[10px] font-bold text-[#1c1b1b] hover:text-[#00876c] underline self-end sm:self-auto cursor-pointer"
                    >
                      {isExpanded ? 'Collapse' : 'Expand Details'}
                    </button>
                  </div>

                  <div>
                    <h4 className="font-display font-bold text-base text-[#1c1b1b]">
                      {finding.title}
                    </h4>
                    <p className="font-sans text-xs text-[#4b4731] mt-1 leading-relaxed">
                      {finding.description}
                    </p>
                  </div>

                  {isExpanded && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                      {/* Why it matters */}
                      {whyMatters && (
                        <div className="p-2.5 bg-white border border-[#121212]">
                          <span className="font-mono text-[9px] font-bold uppercase text-[#b43b5b] flex items-center gap-1 mb-1">
                            <AlertCircle size={12} className="text-[#b43b5b]" />
                            Why It Matters
                          </span>
                          <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed">
                            {whyMatters}
                          </p>
                        </div>
                      )}

                      {/* Supporting evidence */}
                      {supporting && (
                        <div className="p-2.5 bg-white border border-[#121212]">
                          <span className="font-mono text-[9px] font-bold uppercase text-[#4b4731] flex items-center gap-1 mb-1">
                            <FileText size={12} className="text-[#4b4731]" />
                            Supporting Evidence
                          </span>
                          <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed">
                            {supporting}
                          </p>
                        </div>
                      )}

                      {/* Recommended action */}
                      {action && (
                        <div className="p-2.5 bg-[#EBF7F5] border border-[#006b58]">
                          <span className="font-mono text-[9px] font-bold uppercase text-[#006b58] flex items-center gap-1 mb-1">
                            <CheckCircle size={12} className="text-[#006b58]" />
                            Recommended Action
                          </span>
                          <p className="font-sans text-xs text-[#1c1b1b] font-medium leading-relaxed">
                            {action}
                          </p>
                        </div>
                      )}

                      {/* Expected benefit */}
                      {benefit && (
                        <div className="p-2.5 bg-[#FFF9E6] border border-[#121212]">
                          <span className="font-mono text-[9px] font-bold uppercase text-[#7a5c00] flex items-center gap-1 mb-1">
                            <Sparkles size={12} className="text-[#7a5c00]" />
                            Expected Benefit
                          </span>
                          <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed">
                            {benefit}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── LLM Advisory Interpretation Section ── */}
      {hasInterpretation ? (
        <div className="bg-white border-[2.5px] border-[#121212] p-6 flex flex-col gap-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="flex flex-col md:flex-row md:items-start justify-between pb-3 border-b-2 border-[#121212] gap-3">
            <div>
              <h3 className="font-display font-bold text-xl flex items-center gap-2">
                <Sparkles size={20} className="text-[#1c1b1b]" />
                LLM Advisory Interpretation
              </h3>
              <p className="font-sans text-xs text-[#4b4731] mt-1">
                Contextual synthesis generated by{' '}
                <span className="font-mono font-bold text-[#1c1b1b]">{ai?.llmModel || 'gemini-2.5-flash'}</span>
                {' '}via {ai?.llmProvider === 'gemini' ? 'Google Gemini' : 'OpenRouter'} based on the deterministic evidence above.
              </p>
            </div>
            <span className="font-mono text-[10px] font-bold bg-[#00E5BE] text-[#121212] px-3 py-1 border border-[#121212]">
              Validated Interpretation
            </span>
          </div>

          {/* Mandatory Faculty Disclaimer */}
          <div className="bg-[#FFF9E6] border-2 border-[#121212] p-4 flex items-start gap-3">
            <Shield size={18} className="text-[#1c1b1b] shrink-0 mt-0.5" />
            <div className="text-xs text-[#4b4731] leading-relaxed">
              <span className="font-bold text-[#1c1b1b] block mb-0.5 uppercase tracking-wide font-mono text-[11px]">
                Faculty Advisory Notice &amp; Evaluation Guardrails
              </span>
              This interpretation is generated by an LLM strictly as an analytical aid for faculty viva preparation. It does NOT constitute verified proof of academic misconduct or AI authorship. All factual claims must be independently verified by examining source code and questioning the student during defense.
            </div>
          </div>

          {/* Executive Summary */}
          <div className="bg-[#FAF6EE] border-2 border-[#121212] p-5">
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block mb-1">
              Executive Summary
            </span>
            <p className="font-sans text-sm text-[#1c1b1b] leading-relaxed">
              {interpretation.executive_summary || 'No executive summary provided.'}
            </p>
          </div>

          {/* Observed Patterns */}
          <div className="bg-[#FAF6EE] border-2 border-[#121212] p-5">
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] block mb-1">
              Observed Patterns Across Project Artifacts
            </span>
            <p className="font-sans text-sm text-[#1c1b1b] leading-relaxed whitespace-pre-line">
              {interpretation.explanation_of_patterns || 'No pattern explanation provided.'}
            </p>
          </div>

          {/* Fact vs Interpretation Breakdown */}
          <div>
            <h4 className="font-display font-bold text-base mb-3">Fact vs. Analytical Interpretation Separation</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {/* Column 1: Facts */}
              <div className="bg-[#EBF7F5] border-2 border-[#121212] p-4">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#006b58] flex items-center gap-1.5 mb-2">
                  <CheckCircle size={14} className="text-[#006b58]" />
                  Directly Supported Facts
                </span>
                <ul className="flex flex-col gap-2">
                  {list(interpretation.fact_vs_interpretation?.facts).map((fact, idx) => (
                    <li key={idx} className="font-sans text-xs text-[#1c1b1b] flex items-start gap-1.5">
                      <span className="w-1.5 h-1.5 bg-[#006b58] shrink-0 mt-1.5" />
                      <span>{fact}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Column 2: Interpretation */}
              <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#4b4731] flex items-center gap-1.5 mb-2">
                  <SlidersHorizontal size={14} className="text-[#4b4731]" />
                  Analytical Interpretations
                </span>
                <ul className="flex flex-col gap-2">
                  {list(interpretation.fact_vs_interpretation?.interpretation).map((interp, idx) => (
                    <li key={idx} className="font-sans text-xs text-[#1c1b1b] flex items-start gap-1.5">
                      <span className="w-1.5 h-1.5 bg-[#ffe600] border border-[#121212] shrink-0 mt-1.5" />
                      <span>{interp}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Column 3: Speculation / Unverified */}
              <div className="bg-[#FFF4D6] border-2 border-[#121212] p-4 md:col-span-2 lg:col-span-1">
                <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-[#b43b5b] flex items-center gap-1.5 mb-2">
                  <AlertTriangle size={14} className="text-[#b43b5b]" />
                  Speculation &amp; Unverified Hypotheses
                </span>
                <ul className="flex flex-col gap-2">
                  {list(interpretation.fact_vs_interpretation?.speculation).map((spec, idx) => (
                    <li key={idx} className="font-sans text-xs text-[#4b4731] flex items-start gap-1.5">
                      <span className="w-1.5 h-1.5 bg-[#FF5C8D] shrink-0 mt-1.5" />
                      <span>{spec}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Evidence References */}
          {interpretation.evidence_references && interpretation.evidence_references.length > 0 && (
            <div className="bg-white border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm mb-3">Direct Evidence References</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {interpretation.evidence_references.map((ref, idx) => (
                  <div key={idx} className="bg-[#FAF6EE] border border-[#121212] p-3 flex flex-col gap-1">
                    <span className="font-mono text-[10px] font-bold bg-white border border-[#121212] px-2 py-0.5 w-fit">
                      {ref.signal_id}
                    </span>
                    <p className="font-sans text-xs text-[#1c1b1b]">{ref.observation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Alternative Explanations & Faculty Follow-Up */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm mb-3 flex items-center gap-1.5">
                <Info size={15} className="text-[#006b58]" />
                Alternative Explanations (Benign Hypotheses)
              </h4>
              <ul className="flex flex-col gap-2">
                {list(interpretation.alternative_explanations).map((item, idx) => (
                  <li key={idx} className="font-sans text-xs text-[#4b4731] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-[#00E5BE] border border-[#121212] shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-white border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm mb-3 flex items-center gap-1.5">
                <CheckCircle size={15} className="text-[#006b58]" />
                Faculty Viva Follow-Up Recommendations
              </h4>
              <ul className="flex flex-col gap-2">
                {list(interpretation.faculty_follow_up_recommendations).map((item, idx) => (
                  <li key={idx} className="font-sans text-xs text-[#4b4731] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-[#ffe600] border border-[#121212] shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Limitations */}
          {((Array.isArray(ai?.limitations) && ai.limitations.length > 0) || (Array.isArray(interpretation.limitations) && interpretation.limitations.length > 0)) && (
            <div className="bg-[#FFF4D6] border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm mb-3 flex items-center gap-1.5">
                <AlertTriangle size={15} className="text-[#b43b5b]" />
                Limitations &amp; Incomplete Evidence
              </h4>
              <ul className="flex flex-col gap-2">
                {list([
                  ...(Array.isArray(ai?.limitations) ? ai.limitations : []),
                  ...(Array.isArray(interpretation.limitations) ? interpretation.limitations : []),
                ]).map((item, idx) => (
                  <li key={idx} className="font-sans text-xs text-[#4b4731] flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-[#FF5C8D] shrink-0 mt-1.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white border-[2.5px] border-[#121212] p-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="flex items-center justify-between pb-3 border-b-2 border-[#121212] mb-4">
            <h3 className="font-display font-bold text-lg flex items-center gap-2">
              <Sparkles size={18} />
              LLM Advisory Interpretation
            </h3>
            <span className={`font-mono text-[10px] font-bold px-2.5 py-1 border border-[#121212] ${ai?.llmInterpretationStatus === 'error'
              ? 'bg-[#FF5C8D] text-white'
              : 'bg-[#FAF6EE] text-[#4b4731]'
              }`}>
              {formatLLMStatus(ai?.llmInterpretationStatus).label}
            </span>
          </div>

          {ai?.llmInterpretationStatus === 'error' ? (
            <OpenRouterUnavailableBanner
              errorInfo={interpretation?.llm_error}
              limitations={ai?.limitations}
              onRetry={onAnalyze}
              analyzing={analyzing}
            />
          ) : ai?.llmInterpretationStatus === 'disabled' ? (
            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                LLM Interpretation Disabled
              </h4>
              <p className="font-sans text-xs text-[#4b4731] mt-1">
                LLM integration is disabled in system configuration (<span className="font-mono">LLM_ENABLED=false</span>). All deterministic evidence collection modules above remain fully operational and authoritative.
              </p>
            </div>
          ) : ai?.llmInterpretationStatus === 'insufficient_evidence' ? (
            <div className="bg-[#FFF9E6] border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                Insufficient Evidence for LLM Synthesis
              </h4>
              <p className="font-sans text-xs text-[#4b4731] mt-1">
                The project currently has insufficient upstream analysis signals to warrant an LLM narrative interpretation. Execute Code Quality, Similarity, and Git History analyses to provide evidence for synthesis.
              </p>
            </div>
          ) : (
            <div className="bg-[#FAF6EE] border-2 border-[#121212] p-5">
              <h4 className="font-display font-bold text-sm text-[#1c1b1b]">
                LLM Interpretation Not Yet Requested
              </h4>
              <p className="font-sans text-xs text-[#4b4731] mt-1">
                Click &quot;Run AI-Assistance Analysis&quot; above to collect deterministic evidence and generate advisory LLM synthesis.
              </p>
            </div>
          )}
        </div>
      )}

      {/* ── Section 6: Innovation & Architectural Distinctiveness Analyzer (Phase 7B) ── */}
      <ErrorBoundary sectionName="Innovation & Distinctiveness Analyzer">
        <InnovationSection
          innovation={inno}
          analyzing={innovAnalyzing}
          error={innovError}
          onAnalyze={onAnalyzeInnovation}
        />
      </ErrorBoundary>
    </div>
  );
}

const VIVA_MODES_DEF: Array<{
  id: VivaMode;
  label: string;
  icon: typeof Zap;
  desc: string;
  badge: string;
}> = [
  {
    id: 'quick_prep',
    label: 'Quick Preparation',
    icon: Zap,
    desc: 'High-probability core questions on fundamentals, architecture & tech stack.',
    badge: 'Fast Review',
  },
  {
    id: 'complete_viva',
    label: 'Complete Viva',
    icon: GraduationCap,
    desc: 'Comprehensive 9-category question set with balanced difficulty.',
    badge: 'Full Defense',
  },
  {
    id: 'technical_deep_dive',
    label: 'Technical Deep Dive',
    icon: Code2,
    desc: 'In-depth focus on code files, algorithms, database schema & APIs.',
    badge: 'Code Focus',
  },
  {
    id: 'examiner_challenge',
    label: 'Examiner Challenge',
    icon: Flame,
    desc: 'Tough questions on scalability, design bottlenecks & missing tests.',
    badge: 'Challenging',
  },
];

const VIVA_CATEGORIES_LIST = [
  'Project Fundamentals',
  'Technical Architecture',
  'Technology Stack',
  'Implementation and Coding',
  'Innovation and Uniqueness',
  'Testing and Validation',
  'Critical Thinking and Problem Solving',
  'Project-Specific Technical Deep Dive',
  'Future Scope and Improvements',
];

function VivaTab({
  project,
  analysis: _analysis,
}: {
  project: Project;
  analysis: ProjectAnalysis | null;
}) {
  const [questionSet, setQuestionSet] = useState<VivaQuestionSet | null>(null);
  const [progress, setProgress] = useState<VivaProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Generation controls
  const [selectedMode, setSelectedMode] = useState<VivaMode>('complete_viva');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedCount, setSelectedCount] = useState<number>(10);

  // Filters & answer reveals
  const [practiceFilter, setPracticeFilter] = useState<'all' | 'practiced' | 'unpracticed'>('all');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [expandedAnswers, setExpandedAnswers] = useState<Record<string, boolean>>({});

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [qs, prog] = await Promise.all([
        fetchVivaQuestions(project.id),
        fetchVivaProgress(project.id).catch(() => null),
      ]);
      setQuestionSet(qs);
      setProgress(prog);
    } catch (err: any) {
      console.warn('Could not load viva questions:', err);
    } finally {
      setLoading(false);
    }
  }, [project.id]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setError(null);
      const newSet = await generateVivaQuestions(project.id, {
        mode: selectedMode,
        difficulty: selectedDifficulty,
        questionCount: selectedCount,
        forceRegenerate: true,
      });
      setQuestionSet(newSet);
      const prog = await fetchVivaProgress(project.id).catch(() => null);
      setProgress(prog);
    } catch (err: any) {
      setError(err?.message || 'Failed to generate viva questions.');
    } finally {
      setGenerating(false);
    }
  };

  const handleTogglePractice = async (questionId: string, currentStatus: boolean) => {
    try {
      const updated = await updateVivaPracticeStatus(project.id, questionId, !currentStatus);
      if (questionSet) {
        setQuestionSet({
          ...questionSet,
          questions: questionSet.questions.map((q) => (q.id === questionId ? updated : q)),
          practicedCount: questionSet.questions.filter((q) =>
            q.id === questionId ? !currentStatus : q.isPracticed,
          ).length,
        });
      }
      const prog = await fetchVivaProgress(project.id).catch(() => null);
      setProgress(prog);
    } catch (err: any) {
      setError(err?.message || 'Failed to update practice status.');
    }
  };

  const handleRegenerateQuestion = async (questionId: string) => {
    try {
      setRegeneratingId(questionId);
      setError(null);
      const updated = await regenerateVivaQuestion(project.id, questionId);
      if (questionSet) {
        setQuestionSet({
          ...questionSet,
          questions: questionSet.questions.map((q) => (q.id === questionId ? updated : q)),
        });
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to regenerate question.');
    } finally {
      setRegeneratingId(null);
    }
  };

  const toggleAnswer = (questionId: string) => {
    setExpandedAnswers((prev) => ({ ...prev, [questionId]: !prev[questionId] }));
  };

  const toggleAllAnswers = () => {
    if (!questionSet) return;
    const allExpanded = questionSet.questions.every((q) => expandedAnswers[q.id]);
    const nextState: Record<string, boolean> = {};
    questionSet.questions.forEach((q) => {
      nextState[q.id] = !allExpanded;
    });
    setExpandedAnswers(nextState);
  };

  const getDifficultyBadge = (diff: string) => {
    switch ((diff || '').toLowerCase()) {
      case 'beginner':
        return { label: 'Beginner', bg: 'bg-[#EBF7F5] text-[#006b58] border-[#006b58]' };
      case 'advanced':
        return { label: 'Advanced', bg: 'bg-[#FFF0F5] text-[#b43b5b] border-[#b43b5b]' };
      case 'intermediate':
      default:
        return { label: 'Intermediate', bg: 'bg-[#FFF9E6] text-[#7a5c00] border-[#7a5c00]' };
    }
  };

  const questions: FullVivaQuestion[] = questionSet?.questions || [];
  const filteredQuestions = questions.filter((q) => {
    if (practiceFilter === 'practiced' && !q.isPracticed) return false;
    if (practiceFilter === 'unpracticed' && q.isPracticed) return false;
    if (categoryFilter !== 'all' && q.category !== categoryFilter) return false;
    return true;
  });

  const practicedCount = questions.filter((q) => q.isPracticed).length;
  const totalCount = questions.length;
  const progressPct = totalCount > 0 ? Math.round((practicedCount / totalCount) * 100) : 0;
  const allAnswersRevealed = questions.length > 0 && questions.every((q) => expandedAnswers[q.id]);

  if (loading && !questionSet) {
    return (
      <div className="bg-white border-[2.5px] border-[#121212] p-12 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <LoadingSpinner message="Loading Viva Preparation questions..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ── Top Generator Controls Card ── */}
      <div className="bg-white border-[2.5px] border-[#121212] p-6" style={{ boxShadow: '4px 4px 0px #121212' }}>
        <div className="flex flex-col md:flex-row md:items-start justify-between pb-4 border-b-2 border-[#121212] mb-5 gap-4">
          <div>
            <h2 className="font-display font-bold text-2xl text-[#1c1b1b] flex items-center gap-2">
              <GraduationCap size={26} className="text-[#1c1b1b]" />
              Intelligent Viva Preparation Suite
            </h2>
            <p className="font-sans text-sm text-[#4b4731] mt-1 leading-relaxed">
              Examiner-grade viva questions and suggested answers generated from actual project documentation, source code, architecture, and complexity metrics using Google Gemini AI.
            </p>
          </div>
          {questionSet && (
            <div className="flex items-center gap-2 shrink-0 self-start md:self-auto">
              <span className={`font-mono text-[10px] font-bold px-2.5 py-1 border border-[#121212] flex items-center gap-1 ${
                questionSet.generationSource === 'gemini'
                  ? 'bg-[#00E5BE] text-[#121212]'
                  : 'bg-[#FAF6EE] text-[#4b4731]'
              }`}>
                {questionSet.generationSource === 'gemini' ? (
                  <>
                    <Sparkles size={12} />
                    Gemini 2.5 Flash AI
                  </>
                ) : (
                  <>
                    <Shield size={12} />
                    Deterministic Fallback
                  </>
                )}
              </span>
            </div>
          )}
        </div>

        {error && (
          <div className="mb-5">
            <ErrorBanner message={error} />
          </div>
        )}

        {/* Mode Selector */}
        <div className="mb-5">
          <label className="font-mono text-[11px] font-bold uppercase tracking-wider text-[#4b4731] block mb-2">
            1. Select Viva Generation Mode:
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
            {VIVA_MODES_DEF.map((m) => {
              const Icon = m.icon;
              const isSelected = selectedMode === m.id;
              return (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMode(m.id)}
                  className={`p-3 border-2 border-[#121212] text-left transition-all cursor-pointer flex flex-col justify-between ${
                    isSelected
                      ? 'bg-[#ffe600] font-bold'
                      : 'bg-[#FAF6EE] hover:bg-white'
                  }`}
                  style={{ boxShadow: isSelected ? '3px 3px 0px #121212' : '1px 1px 0px #121212' }}
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-1">
                      <div className="flex items-center gap-1.5 font-display text-sm font-bold text-[#1c1b1b]">
                        <Icon size={16} />
                        {m.label}
                      </div>
                      <span className="font-mono text-[9px] uppercase px-1.5 py-0.5 border border-[#121212] bg-white text-[#1c1b1b]">
                        {m.badge}
                      </span>
                    </div>
                    <p className="font-sans text-[11px] text-[#4b4731] leading-tight">
                      {m.desc}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Difficulty & Count Options */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t-2 border-[#121212]">
          <div className="flex flex-wrap items-center gap-4">
            {/* Target Difficulty */}
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] font-bold text-[#4b4731] uppercase">Difficulty:</span>
              <div className="flex items-center gap-1">
                {['all', 'beginner', 'intermediate', 'advanced'].map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setSelectedDifficulty(d)}
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] uppercase transition-colors cursor-pointer ${
                      selectedDifficulty === d
                        ? 'bg-[#121212] text-white'
                        : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-white'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {/* Question Count */}
            <div className="flex items-center gap-2">
              <span className="font-mono text-[11px] font-bold text-[#4b4731] uppercase">Questions:</span>
              <div className="flex items-center gap-1">
                {[5, 10, 15, 20].map((cnt) => (
                  <button
                    key={cnt}
                    type="button"
                    onClick={() => setSelectedCount(cnt)}
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] transition-colors cursor-pointer ${
                      selectedCount === cnt
                        ? 'bg-[#121212] text-white'
                        : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-white'
                    }`}
                  >
                    {cnt}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Action Button */}
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            <RefreshCw size={14} className={generating ? 'animate-spin' : ''} />
            {generating
              ? 'Generating Viva Questions with Gemini...'
              : questionSet
                ? 'Regenerate All Questions'
                : 'Generate Viva Questions'}
          </button>
        </div>
      </div>

      {/* ── Practice Progress & Filter Ribbon ── */}
      {questionSet && (
        <div className="bg-white border-[2.5px] border-[#121212] p-5" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b-2 border-[#121212] mb-4">
            <div>
              <span className="font-mono text-[10px] font-bold uppercase tracking-wider text-[#4b4731] block mb-0.5">
                Practice &amp; Preparation Progress
              </span>
              <div className="font-display font-bold text-lg text-[#1c1b1b] flex items-center gap-2">
                <span>{practicedCount} of {totalCount} Questions Practiced</span>
                <span className="font-mono text-sm text-[#006b58] font-bold">({progressPct}%)</span>
              </div>
              {progress?.byDifficulty && (
                <div className="flex items-center gap-2 mt-1.5 flex-wrap">
                  <span className="font-mono text-[9px] uppercase font-bold text-[#4b4731]">Mastery:</span>
                  {Object.entries(progress.byDifficulty).map(([d, stat]) => (
                    <span key={d} className="font-mono text-[9px] bg-[#FAF6EE] border border-[#121212] px-1.5 py-0.5 text-[#1c1b1b]">
                      {d}: {stat.practiced}/{stat.total}
                    </span>
                  ))}
                </div>
              )}
            </div>
            <button
              type="button"
              onClick={toggleAllAnswers}
              className="font-mono text-[11px] font-bold px-3 py-1 bg-[#FAF6EE] border border-[#121212] hover:bg-[#eae4d5] transition-colors flex items-center gap-1.5 self-start sm:self-auto cursor-pointer"
            >
              {allAnswersRevealed ? <EyeOff size={13} /> : <Eye size={13} />}
              {allAnswersRevealed ? 'Hide All Answers' : 'Reveal All Answers'}
            </button>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-[#FAF6EE] border border-[#121212] h-3.5 mb-4 p-0.5">
            <div
              className="bg-[#00E5BE] h-full transition-all duration-300"
              style={{ width: `${progressPct}%` }}
            />
          </div>

          {/* Filters Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            {/* Practiced Filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="font-mono text-[10px] uppercase font-bold text-[#4b4731] mr-1">Status:</span>
              {[
                { id: 'all', label: `All (${totalCount})` },
                { id: 'unpracticed', label: `To Practice (${totalCount - practicedCount})` },
                { id: 'practiced', label: `Practiced (${practicedCount})` },
              ].map((f) => (
                <button
                  key={f.id}
                  type="button"
                  onClick={() => setPracticeFilter(f.id as any)}
                  className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] transition-colors cursor-pointer ${
                    practiceFilter === f.id
                      ? 'bg-[#121212] text-white'
                      : 'bg-[#FAF6EE] text-[#1c1b1b] hover:bg-white'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>

            {/* Category Select Filter */}
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[10px] uppercase font-bold text-[#4b4731]">Category:</span>
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="font-mono text-[10px] font-bold bg-[#FAF6EE] border border-[#121212] px-2 py-1 outline-none cursor-pointer"
              >
                <option value="all">All Categories</option>
                {VIVA_CATEGORIES_LIST.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* ── Question Cards List ── */}
      {questionSet && filteredQuestions.length > 0 && (
        <div className="flex flex-col gap-4">
          {filteredQuestions.map((q, idx) => {
            const diffStyle = getDifficultyBadge(q.difficulty);
            const isAnswerVisible = expandedAnswers[q.id] || false;
            const isRegenerating = regeneratingId === q.id;

            return (
              <div
                key={q.id}
                className={`bg-white border-2 border-[#121212] p-5 flex flex-col gap-3 transition-all ${
                  q.isPracticed ? 'border-l-8 border-l-[#00E5BE]' : ''
                }`}
                style={{ boxShadow: '3px 3px 0px #121212' }}
              >
                {/* Card Top Ribbon */}
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#121212] pb-2.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-[11px] font-bold bg-[#121212] text-white px-2 py-0.5">
                      Q{idx + 1}
                    </span>
                    <span className="font-mono text-[10px] font-bold uppercase bg-[#FAF6EE] border border-[#121212] px-2 py-0.5 text-[#1c1b1b]">
                      {q.category}
                    </span>
                    <span className={`font-mono text-[9px] font-bold uppercase px-2 py-0.5 border ${diffStyle.bg}`}>
                      {diffStyle.label}
                    </span>
                    {q.source === 'gemini' ? (
                      <span className="font-mono text-[9px] font-bold bg-[#00E5BE] text-[#121212] border border-[#121212] px-1.5 py-0.5 flex items-center gap-1">
                        <Sparkles size={10} />
                        Gemini AI
                      </span>
                    ) : (
                      <span className="font-mono text-[9px] font-bold bg-[#FAF6EE] text-[#4b4731] border border-[#121212] px-1.5 py-0.5">
                        Deterministic Fallback
                      </span>
                    )}
                  </div>

                  {/* Practiced check indicator */}
                  <button
                    type="button"
                    onClick={() => handleTogglePractice(q.id, q.isPracticed)}
                    className={`font-mono text-[10px] font-bold px-2 py-0.5 border border-[#121212] flex items-center gap-1 cursor-pointer transition-colors ${
                      q.isPracticed
                        ? 'bg-[#00E5BE] text-[#121212]'
                        : 'bg-[#FAF6EE] text-[#4b4731] hover:bg-white'
                    }`}
                  >
                    {q.isPracticed ? <CheckSquare size={12} /> : <Square size={12} />}
                    {q.isPracticed ? 'Practiced' : 'Mark Practiced'}
                  </button>
                </div>

                {/* Question Text */}
                <h3 className="font-display font-bold text-base text-[#1c1b1b] leading-snug">
                  {q.question}
                </h3>

                {/* Examiner Rationale Box */}
                <div className="bg-[#FFF9E6] border-l-4 border-[#ffe600] p-2.5 text-xs text-[#4b4731]">
                  <strong className="font-mono text-[10px] font-bold text-[#1c1b1b] uppercase block mb-0.5">
                    Why an Examiner Asks This:
                  </strong>
                  {q.examinerRationale}
                </div>

                {/* Evidence Reference */}
                {q.evidenceReference && (
                  <div className="font-mono text-[10px] text-[#4b4731] flex items-center gap-1">
                    <span className="font-bold text-[#1c1b1b] uppercase">Evidence Basis:</span>
                    <span className="bg-[#FAF6EE] border border-[#121212] px-1.5 py-0.5">
                      {q.evidenceReference}
                    </span>
                  </div>
                )}

                {/* Suggested Answer Accordion */}
                <div className="mt-1">
                  <button
                    type="button"
                    onClick={() => toggleAnswer(q.id)}
                    className="font-mono text-[11px] font-bold text-[#006b58] hover:underline flex items-center gap-1.5 cursor-pointer py-1"
                  >
                    {isAnswerVisible ? <EyeOff size={14} /> : <Eye size={14} />}
                    {isAnswerVisible ? 'Hide Suggested Answer' : 'Show Suggested Answer & Key Points'}
                  </button>

                  {isAnswerVisible && (
                    <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4 mt-2 flex flex-col gap-3">
                      {/* Expected Key Points */}
                      {q.keyPoints && q.keyPoints.length > 0 && (
                        <div>
                          <strong className="font-mono text-[10px] uppercase font-bold text-[#006b58] block mb-1.5">
                            Key Points Expected in a Strong Viva Answer:
                          </strong>
                          <ul className="list-disc list-inside space-y-1 text-xs text-[#1c1b1b]">
                            {q.keyPoints.map((pt, i) => (
                              <li key={i}>{pt}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Full Suggested Answer */}
                      <div>
                        <strong className="font-mono text-[10px] uppercase font-bold text-[#1c1b1b] block mb-1">
                          Comprehensive Suggested Answer:
                        </strong>
                        <p className="font-sans text-xs text-[#1c1b1b] leading-relaxed whitespace-pre-line bg-white border border-[#121212] p-3">
                          {q.suggestedAnswer}
                        </p>
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Footer Actions */}
                <div className="flex items-center justify-between pt-2 border-t border-[#121212]/30 text-xs">
                  <span className="font-mono text-[9px] text-[#7c775f]">
                    ID: {q.id}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleRegenerateQuestion(q.id)}
                    disabled={isRegenerating}
                    className="font-mono text-[10px] font-bold text-[#4b4731] hover:text-[#1c1b1b] flex items-center gap-1 cursor-pointer disabled:opacity-50"
                  >
                    <RefreshCw size={11} className={isRegenerating ? 'animate-spin' : ''} />
                    {isRegenerating ? 'Regenerating...' : 'Regenerate This Question'}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Empty State ── */}
      {!loading && (!questionSet || questions.length === 0) && (
        <div className="bg-white border-[2.5px] border-[#121212] p-10 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <div className="w-16 h-16 bg-[#ffe600] border-2 border-[#121212] flex items-center justify-center mx-auto mb-4" style={{ boxShadow: '3px 3px 0px #121212' }}>
            <GraduationCap size={32} className="text-[#121212]" />
          </div>
          <h3 className="font-display font-bold text-xl text-[#1c1b1b] mb-2">
            No Viva Questions Generated Yet
          </h3>
          <p className="font-sans text-sm text-[#4b4731] max-w-xl mx-auto mb-6 leading-relaxed">
            ProjectLens can analyze this project's code files, complexity hotspots, documentation claims, and technology stack to generate personalized examiner viva defense questions with complete suggested answers using Google Gemini AI.
          </p>
          <button
            type="button"
            onClick={handleGenerate}
            disabled={generating}
            className="btn-primary inline-flex items-center gap-2 cursor-pointer disabled:opacity-50 text-sm py-2.5 px-6"
          >
            <Sparkles size={16} />
            {generating ? 'Generating Viva Questions...' : 'Generate Viva Questions Now'}
          </button>
        </div>
      )}

      {/* ── No matches for current filter ── */}
      {questionSet && questions.length > 0 && filteredQuestions.length === 0 && (
        <div className="bg-white border-[2.5px] border-[#121212] p-8 text-center" style={{ boxShadow: '4px 4px 0px #121212' }}>
          <p className="font-sans text-sm text-[#4b4731] mb-2">
            No questions match the current status or category filter.
          </p>
          <button
            type="button"
            onClick={() => {
              setPracticeFilter('all');
              setCategoryFilter('all');
            }}
            className="font-mono text-xs font-bold text-[#006b58] underline cursor-pointer"
          >
            Reset Filters
          </button>
        </div>
      )}
    </div>
  );
}

function ReportTab({
  project,
  analysis,
  onDownload,
  onRequestReport,
  onExportJson,
  reportLoading,
  reportError,
}: {
  project: Project;
  analysis: ProjectAnalysis | null;
  onDownload: () => void;
  onRequestReport: () => void;
  onExportJson?: () => void;
  reportLoading: boolean;
  reportError: string | null;
}) {
  const report = analysis?.evaluationReport;
  const evaluation = report?.evaluation;
  const categories = evaluation?.category_scores || [];
  const strengths = evaluation?.strengths || [];
  const weaknesses = evaluation?.weaknesses || [];
  const risks = evaluation?.risks || [];
  const recommendations = evaluation?.recommendations || [];

  const statusLabel =
    evaluation?.evaluation_status === 'complete'
      ? 'Complete Evaluation'
      : evaluation?.evaluation_status === 'provisional' || evaluation?.evaluation_status === 'partial'
      ? 'Provisional Evaluation'
      : evaluation?.evaluation_status === 'insufficient_evidence'
      ? 'Insufficient Evidence'
      : 'Evaluation Ready';

  return (
    <div className="flex flex-col gap-6">
      {/* ── 1. Top Executive Evaluation Scorecard ── */}
      <div
        className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div className="bg-[#ffe600] border-b-2 border-[#121212] px-5 py-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Award size={20} className="text-[#1c1b1b]" />
            <span className="font-display font-bold uppercase tracking-wide text-sm">
              Overall Project Evaluation &amp; Formal Report
            </span>
          </div>
          <div className="flex items-center gap-2">
            {report?.grade && (
              <span
                className="font-mono text-xs font-bold bg-white px-2.5 py-1 border-2 border-[#121212]"
                style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
              >
                GRADE {report.grade}
              </span>
            )}
            {evaluation?.coverage_pct !== undefined && (
              <span
                className="font-mono text-xs font-bold bg-[#EBF7F5] text-[#006b58] px-2.5 py-1 border-2 border-[#121212]"
                style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
              >
                {Math.round(evaluation.coverage_pct)}% COVERAGE
              </span>
            )}
          </div>
        </div>

        <div className="p-6 md:p-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center">
            {/* Score & Grade Display */}
            <div className="lg:col-span-5 flex flex-col justify-center">
              <span className="font-mono text-xs uppercase tracking-wider text-[#4b4731] font-bold mb-1">
                Consolidated Faculty Evaluation
              </span>
              <div className="flex items-baseline gap-2">
                <span className="font-display font-black text-6xl md:text-7xl text-[#1c1b1b] tracking-tight">
                  {report?.overallScore !== undefined ? report.overallScore : project.score ?? '—'}
                </span>
                <span className="font-display font-bold text-2xl text-[#4b4731]">/100</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-2">
                <span
                  className="font-mono text-xs font-bold uppercase px-2 py-0.5 border border-[#121212]"
                  style={{
                    backgroundColor:
                      evaluation?.evaluation_status === 'complete'
                        ? '#00E5BE'
                        : '#FFE600',
                  }}
                >
                  {statusLabel}
                </span>
                <span className="font-mono text-xs text-[#4b4731]">
                  Rubric v1.0 • 6 Core Categories
                </span>
              </div>
            </div>

            {/* Quick Actions Panel */}
            <div className="lg:col-span-7 flex flex-col sm:flex-row flex-wrap gap-3 items-stretch sm:items-center justify-end">
              <button
                className="btn-primary flex items-center justify-center gap-2 py-3 px-5 text-sm cursor-pointer disabled:opacity-50"
                onClick={onRequestReport}
                disabled={reportLoading}
              >
                {reportLoading ? (
                  <span
                    className="w-4 h-4 border-2 border-[#121212] border-t-transparent animate-spin inline-block"
                    style={{ borderRadius: '50%' }}
                  />
                ) : (
                  <RefreshCw size={17} />
                )}
                {report?.reportAvailable ? 'Re-Evaluate Project' : 'Run Overall Evaluation'}
              </button>

              <button
                className="btn-secondary flex items-center justify-center gap-2 py-3 px-5 text-sm cursor-pointer disabled:opacity-50 bg-[#00E5BE] hover:bg-[#00c9a7]"
                onClick={onDownload}
                disabled={!report?.reportAvailable || reportLoading}
              >
                {reportLoading ? (
                  <span
                    className="w-4 h-4 border-2 border-[#121212] border-t-transparent animate-spin inline-block"
                    style={{ borderRadius: '50%' }}
                  />
                ) : (
                  <Download size={17} />
                )}
                Download Formal PDF Report
              </button>

              {onExportJson && (
                <button
                  className="btn-secondary flex items-center justify-center gap-2 py-3 px-4 text-xs font-mono cursor-pointer disabled:opacity-50"
                  onClick={onExportJson}
                  disabled={!report?.reportAvailable || reportLoading}
                  title="Export raw JSON evaluation data"
                >
                  <FileCode size={15} />
                  JSON
                </button>
              )}
            </div>
          </div>

          {reportError && (
            <div className="mt-6">
              <ErrorBanner message={reportError} />
            </div>
          )}

          {/* Executive Summary */}
          {evaluation?.executive_summary && (
            <div className="mt-6 p-4 bg-[#FAF6EE] border-2 border-[#121212]">
              <div className="flex items-center gap-2 mb-1.5 font-bold text-xs uppercase font-mono text-[#1c1b1b]">
                <FileText size={15} />
                <span>Executive Evaluation Summary</span>
              </div>
              <p className="font-sans text-sm text-[#3a3726] leading-relaxed">
                {evaluation.executive_summary}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── 2. Category-Wise Rubric Breakdown ── */}
      <div
        className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div className="bg-[#121212] text-white px-5 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <SlidersHorizontal size={18} className="text-[#ffe600]" />
            <span className="font-display font-bold uppercase tracking-wide text-sm">
              Multi-Dimensional Evaluation Breakdown
            </span>
          </div>
          <span className="font-mono text-xs text-[#d8d5ca]">
            Normalized Weighting (100% Total)
          </span>
        </div>

        <div className="p-6">
          {categories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {categories.map((cat, idx) => {
                const name = cat.name || cat.title || cat.id || `Category ${idx + 1}`;
                const rawScore = cat.score ?? cat.raw_score;
                const weight = cat.weight ?? 0;
                const contrib = cat.contribution ?? cat.weighted_score ?? 0;
                const isAssessed = cat.status === 'assessed';

                return (
                  <div
                    key={cat.id || idx}
                    className="p-4 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col justify-between"
                    style={{ boxShadow: '2px 2px 0px #121212' }}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-2">
                        <span className="font-display font-bold text-sm text-[#1c1b1b]">
                          {name}
                        </span>
                        <span
                          className="font-mono text-[10px] font-bold uppercase px-1.5 py-0.5 border border-[#121212]"
                          style={{
                            backgroundColor: isAssessed ? '#00E5BE' : '#FFF4D6',
                          }}
                        >
                          {cat.status}
                        </span>
                      </div>

                      <div className="flex items-baseline justify-between mb-1.5">
                        <span className="font-mono text-xs text-[#4b4731]">
                          Weight: <b>{weight}%</b>
                        </span>
                        <span className="font-display font-bold text-lg text-[#1c1b1b]">
                          {rawScore !== null && rawScore !== undefined ? `${rawScore}` : 'N/A'}
                          <span className="text-xs text-[#4b4731] font-mono"> / 100</span>
                        </span>
                      </div>

                      {/* Progress Bar */}
                      <div className="h-3 w-full bg-white border border-[#121212] overflow-hidden mb-2">
                        <div
                          className="h-full bg-[#ffe600] border-r border-[#121212] transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(0, rawScore || 0))}%` }}
                        />
                      </div>
                    </div>

                    <div className="mt-2 pt-2 border-t border-[#121212] flex items-center justify-between text-[11px] font-mono">
                      <span className="text-[#4b4731]">Contribution:</span>
                      <span className="font-bold text-[#1c1b1b]">{contrib.toFixed(1)} pts</span>
                    </div>

                    {cat.reason && (
                      <p className="mt-2 text-[11px] text-[#4b4731] font-mono leading-tight">
                        {cat.reason}
                      </p>
                    )}
                  </div>
                );
              })}
            </div>
          ) : report?.scoreBreakdown && report.scoreBreakdown.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {report.scoreBreakdown.map((s) => (
                <div
                  key={s.dimension}
                  className="p-3 bg-[#FAF6EE] border-2 border-[#121212] flex flex-col justify-between"
                  style={{ boxShadow: '2px 2px 0px #121212' }}
                >
                  <div className="flex justify-between items-center mb-1">
                    <span className="font-display font-bold text-sm">{s.dimension}</span>
                    <span className="font-mono font-bold text-sm">
                      {s.score} / {s.maxScore}
                    </span>
                  </div>
                  {s.notes && (
                    <span className="font-mono text-[10px] text-[#4b4731]">{s.notes}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center">
              <p className="font-mono text-sm text-[#4b4731]">
                No category breakdown available yet. Run the overall evaluation above.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── 3. Tri-Pillar Synthesis: Strengths, Weaknesses, Viva Risks ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Identified Strengths */}
        <div
          className="bg-white border-[2.5px] border-[#121212] flex flex-col"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="bg-[#00E5BE] border-b-2 border-[#121212] px-4 py-2.5 flex items-center gap-2">
            <CheckCircle size={17} className="text-[#121212]" />
            <span className="font-display font-bold text-xs uppercase tracking-wide">
              Identified Strengths ({strengths.length})
            </span>
          </div>
          <div className="p-4 flex-1">
            {strengths.length > 0 ? (
              <ul className="space-y-2">
                {strengths.map((str, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-xs text-[#1c1b1b] font-sans leading-relaxed"
                  >
                    <span className="text-[#008970] font-bold font-mono mt-0.5">✓</span>
                    <span>{str}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#4b4731] font-mono italic">
                No distinct strengths logged for this evaluation.
              </p>
            )}
          </div>
        </div>

        {/* Technical Weaknesses */}
        <div
          className="bg-white border-[2.5px] border-[#121212] flex flex-col"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="bg-[#FFE600] border-b-2 border-[#121212] px-4 py-2.5 flex items-center gap-2">
            <AlertTriangle size={17} className="text-[#121212]" />
            <span className="font-display font-bold text-xs uppercase tracking-wide">
              Areas for Improvement ({weaknesses.length})
            </span>
          </div>
          <div className="p-4 flex-1">
            {weaknesses.length > 0 ? (
              <ul className="space-y-2">
                {weaknesses.map((w, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-xs text-[#1c1b1b] font-sans leading-relaxed"
                  >
                    <span className="text-[#b43b5b] font-bold font-mono mt-0.5">•</span>
                    <span>{w}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#4b4731] font-mono italic">
                No major weaknesses identified.
              </p>
            )}
          </div>
        </div>

        {/* Viva Defense & Integrity Risks */}
        <div
          className="bg-white border-[2.5px] border-[#121212] flex flex-col"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="bg-[#FF5C8D] text-white border-b-2 border-[#121212] px-4 py-2.5 flex items-center gap-2">
            <ShieldAlert size={17} className="text-[#121212]" />
            <span className="font-display font-bold text-xs uppercase tracking-wide text-[#121212]">
              Viva Defense Risks ({risks.length})
            </span>
          </div>
          <div className="p-4 flex-1">
            {risks.length > 0 ? (
              <ul className="space-y-2">
                {risks.map((r, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-xs text-[#1c1b1b] font-sans leading-relaxed"
                  >
                    <span className="text-[#FF5C8D] font-bold font-mono mt-0.5">!</span>
                    <span>{r}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-xs text-[#4b4731] font-mono italic">
                No high-priority defense risks flagged.
              </p>
            )}
          </div>
        </div>
      </div>

      {/* ── 4. Prioritized Action Plan & Recommendations ── */}
      {recommendations.length > 0 && (
        <div
          className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="bg-[#FAF6EE] border-b-2 border-[#121212] px-5 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap size={18} className="text-[#1c1b1b]" />
              <span className="font-display font-bold uppercase tracking-wide text-sm">
                Prioritized Action Plan ({recommendations.length} Recommendations)
              </span>
            </div>
            <span className="font-mono text-xs text-[#4b4731]">
              Ranked by Evaluator Priority
            </span>
          </div>

          <div className="p-6 divide-y-2 divide-[#121212]">
            {recommendations.map((rec, idx) => {
              const priority = rec.priority || 'Medium';
              const isCritical = priority === 'Critical' || priority === 'Immediate';
              const isHigh = priority === 'High' || priority === 'Important';

              return (
                <div key={idx} className={`py-4 ${idx === 0 ? 'pt-0' : ''}`}>
                  <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2">
                      <span
                        className="font-mono text-[10px] font-bold uppercase px-2 py-0.5 border border-[#121212]"
                        style={{
                          backgroundColor: isCritical
                            ? '#FF5C8D'
                            : isHigh
                            ? '#FFE600'
                            : '#D8B4FE',
                          color: '#121212',
                        }}
                      >
                        {priority}
                      </span>
                      <span className="font-display font-bold text-sm text-[#1c1b1b]">
                        {rec.title || rec.action}
                      </span>
                    </div>
                    {(rec.sourceModule || rec.target_area) && (
                      <span className="font-mono text-[10px] bg-[#FAF6EE] border border-[#121212] px-2 py-0.5">
                        {rec.sourceModule || rec.target_area}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-[#3a3726] font-sans leading-relaxed mb-2">
                    {rec.description || rec.rationale}
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
                    {(rec.recommendedAction || rec.action) && (
                      <div className="p-2.5 bg-[#FAF6EE] border border-[#121212] text-xs">
                        <span className="font-mono font-bold text-[10px] uppercase block mb-1 text-[#1c1b1b]">
                          Action:
                        </span>
                        <span className="text-[#4b4731]">{rec.recommendedAction || rec.action}</span>
                      </div>
                    )}
                    {(rec.expectedBenefit || rec.whyItMatters) && (
                      <div className="p-2.5 bg-[#EBF7F5] border border-[#121212] text-xs">
                        <span className="font-mono font-bold text-[10px] uppercase block mb-1 text-[#006b58]">
                          Expected Benefit:
                        </span>
                        <span className="text-[#006b58]">{rec.expectedBenefit || rec.whyItMatters}</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── 5. Academic Disclaimer & Advisory Notice ── */}
      <div className="bg-[#FAF6EE] border-2 border-[#121212] p-4 text-xs text-[#4b4731] leading-relaxed">
        <div className="flex items-center gap-2 mb-1 text-[#1c1b1b] font-bold font-mono uppercase text-[11px]">
          <Shield size={14} />
          <span>Academic Evaluation Standard &amp; Faculty Notice</span>
        </div>
        <p>
          ProjectLens provides deterministic screening signals, evidence extraction, and
          rubric-weighted scores to assist evaluation panels. These metrics serve as an advisory
          foundation to guide oral examination (viva voce). Final scoring, grading, and academic
          integrity decisions remain the sole prerogative of faculty evaluators.
        </p>
      </div>
    </div>
  );
}

// ─── Project Workspace Page ───────────────────────────────────────────────────
export default function ProjectWorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>();
  const [activeTab, setActiveTab] = useState<TabId>('overview');

  const [project, setProject] = useState<Project | null>(null);
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null);
  const [structure, setStructure] = useState<ProjectStructure | null>(null);
  const [codeQuality, setCodeQuality] = useState<CodeQualityResponse | null>(null);
  const [similarity, setSimilarity] = useState<ProjectSimilarityResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [cqLoading, setCqLoading] = useState(false);
  const [cqAnalyzing, setCqAnalyzing] = useState(false);
  const [cqError, setCqError] = useState<string | null>(null);

  const [simLoading, setSimLoading] = useState(false);
  const [simAnalyzing, setSimAnalyzing] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  const [documentation, setDocumentation] = useState<DocumentationResponse | null>(null);
  const [docLoading, setDocLoading] = useState(false);
  const [docAnalyzing, setDocAnalyzing] = useState(false);
  const [docError, setDocError] = useState<string | null>(null);

  const [gitHistory, setGitHistory] = useState<GitHistoryResponse | null>(null);
  const [gitLoading, setGitLoading] = useState(false);
  const [gitAnalyzing, setGitAnalyzing] = useState(false);
  const [gitError, setGitError] = useState<string | null>(null);

  const [aiAssistance, setAiAssistance] = useState<AIAssistanceResult | null>(null);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const [innovation, setInnovation] = useState<InnovationAnalysisResponse | null>(null);
  const [innovAnalyzing, setInnovAnalyzing] = useState(false);
  const [innovError, setInnovError] = useState<string | null>(null);

  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setCqLoading(true);
    setSimLoading(true);
    setDocLoading(true);
    setGitLoading(true);
    setError(null);
    try {
      const [proj, anal, struct, cq, sim, doc, git, aiRes, innovRes] = await Promise.all([
        fetchProject(projectId),
        fetchAnalysis(projectId).catch(() => null),
        fetchProjectStructure(projectId).catch(() => null),
        fetchCodeQuality(projectId).catch(() => null),
        fetchSimilarity(projectId).catch(() => null),
        fetchDocumentation(projectId).catch(() => null),
        fetchDevelopmentHistory(projectId).catch(() => null),
        fetchAIAssistance(projectId).catch(() => null),
        fetchInnovationAnalysis(projectId).catch(() => null),
      ]);
      setProject(proj);
      setAnalysis(anal);
      setStructure(struct);
      setCodeQuality(cq);
      setSimilarity(sim);
      setDocumentation(doc);
      setGitHistory(git);
      setAiAssistance(anal?.aiAssistance ?? aiRes ?? null);
      setInnovation(anal?.innovation ?? innovRes ?? null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load project.');
    } finally {
      setLoading(false);
      setCqLoading(false);
      setSimLoading(false);
      setDocLoading(false);
      setGitLoading(false);
    }
  }, [projectId]);

  useEffect(() => { load(); }, [load]);

  // Poll while processing
  useEffect(() => {
    if (!project || project.status !== 'processing') return;
    const id = setInterval(load, 10_000);
    return () => clearInterval(id);
  }, [project, load]);

  async function handleReparse() {
    if (!projectId) return;
    setParsing(true);
    try {
      const updated = await reparseProject(projectId);
      setStructure(updated);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to parse project structure.');
    } finally {
      setParsing(false);
    }
  }

  async function handleAnalyzeCodeQuality() {
    if (!projectId) return;
    setCqAnalyzing(true);
    setCqError(null);
    try {
      const res = await triggerCodeQualityAnalysis(projectId);
      setCodeQuality(res);
      await load();
    } catch (err) {
      setCqError(err instanceof Error ? err.message : 'Failed to analyze code quality.');
    } finally {
      setCqAnalyzing(false);
    }
  }

  async function handleAnalyzeSimilarity() {
    if (!projectId) return;
    setSimAnalyzing(true);
    setSimError(null);
    try {
      const res = await triggerSimilarityAnalysis(projectId);
      setSimilarity(res);
      await load();
    } catch (err) {
      setSimError(err instanceof Error ? err.message : 'Failed to analyze code similarity.');
    } finally {
      setSimAnalyzing(false);
    }
  }

  async function handleAnalyzeDocumentation() {
    if (!projectId) return;
    setDocAnalyzing(true);
    setDocError(null);
    try {
      const res = await triggerDocumentationAnalysis(projectId);
      setDocumentation(res);
      await load();
    } catch (err) {
      setDocError(err instanceof Error ? err.message : 'Failed to analyze documentation.');
    } finally {
      setDocAnalyzing(false);
    }
  }

  async function handleAnalyzeGitHistory() {
    if (!projectId) return;
    setGitAnalyzing(true);
    setGitError(null);
    try {
      const res = await triggerDevelopmentHistoryAnalysis(projectId);
      setGitHistory(res);
      await load();
    } catch (err) {
      setGitError(err instanceof Error ? err.message : 'Failed to analyze Git development history.');
    } finally {
      setGitAnalyzing(false);
    }
  }

  async function handleAnalyzeAIAssistance() {
    if (!projectId) return;
    setAiAnalyzing(true);
    setAiError(null);
    try {
      const result = await triggerAIAssistance(projectId);
      setAiAssistance(result);
      setAnalysis((current) => current ? { ...current, aiAssistance: result } : current);
    } catch (err) {
      setAiError(err instanceof Error ? err.message : 'Failed to run AI-assistance analysis.');
    } finally {
      setAiAnalyzing(false);
    }
  }

  async function handleAnalyzeInnovation() {
    if (!projectId) return;
    setInnovAnalyzing(true);
    setInnovError(null);
    try {
      const result = await triggerInnovationAnalysis(projectId);
      setInnovation(result);
      setAnalysis((current) => current ? { ...current, innovation: result } : current);
    } catch (err) {
      setInnovError(err instanceof Error ? err.message : 'Failed to run innovation analysis.');
    } finally {
      setInnovAnalyzing(false);
    }
  }

  async function handleDownload() {
    if (!projectId || !project) return;
    setReportLoading(true);
    setReportError(null);
    try {
      await downloadReport(projectId, `${project.title || projectId}_report.pdf`);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Download failed.');
    } finally {
      setReportLoading(false);
    }
  }

  async function handleRequestReport() {
    if (!projectId) return;
    setReportLoading(true);
    setReportError(null);
    try {
      await triggerEvaluation(projectId);
      await load();
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Failed to request report.');
    } finally {
      setReportLoading(false);
    }
  }

  async function handleDownloadJson() {
    if (!projectId || !project) return;
    setReportLoading(true);
    setReportError(null);
    try {
      await downloadEvaluationJson(projectId, `${project.title || projectId}_evaluation.json`);
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'JSON export failed.');
    } finally {
      setReportLoading(false);
    }
  }

  if (loading) return (
    <div className="max-w-[1280px] mx-auto px-5 md:px-10 py-10">
      <LoadingSpinner message="Loading project workspace..." />
    </div>
  );

  if (error || !project) return (
    <div className="max-w-[1280px] mx-auto px-5 md:px-10 py-10">
      <ErrorBanner
        title="Failed to load project"
        message={error ?? 'Project not found.'}
        onRetry={load}
      />
    </div>
  );

  const simPct = analysis?.similarity?.overallSimilarity;
  const vqCount = analysis?.vivaQuestions?.length;

  return (
    <div className="max-w-[1280px] w-full mx-auto px-5 md:px-10 pb-16 space-y-6">
      {/* ── Project header ── */}
      <section className="mt-6 flex flex-col lg:flex-row gap-6 items-stretch">

        {/* Left: project info */}
        <div
          className="flex-1 bg-white border-[2.5px] border-[#121212] p-6 flex flex-col justify-between"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <span className="font-mono text-[11px] bg-[#F2ECE1] px-2 py-1 border-[1.5px] border-[#121212] uppercase">
                  ID: {project.id}
                </span>
                <StatusBadge status={project.status} stage={project.processingStage} />
              </div>
              <span className="font-mono text-[11px] text-[#4b4731] flex items-center gap-1">
                <Clock size={13} />
                {formatDate(project.updatedAt)}
              </span>
            </div>

            <h1 className="font-display font-bold text-3xl md:text-4xl text-[#1c1b1b] tracking-tight mb-3">
              {project.title || project.id}
            </h1>

            <div className="flex flex-wrap items-center gap-2">
              {project.course && (
                <span className="font-mono text-[11px] font-bold bg-[#ffe600] text-[#1c1b1b] px-2 py-1 border-[1.5px] border-[#121212]">
                  {project.course}
                </span>
              )}
              {project.team && (
                <span className="font-mono text-[11px] bg-[#F2ECE1] text-[#1c1b1b] px-2 py-1 border-[1.5px] border-[#121212]">
                  Team: {project.team}
                </span>
              )}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t-2 border-[#121212] flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-4 font-mono text-[11px] text-[#1c1b1b]">
              {project.status === 'completed' && (
                <span className="flex items-center gap-1 text-[#006b58] font-bold">
                  <CheckCircle size={15} />
                  Analysis Complete
                </span>
              )}
              {project.status === 'processing' && (
                <span className="flex items-center gap-1 text-[#4b4731]">
                  <RefreshCw size={15} className="animate-spin" />
                  {project.processingStage ?? 'Processing...'}
                </span>
              )}
              {project.status === 'pending' && (
                <span className="flex items-center gap-1 text-[#4b4731]">
                  <Layers size={15} />
                  {project.processingStage ?? 'Queued for analysis'}
                </span>
              )}
            </div>
            <button
              className="btn-secondary text-sm px-3 py-1.5"
              onClick={() => setActiveTab('report')}
            >
              <Edit3 size={14} />
              Quick Grade
            </button>
          </div>
        </div>

        {/* Right: score card */}
        <div
          className="w-full lg:w-[340px] bg-white border-[2.5px] border-[#121212] flex flex-col justify-between"
          style={{ boxShadow: '4px 4px 0px #121212' }}
        >
          <div className="bg-[#ffe600] border-b-2 border-[#121212] px-4 py-2 flex items-center justify-between">
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest">Calculated Score</span>
            {analysis?.evaluationReport?.grade && (
              <span className="font-mono text-[11px] font-bold bg-white px-2 py-0.5 border-[1.5px] border-[#121212]">
                Grade {analysis.evaluationReport.grade}
              </span>
            )}
          </div>
          <div className="p-6 flex flex-col items-center justify-center text-center flex-1">
            {analysis?.evaluationReport?.overallScore !== undefined || (project.score !== undefined && project.score !== null) ? (
              <>
                <div className="flex items-baseline gap-1 my-2">
                  <span className="font-display font-bold text-[60px] text-[#1c1b1b] leading-none tracking-tighter">
                    {analysis?.evaluationReport?.overallScore ?? project.score}
                  </span>
                  <span className="font-display font-bold text-xl text-[#4b4731]">/100</span>
                </div>
                <p className="font-mono text-[11px] text-[#4b4731]">
                  {analysis?.evaluationReport?.grade ? `Faculty Grade ${analysis.evaluationReport.grade}` : 'Faculty Baseline Score from Backend'}
                </p>
              </>
            ) : (
              <div className="text-center py-4">
                <p className="font-mono text-[11px] text-[#4b4731] uppercase tracking-wide">
                  {project.status === 'processing' ? 'Score pending...' : 'Pending Evaluation'}
                </p>
              </div>
            )}
          </div>
          <div className="p-3 border-t-2 border-[#121212] bg-[#F2ECE1]">
            <button
              className="w-full py-2 px-4 bg-[#ffe600] text-[#1c1b1b] font-display font-bold border-2 border-[#121212] flex items-center justify-center gap-2 hover:-translate-y-0.5 transition-all cursor-pointer disabled:opacity-50"
              style={{ boxShadow: '2px 2px 0px #121212' }}
              onClick={handleDownload}
              disabled={!analysis?.evaluationReport?.reportAvailable || reportLoading}
            >
              <Download size={16} />
              Download PDF Report
            </button>
          </div>
        </div>
      </section>

      {/* ── Sticky tab bar ── */}
      <div className="sticky top-20 z-40 bg-[#FAF6EE] pt-1 pb-2 border-b-2 border-[#121212]">
        <div className="flex items-center overflow-x-auto gap-1 py-1 no-scrollbar">
          {TABS.map((tab) => {
            const isActive = activeTab === tab.id;
            let badge: string | null = null;
            if (tab.id === 'code' && codeQuality?.score !== undefined && codeQuality.score !== null) {
              badge = `${codeQuality.score}`;
            }
            if (tab.id === 'similarity') {
              if (similarity && similarity.status !== 'not_started' && similarity.status !== 'no_candidates') {
                badge = `${similarity.overallSimilarity}%`;
              } else if (simPct !== undefined) {
                badge = `${simPct}%`;
              }
            }
            if (tab.id === 'docs' && documentation && documentation.status !== 'not_started') {
              if (documentation.preliminaryScore !== null && documentation.preliminaryScore !== undefined) {
                badge = `${documentation.preliminaryScore}`;
              } else if (documentation.status === 'insufficient_evidence') {
                badge = 'N/A';
              }
            }
            if (tab.id === 'ai') {
              const currentAi = aiAssistance ?? analysis?.aiAssistance;
              if (currentAi && currentAi.analysisStatus === 'completed') {
                badge = currentAi.advisoryCategory === 'Multiple Observable Signals Requiring Faculty Review'
                  ? 'Review'
                  : currentAi.advisoryCategory === 'Some Observable Signals'
                    ? 'Signals'
                    : 'Done';
              }
            }
            if (tab.id === 'viva' && vqCount !== undefined) badge = `${vqCount} Qs`;
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                className={`tab-btn ${isActive ? 'active' : ''} flex items-center gap-1.5`}
                onClick={() => setActiveTab(tab.id)}
                aria-current={isActive ? 'true' : undefined}
              >
                {tab.label}
                {badge && (
                  <span className={`font-mono text-[9px] font-bold px-1.5 py-0.5 border border-[#121212] ${tab.id === 'similarity' ? 'bg-[#FF5C8D] text-white' :
                    tab.id === 'code' ? 'bg-[#ffe600] text-[#1c1b1b]' :
                      tab.id === 'docs' ? 'bg-[#D8B4FE] text-[#1c1b1b]' :
                        tab.id === 'ai' ? 'bg-[#FFF4D6] text-[#1c1b1b]' :
                          'bg-[#00E5BE] text-[#1c1b1b]'
                    }`}>
                    {badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Tab panels ── */}
      <div className="tab-panel-container">
        {activeTab === 'overview' && (
          <ErrorBoundary sectionName="Overview">
            <OverviewTab
              project={project}
              analysis={analysis}
              structure={structure}
              codeQuality={codeQuality}
              onReparse={handleReparse}
              parsing={parsing}
            />
          </ErrorBoundary>
        )}
        {activeTab === 'code' && (
          <ErrorBoundary sectionName="Code Quality">
            <CodeQualityTab
              codeQuality={codeQuality}
              loading={cqLoading}
              analyzing={cqAnalyzing}
              onAnalyze={handleAnalyzeCodeQuality}
              error={cqError}
            />
          </ErrorBoundary>
        )}
        {activeTab === 'similarity' && (
          <ErrorBoundary sectionName="Similarity">
            <SimilarityTab
              similarity={similarity}
              loading={simLoading}
              analyzing={simAnalyzing}
              onAnalyze={handleAnalyzeSimilarity}
              error={simError}
            />
          </ErrorBoundary>
        )}
        {activeTab === 'docs' && (
          <ErrorBoundary sectionName="Documentation & Development History">
            <DocumentationTab
              documentation={documentation}
              loading={docLoading}
              analyzing={docAnalyzing}
              onAnalyze={handleAnalyzeDocumentation}
              error={docError}
              gitHistory={gitHistory}
              gitLoading={gitLoading}
              gitAnalyzing={gitAnalyzing}
              onAnalyzeGit={handleAnalyzeGitHistory}
              gitError={gitError}
            />
          </ErrorBoundary>
        )}
        {activeTab === 'ai' && (
          <ErrorBoundary sectionName="AI Assistance & Innovation">
            <AIAssistanceTab
              analysis={analysis}
              aiAssistance={aiAssistance}
              analyzing={aiAnalyzing}
              error={aiError}
              onAnalyze={handleAnalyzeAIAssistance}
              innovation={innovation}
              innovAnalyzing={innovAnalyzing}
              innovError={innovError}
              onAnalyzeInnovation={handleAnalyzeInnovation}
            />
          </ErrorBoundary>
        )}
        {activeTab === 'viva' && (
          <ErrorBoundary sectionName="Viva Questions">
            <VivaTab project={project} analysis={analysis} />
          </ErrorBoundary>
        )}
        {activeTab === 'report' && (
          <ErrorBoundary sectionName="Evaluation Report">
            <ReportTab
              project={project}
              analysis={analysis}
              onDownload={handleDownload}
              onRequestReport={handleRequestReport}
              onExportJson={handleDownloadJson}
              reportLoading={reportLoading}
              reportError={reportError}
            />
          </ErrorBoundary>
        )}
      </div>

      {/* Breadcrumb back */}
      <div className="pt-4 border-t-2 border-[#121212]">
        <Link to="/" className="flex items-center gap-1 font-mono text-[11px] text-[#4b4731] hover:text-[#1c1b1b] font-bold">
          <ChevronRight size={13} className="rotate-180" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
