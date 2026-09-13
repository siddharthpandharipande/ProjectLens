import React from 'react';
import { AnalysisMeta } from '../../types/overview';
import { FileCheck, FileX, CheckCircle, AlertCircle, RotateCw } from 'lucide-react';

interface AnalysisStatusProps {
  analysis: AnalysisMeta;
  onReanalyze?: () => void;
  isReanalyzing?: boolean;
}

export const AnalysisStatus: React.FC<AnalysisStatusProps> = ({
  analysis,
  onReanalyze,
  isReanalyzing = false,
}) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-headline font-bold text-base text-white">
          Analysis Metadata & Status
        </h3>
        {onReanalyze && (
          <button
            onClick={onReanalyze}
            disabled={isReanalyzing}
            className="flex items-center gap-2 py-1.5 px-3 rounded bg-primary/10 border border-primary/30 text-primary hover:bg-primary/20 text-xs font-semibold transition-all disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 ${isReanalyzing ? 'animate-spin' : ''}`} />
            {isReanalyzing ? 'Re-analyzing...' : 'Re-Analyze Codebase'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-bg-main border border-border">
          <div className="p-2 rounded bg-status-green/10 text-status-green">
            <FileCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="font-headline font-bold text-lg text-white">
              {analysis.files_analyzed} / {analysis.total_files}
            </div>
            <div className="font-mono text-[10px] text-zinc-400 uppercase">
              Files Analyzed
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-bg-main border border-border">
          <div className={`p-2 rounded ${analysis.files_failed > 0 ? 'bg-status-red/10 text-status-red' : 'bg-zinc-800 text-zinc-400'}`}>
            <FileX className="w-5 h-5" />
          </div>
          <div>
            <div className="font-headline font-bold text-lg text-white">
              {analysis.files_failed}
            </div>
            <div className="font-mono text-[10px] text-zinc-400 uppercase">
              Parse Failures
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-bg-main border border-border">
          <div className="p-2 rounded bg-primary/10 text-primary">
            {analysis.status === 'completed' ? (
              <CheckCircle className="w-5 h-5 text-status-green" />
            ) : (
              <AlertCircle className="w-5 h-5 text-status-yellow" />
            )}
          </div>
          <div>
            <div className="font-mono text-sm font-semibold text-white capitalize">
              {analysis.status}
            </div>
            <div className="font-mono text-[10px] text-zinc-400 uppercase">
              Pipeline Status
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
