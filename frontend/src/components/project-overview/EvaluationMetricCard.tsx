import React, { useState } from 'react';
import { Clock, HelpCircle, X, CheckCircle2, AlertTriangle, Sparkles } from 'lucide-react';
import { EvaluationDetail } from '../../types/overview';

interface EvaluationMetricCardProps {
  title: string;
  score: number | null;
  strokeColor?: string;
  detail?: EvaluationDetail | null;
  subtext?: string;
}

export const EvaluationMetricCard: React.FC<EvaluationMetricCardProps> = ({
  title,
  score,
  strokeColor = '#3157D5',
  detail,
  subtext
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const evidenceList = detail?.evidence || [];
  const statusLabel = detail?.status || (score !== null ? 'completed' : 'Pending');

  return (
    <div className="bg-[#17191F] border border-[#262933] rounded-xl p-5 flex flex-col justify-between shadow-md relative group">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
              {title}
            </h4>
            {(evidenceList.length > 0 || detail) && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="text-zinc-500 hover:text-indigo-400 transition-colors p-0.5"
                title="View scoring rationale & evidence"
              >
                <HelpCircle className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          <div className="flex items-baseline gap-2 mt-1">
            {score !== null ? (
              <span className="font-headline font-bold text-3xl text-white">{score}</span>
            ) : (
              <div className="flex items-center gap-1.5 text-zinc-400 mt-1">
                <Clock className="w-4 h-4 text-zinc-500" />
                <span className="font-mono text-sm text-zinc-400 font-medium">
                  {statusLabel === 'N/A' ? 'N/A' : 'Pending'}
                </span>
              </div>
            )}
          </div>

          <p className="text-[11px] text-zinc-400 mt-2 line-clamp-1">
            {subtext || (evidenceList.length > 0 ? evidenceList[0] : statusLabel)}
          </p>
        </div>

        <div className="w-12 h-12 relative flex items-center justify-center flex-shrink-0">
          {score !== null ? (
            <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-zinc-800"
                strokeWidth="3"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                strokeWidth="3"
                strokeDasharray={`${score}, 100`}
                stroke={strokeColor}
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
          ) : (
            <div className="w-10 h-10 rounded-full border border-dashed border-zinc-700 flex items-center justify-center text-[10px] font-mono text-zinc-500">
              {statusLabel === 'N/A' ? 'N/A' : 'TBD'}
            </div>
          )}
        </div>
      </div>

      {/* Rationale Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150"
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
                  {title} Evaluation Rationale
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
              <div className="flex items-center justify-between p-3 rounded-lg bg-[#0F1014] border border-[#262933]">
                <span className="text-xs text-zinc-400 font-medium">Calculated Score</span>
                <span className="font-mono font-bold text-lg text-white">
                  {score !== null ? `${score} / 100` : statusLabel}
                </span>
              </div>

              {evidenceList.length > 0 && (
                <div className="space-y-2">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">
                    Repository Findings & Rationale
                  </span>
                  <div className="space-y-1.5 text-xs text-zinc-300">
                    {evidenceList.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-2 p-2 rounded bg-[#0F1014] border border-zinc-800">
                        {item.startsWith('✓') ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mt-0.5 flex-shrink-0" />
                        ) : (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 mt-0.5 flex-shrink-0" />
                        )}
                        <span>{item.replace(/^[✓⚠]\s*/, '')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {detail?.breakdown && Object.keys(detail.breakdown).length > 0 && (
                <div className="space-y-2 pt-2 border-t border-zinc-800">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-zinc-400">
                    Sub-Metric Contributions
                  </span>
                  <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                    {Object.entries(detail.breakdown).map(([k, v]) => (
                      <div key={k} className="p-2 rounded bg-[#0F1014] border border-zinc-800 flex justify-between">
                        <span className="text-zinc-400 capitalize">{k.replace('_', ' ')}</span>
                        <span className="text-white font-bold">{v} pts</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
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
