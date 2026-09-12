import React from 'react';
import { Improvement } from '../../types/overview';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface ImprovementsPanelProps {
  improvements: Improvement[];
}

export const ImprovementsPanel: React.FC<ImprovementsPanelProps> = ({ improvements }) => {
  const getSeverityBadge = (severity?: string) => {
    switch (severity) {
      case 'critical':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 font-bold uppercase">
            <AlertCircle className="w-2.5 h-2.5" /> Critical
          </span>
        );
      case 'warning':
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-400 font-bold uppercase">
            <AlertTriangle className="w-2.5 h-2.5" /> Warning
          </span>
        );
      case 'info':
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded bg-blue-500/10 border border-blue-500/30 text-blue-400 font-bold uppercase">
            <Info className="w-2.5 h-2.5" /> Notice
          </span>
        );
    }
  };

  return (
    <div className="bg-[#17191F] border border-[#262933] rounded-xl p-6 shadow-md flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-headline font-bold text-base text-amber-400 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Areas for Improvement
          </h3>
          {improvements.length > 0 && (
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {improvements.length} Flagged
            </span>
          )}
        </div>

        {improvements.length > 0 ? (
          <ul className="space-y-3.5">
            {improvements.map((imp, idx) => (
              <li key={idx} className="flex items-start gap-3 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 shrink-0" />
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <strong className="text-white font-medium">{imp.title}</strong>
                    {getSeverityBadge(imp.severity)}
                  </div>
                  <p className="text-zinc-400 leading-relaxed text-[11px]">{imp.description}</p>
                  {imp.evidence && (
                    <span className="text-[10px] text-amber-400/80 font-mono block">
                      Evidence: {imp.evidence}
                    </span>
                  )}
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-zinc-500 font-mono">
            No critical areas for improvement flagged by threshold detectors.
          </p>
        )}
      </div>
    </div>
  );
};
