import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Code2, AlertTriangle, Info, CheckCircle2, ShieldAlert, Cpu, Sparkles } from 'lucide-react';
import { projectService } from '../../services/projectService';

interface Finding {
  type: string;
  severity: 'HIGH' | 'WARNING' | 'INFO';
  file: string;
  message: string;
  recommendation: string;
}

interface CodeQualityData {
  project_id: string;
  overall_score: number;
  subscores: {
    complexity: number;
    maintainability: number;
    modularity: number;
    duplication: number;
    naming: number;
  };
  metrics: {
    total_loc: number;
    code_lines: number;
    comment_lines: number;
    blank_lines: number;
    average_complexity: number;
    maximum_complexity: number;
    source_files: number;
    large_files: number;
  };
  findings: Finding[];
}

interface CodeQualityDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectId: string;
}

export const CodeQualityDetailModal: React.FC<CodeQualityDetailModalProps> = ({
  isOpen,
  onClose,
  projectId,
}) => {
  const [data, setData] = useState<CodeQualityData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && projectId) {
      setIsLoading(true);
      setError(null);
      projectService
        .getCodeQualityAnalysis(projectId)
        .then((res) => {
          setData(res);
          setIsLoading(false);
        })
        .catch((err) => {
          console.error('Failed to load code quality analysis:', err);
          setError(err.message || 'Failed to fetch code quality metrics.');
          setIsLoading(false);
        });
    }
  }, [isOpen, projectId]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-3xl overflow-hidden shadow-2xl"
        >
          {/* Header */}
          <div className="p-6 bg-gradient-to-r from-[#1C1F2B] to-[#17191F] border-b border-[#2A2D38] flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
                <Code2 className="w-5 h-5 text-indigo-400" />
              </div>
              <div>
                <h3 className="font-headline font-bold text-lg text-white">
                  Code Quality & Maintainability Audit
                </h3>
                <p className="text-xs text-zinc-400">
                  AST structural complexity, modularity metrics, and maintainability findings
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white bg-[#21242D] hover:bg-[#2A2D38] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Modal Content */}
          <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
            {isLoading && (
              <div className="py-12 text-center text-zinc-400 space-y-3">
                <Cpu className="w-8 h-8 animate-spin mx-auto text-indigo-400" />
                <p className="text-xs font-mono">Analyzing AST metrics and quality findings...</p>
              </div>
            )}

            {error && (
              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs">
                {error}
              </div>
            )}

            {data && !isLoading && (
              <>
                {/* Overall Score Header */}
                <div className="bg-[#0F1014] border border-[#262933] rounded-xl p-5 flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="font-mono text-xs uppercase tracking-wider text-zinc-400">
                      Weighted Technical Quality Score
                    </span>
                    <div className="flex items-center gap-3">
                      <span className="font-headline font-bold text-3xl text-white">
                        {data.overall_score} <span className="text-sm text-zinc-500 font-normal">/ 100</span>
                      </span>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {data.overall_score >= 80 ? 'High Maintainability' : data.overall_score >= 60 ? 'Moderate Quality' : 'Needs Refactoring'}
                      </span>
                    </div>
                  </div>
                  <div className="text-right font-mono text-xs text-zinc-400 space-y-1">
                    <div>Source Files: <span className="text-white font-bold">{data.metrics.source_files}</span></div>
                    <div>Avg Complexity: <span className="text-white font-bold">{data.metrics.average_complexity}</span></div>
                  </div>
                </div>

                {/* Subscores Grid */}
                <div>
                  <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">
                    Quality Subscore Breakdown
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-[#262933]">
                      <span className="text-[11px] text-zinc-400 block mb-1">Complexity</span>
                      <span className="font-mono font-bold text-base text-indigo-400">{data.subscores.complexity}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-[#262933]">
                      <span className="text-[11px] text-zinc-400 block mb-1">Maintainability</span>
                      <span className="font-mono font-bold text-base text-emerald-400">{data.subscores.maintainability}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-[#262933]">
                      <span className="text-[11px] text-zinc-400 block mb-1">Modularity</span>
                      <span className="font-mono font-bold text-base text-cyan-400">{data.subscores.modularity}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-[#262933]">
                      <span className="text-[11px] text-zinc-400 block mb-1">Deduplication</span>
                      <span className="font-mono font-bold text-base text-amber-400">{data.subscores.duplication}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-[#262933]">
                      <span className="text-[11px] text-zinc-400 block mb-1">Naming</span>
                      <span className="font-mono font-bold text-base text-purple-400">{data.subscores.naming}</span>
                    </div>
                  </div>
                </div>

                {/* Code Metrics Summary */}
                <div>
                  <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">
                    Line & Volume Statistics
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-zinc-800/80">
                      <span className="text-zinc-400 block text-[10px]">Total LOC</span>
                      <span className="text-white font-bold text-sm">{data.metrics.total_loc.toLocaleString()}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-zinc-800/80">
                      <span className="text-zinc-400 block text-[10px]">Code Lines</span>
                      <span className="text-white font-bold text-sm">{data.metrics.code_lines.toLocaleString()}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-zinc-800/80">
                      <span className="text-zinc-400 block text-[10px]">Comment Lines</span>
                      <span className="text-white font-bold text-sm">{data.metrics.comment_lines.toLocaleString()}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-[#0F1014] border border-zinc-800/80">
                      <span className="text-zinc-400 block text-[10px]">Max Complexity</span>
                      <span className="text-white font-bold text-sm">{data.metrics.maximum_complexity}</span>
                    </div>
                  </div>
                </div>

                {/* Findings & Warnings */}
                <div>
                  <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">
                    Code Quality Findings ({data.findings.length})
                  </h4>

                  {data.findings.length === 0 ? (
                    <div className="p-4 rounded-xl bg-[#0F1014] border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>No critical code quality smells or complexity violations detected!</span>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {data.findings.map((f, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-[#0F1014] border border-[#262933] space-y-2 text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2 font-mono">
                              {f.severity === 'HIGH' ? (
                                <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-400 text-[10px] font-bold border border-rose-500/30 flex items-center gap-1">
                                  <ShieldAlert className="w-3 h-3" /> HIGH
                                </span>
                              ) : f.severity === 'WARNING' ? (
                                <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-400 text-[10px] font-bold border border-amber-500/30 flex items-center gap-1">
                                  <AlertTriangle className="w-3 h-3" /> WARNING
                                </span>
                              ) : (
                                <span className="px-2 py-0.5 rounded bg-blue-500/20 text-blue-400 text-[10px] font-bold border border-blue-500/30 flex items-center gap-1">
                                  <Info className="w-3 h-3" /> INFO
                                </span>
                              )}
                              <span className="text-zinc-300 font-semibold">{f.type}</span>
                            </div>
                            <span className="font-mono text-[11px] text-zinc-400 truncate max-w-[250px]">
                              {f.file}
                            </span>
                          </div>
                          <p className="text-zinc-300">{f.message}</p>
                          <p className="text-[#A5B4FC] text-[11px] bg-indigo-950/30 p-2 rounded border border-indigo-500/20">
                            <strong>Recommendation:</strong> {f.recommendation}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Footer */}
          <div className="p-4 bg-[#111318] border-t border-[#2A2D38] flex items-center justify-between">
            <span className="font-mono text-xs text-zinc-500">
              ProjectLens AST Static Audit Engine
            </span>
            <button
              onClick={onClose}
              className="py-2 px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
            >
              Close
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
