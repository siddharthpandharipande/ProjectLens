import React from 'react';
import { Strength } from '../../types/overview';
import { CheckCircle2 } from 'lucide-react';

interface StrengthsPanelProps {
  strengths: Strength[];
}

export const StrengthsPanel: React.FC<StrengthsPanelProps> = ({ strengths }) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-6">
      <h3 className="font-headline font-bold text-base text-status-green flex items-center gap-2 mb-4">
        <CheckCircle2 className="w-5 h-5 text-status-green" />
        Identified Strengths
      </h3>

      {strengths.length > 0 ? (
        <ul className="space-y-3">
          {strengths.map((str, idx) => (
            <li key={idx} className="flex items-start gap-3 text-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-status-green mt-1.5 shrink-0" />
              <div>
                <strong className="text-white block font-medium mb-0.5">{str.title}</strong>
                <span className="text-zinc-400 leading-relaxed">{str.description}</span>
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
  );
};
