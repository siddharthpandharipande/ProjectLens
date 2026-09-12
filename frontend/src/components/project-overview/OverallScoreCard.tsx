import React, { useState } from 'react';
import { Clock, Sparkles, HelpCircle, X, CheckCircle2 } from 'lucide-react';
import { Evaluation } from '../../types/overview';

interface OverallScoreCardProps {
  score: number | null;
  evaluation?: Evaluation;
}

export const OverallScoreCard: React.FC<OverallScoreCardProps> = ({ score, evaluation }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const statusText = evaluation?.overall_status || (score !== null ? 'Evaluation Complete' : 'Evaluation Pending');

  return (
    <div className="bg-[#17191F] border border-[#262933] rounded-xl p-6 flex flex-col items-center justify-center text-center shadow-md relative">
      {score !== null ? (
        <div className="w-32 h-32 rounded-full border-8 border-zinc-800 border-t-indigo-500 flex flex-col items-center justify-center mb-4 relative shadow-inner">
          <span className="font-headline font-bold text-4xl text-white">{score}</span>
          <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-mono">Overall</span>
        </div>
      ) : (
        <div className="w-32 h-32 rounded-full border-4 border-dashed border-zinc-800 flex flex-col items-center justify-center mb-4 text-zinc-500">
          <Clock className="w-8 h-8 text-zinc-500 mb-1" />
          <span className="text-[11px] font-mono font-medium text-zinc-400">Pending</span>
        </div>
      )}

      <div className="flex items-center gap-2">
        <span className="px-3 py-1 rounded-full text-xs font-mono font-medium border border-zinc-700 bg-[#21242D] text-zinc-300">
          {score !== null ? 'Evaluation Complete' : 'Evaluation Pending'}
        </span>

        {evaluation && (
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-zinc-500 hover:text-indigo-400 transition-colors p-1"
            title="View overall score calculation"
          >
            <HelpCircle className="w-4 h-4" />
          </button>
        )}
      </div>

      <p className="text-[11px] text-zinc-400 mt-3 max-w-[220px]">
        {statusText}
      </p>

      {/* Overall Score Details Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150 text-left"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-center justify-between pb-3 border-b border-[#2A2D38]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                <h3 className="font-headline font-bold text-base text-white">
                  Overall Score Calculation
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white bg-[#21242D]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-3">
              <p className="text-xs text-zinc-400">
                The overall evaluation score is calculated as a transparent weighted average of available evaluation dimensions. Unavailable dimensions are excluded to prevent unfair penalization.
              </p>

              <div className="space-y-2">
                <div className="p-2.5 rounded-lg bg-[#0F1014] border border-[#262933] flex justify-between items-center text-xs">
                  <span className="text-zinc-300 font-medium">Technical Execution</span>
                  <span className="font-mono font-bold text-white">
                    {evaluation?.technical_execution !== null ? `${evaluation?.technical_execution} / 100` : 'Pending'}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-[#0F1014] border border-[#262933] flex justify-between items-center text-xs">
                  <span className="text-zinc-300 font-medium">Documentation Integrity</span>
                  <span className="font-mono font-bold text-white">
                    {evaluation?.documentation_integrity !== null ? `${evaluation?.documentation_integrity} / 100` : 'Pending'}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-[#0F1014] border border-[#262933] flex justify-between items-center text-xs">
                  <span className="text-zinc-300 font-medium">Development Process</span>
                  <span className="font-mono font-bold text-white">
                    {evaluation?.development_process !== null ? `${evaluation?.development_process} / 100` : 'N/A (Git history missing)'}
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-[#0F1014] border border-[#262933] flex justify-between items-center text-xs">
                  <span className="text-zinc-300 font-medium">Originality Assessment</span>
                  <span className="font-mono font-bold text-zinc-400">
                    Pending (Requires comparison data)
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#2A2D38] flex justify-end">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
