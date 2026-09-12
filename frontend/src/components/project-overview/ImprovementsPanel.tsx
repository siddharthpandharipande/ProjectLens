import React from 'react';
import { Improvement } from '../../types/overview';
import { AlertTriangle } from 'lucide-react';

interface ImprovementsPanelProps {
  improvements: Improvement[];
}

export const ImprovementsPanel: React.FC<ImprovementsPanelProps> = ({ improvements }) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-6">
      <h3 className="font-headline font-bold text-base text-secondary flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-secondary" />
        Areas for Improvement
      </h3>

      {improvements.length > 0 ? (
        <ul className="space-y-3">
          {improvements.map((imp, idx) => (
            <li key={idx} className="flex items-start gap-3 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-secondary mt-1.5 shrink-0" />
              <div>
                <strong className="text-white block font-medium mb-0.5">{imp.title}</strong>
                <span className="text-zinc-400 leading-relaxed">{imp.description}</span>
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
  );
};
