import React, { useState } from 'react';
import { Strength } from '../../types/overview';
import { CheckCircle2, Sparkles, X } from 'lucide-react';

interface StrengthsPanelProps {
  strengths: Strength[];
}

export const StrengthsPanel: React.FC<StrengthsPanelProps> = ({ strengths }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  const displayedStrengths = strengths.slice(0, 4);
  const remainingCount = Math.max(0, strengths.length - 4);

  return (
    <div className="bg-[#17191F] border border-[#262933] rounded-xl p-6 shadow-md flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-headline font-bold text-base text-emerald-400 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            Identified Strengths
          </h3>
          {strengths.length > 0 && (
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              {strengths.length} Found
            </span>
          )}
        </div>

        {strengths.length > 0 ? (
          <ul className="space-y-3.5">
            {displayedStrengths.map((str, idx) => (
              <li key={idx} className="flex items-start gap-3 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                <div>
                  <strong className="text-white block font-medium mb-0.5">{str.title}</strong>
                  <p className="text-zinc-400 leading-relaxed text-[11px]">{str.description}</p>
                  {str.evidence && (
                    <span className="text-[10px] text-emerald-400/80 font-mono mt-0.5 block">
                      Evidence: {str.evidence}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-zinc-500 font-mono">
            No significant evidence-backed strengths met threshold criteria.
          </p>
        )}
      </div>

      {remainingCount > 0 && (
        <div className="mt-4 pt-3 border-t border-[#262933]">
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-xs text-emerald-400 hover:text-emerald-300 font-medium transition-colors"
          >
            View all {strengths.length} strengths →
          </button>
        </div>
      )}

      {/* Modal Drawer for all strengths */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            <div className="p-5 border-b border-[#2A2D38] flex items-center justify-between bg-[#13151A]">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-emerald-400" />
                <h3 className="font-headline font-bold text-base text-white">
                  All Identified Repository Strengths ({strengths.length})
                </h3>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1 rounded-lg text-zinc-400 hover:text-white bg-[#21242D]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 max-h-[calc(80vh-120px)]">
              {strengths.map((str, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] space-y-1">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                    <span className="font-bold text-xs text-white">{str.title}</span>
                  </div>
                  <p className="text-xs text-zinc-400 pl-6">{str.description}</p>
                  {str.evidence && (
                    <span className="text-[10px] text-emerald-400 font-mono pl-6 block">
                      Evidence: {str.evidence}
                    </span>
                  )}
                </div>
              ))}
            </div>

            <div className="p-3 border-t border-[#2A2D38] flex justify-end bg-[#13151A]">
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-xs transition-colors"
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
