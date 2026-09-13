import React, { useState, useEffect } from 'react';
import { X, FileText, CheckCircle2, AlertTriangle, Layers, BookOpen } from 'lucide-react';
import { projectService } from '../../services/projectService';

interface DocumentationDetailModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
}

export const DocumentationDetailModal: React.FC<DocumentationDetailModalProps> = ({
  isOpen,
  projectId,
  onClose,
}) => {
  const [data, setData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && projectId) {
      setIsLoading(true);
      setError(null);
      projectService
        .getDocumentationAnalysis(projectId)
        .then((res) => {
          setData(res);
          setIsLoading(false);
        })
        .catch((err) => {
          setError(err.message || 'Failed to fetch documentation analysis.');
          setIsLoading(false);
        });
    }
  }, [isOpen, projectId]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150"
      onClick={onClose}
    >
      <div
        className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-2xl p-6 shadow-2xl space-y-5 relative overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between pb-3 border-b border-[#2A2D38]">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
              <BookOpen className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h3 className="font-headline font-bold text-base text-white">
                Documentation Integrity & Consistency Engine
              </h3>
              <p className="text-xs text-zinc-400 font-mono">
                PyMuPDF Parsing &bull; Section Structure &bull; Code ↔ Doc Mismatch Detection
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-zinc-400 hover:text-white bg-[#21242D] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {isLoading ? (
          <div className="py-12 flex flex-col items-center justify-center gap-3">
            <div className="w-6 h-6 border-2 border-emerald-500/30 border-t-emerald-500 rounded-full animate-spin" />
            <span className="text-xs font-mono text-zinc-400">Parsing PDF & Markdown documentation artifacts...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-lg bg-status-red/10 border border-status-red/30 text-status-red text-xs">
            {error}
          </div>
        ) : data ? (
          <div className="space-y-4">
            {/* Top Score Banner */}
            <div className="grid grid-cols-4 gap-3">
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Doc Integrity</span>
                <span className="font-headline font-bold text-xl text-white">
                  {data.overall_score !== null ? `${data.overall_score}` : 'N/A'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Section Coverage</span>
                <span className="font-headline font-bold text-lg text-emerald-400">
                  {data.subscores?.completeness}%
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Consistency</span>
                <span className="font-headline font-bold text-lg text-indigo-400">
                  {data.subscores?.consistency}%
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Doc Files</span>
                <span className="font-headline font-bold text-lg text-amber-400">
                  {data.doc_file_count}
                </span>
              </div>
            </div>

            {/* Code ↔ Doc Mismatches */}
            {data.mismatches && data.mismatches.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-status-red flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4 text-status-red" />
                  <span>Code ↔ Documentation Mismatches Detected ({data.mismatches.length})</span>
                </span>
                <div className="space-y-2">
                  {data.mismatches.map((m: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-status-red/10 border border-status-red/30 space-y-1">
                      <div className="flex justify-between items-center text-xs font-bold text-white">
                        <span>Claimed: {m.claim}</span>
                        <span className="font-mono text-[10px] px-2 py-0.5 rounded bg-status-red/20 text-status-red uppercase">{m.type}</span>
                      </div>
                      <p className="text-xs text-zinc-300">{m.message}</p>
                      <p className="text-[11px] text-zinc-400 font-mono italic">Recommendation: {m.recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Verified Tech Claims */}
            {data.matched_claims && data.matched_claims.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Verified Implementation Claims ({data.matched_claims.length})</span>
                </span>
                <div className="grid grid-cols-2 gap-2">
                  {data.matched_claims.map((mc: any, idx: number) => (
                    <div key={idx} className="p-2 rounded bg-[#0F1014] border border-zinc-800 flex items-center justify-between text-xs">
                      <span className="font-bold text-white">{mc.claim}</span>
                      <span className="text-[10px] font-mono text-emerald-400">✓ VERIFIED</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Section Structure Checklist */}
            {data.structure && data.structure.sections_detected && (
              <div className="space-y-2 pt-2 border-t border-[#2A2D38]">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">
                  Academic Report Section Structure ({data.structure.detected_count} / {data.structure.total_count})
                </span>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {Object.entries(data.structure.sections_detected).map(([sec, present]) => (
                    <div
                      key={sec}
                      className={`p-2 rounded border flex items-center gap-1.5 capitalize font-mono text-[11px] ${
                        present
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                          : 'bg-zinc-900 border-zinc-800 text-zinc-500 line-through'
                      }`}
                    >
                      {present ? (
                        <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />
                      ) : (
                        <X className="w-3 h-3 text-zinc-600 shrink-0" />
                      )}
                      <span className="truncate">{sec}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : null}

        <div className="pt-3 border-t border-[#2A2D38] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
