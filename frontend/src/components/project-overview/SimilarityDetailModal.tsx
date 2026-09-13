import React, { useState, useEffect } from 'react';
import { X, ShieldCheck, Dna, FileCode, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { projectService } from '../../services/projectService';

interface SimilarityDetailModalProps {
  isOpen: boolean;
  projectId: string;
  onClose: () => void;
}

export const SimilarityDetailModal: React.FC<SimilarityDetailModalProps> = ({
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
        .getSimilarityAnalysis(projectId)
        .then((res) => {
          setData(res);
          setIsLoading(false);
        })
        .catch((err) => {
          setError(err.message || 'Failed to fetch similarity comparison.');
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
            <div className="p-2 rounded-lg bg-coral/10 border border-coral/30 text-coral">
              <Dna className="w-5 h-5 text-[#E9785B]" />
            </div>
            <div>
              <h3 className="font-headline font-bold text-base text-white">
                Code Similarity & Originality Engine
              </h3>
              <p className="text-xs text-zinc-400 font-mono">
                Token Jaccard &bull; AST Structural Compare &bull; Cosine Embeddings
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
            <div className="w-6 h-6 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
            <span className="text-xs font-mono text-zinc-400">Comparing AST signatures across repository corpus...</span>
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
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Overall Similarity</span>
                <span className="font-headline font-bold text-xl text-white">
                  {data.similarity_percentage ? `${data.similarity_percentage}%` : '0%'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Token Jaccard</span>
                <span className="font-headline font-bold text-lg text-indigo-400">
                  {data.token_similarity ? `${(data.token_similarity * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">AST Structural</span>
                <span className="font-headline font-bold text-lg text-emerald-400">
                  {data.ast_similarity ? `${(data.ast_similarity * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-center">
                <span className="block text-[10px] font-mono text-zinc-500 uppercase">Semantic Vector</span>
                <span className="font-headline font-bold text-lg text-amber-400">
                  {data.semantic_similarity ? `${(data.semantic_similarity * 100).toFixed(1)}%` : '0%'}
                </span>
              </div>
            </div>

            {/* Comparison Details */}
            {data.project_b ? (
              <div className="p-3 rounded-lg bg-[#0F1014] border border-zinc-800 text-xs text-zinc-300 flex justify-between items-center">
                <span>Paired Comparison Target:</span>
                <span className="font-mono font-bold text-white">
                  {data.project_b.name} ({data.project_b.student_name})
                </span>
              </div>
            ) : (
              <div className="p-3 rounded-lg bg-[#0F1014] border border-zinc-800 text-xs text-zinc-400">
                {data.message || 'Single project uploaded. Upload additional repositories to view pairwise corpus matrix.'}
              </div>
            )}

            {/* Matching File Evidence */}
            {data.matching_files && data.matching_files.length > 0 && (
              <div className="space-y-2">
                <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400 flex items-center gap-1.5">
                  <FileCode className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Matching Source File Pair Signatures ({data.matching_files.length})</span>
                </span>
                <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                  {data.matching_files.map((mf: any, idx: number) => (
                    <div key={idx} className="p-2.5 rounded-lg bg-[#0F1014] border border-[#262933] flex justify-between items-center text-xs font-mono">
                      <div className="flex items-center gap-2 truncate max-w-[70%]">
                        <span className="text-zinc-300">{mf.file_a}</span>
                        <span className="text-zinc-600">&rarr;</span>
                        <span className="text-zinc-400">{mf.file_b}</span>
                      </div>
                      <div className="flex gap-2 text-[11px]">
                        <span className="text-indigo-400 font-bold">Token: {(mf.token_score * 100).toFixed(0)}%</span>
                        <span className="text-emerald-400 font-bold">AST: {(mf.ast_score * 100).toFixed(0)}%</span>
                      </div>
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
            className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
