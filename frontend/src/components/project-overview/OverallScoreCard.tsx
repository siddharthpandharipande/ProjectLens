import React from 'react';
import { Clock } from 'lucide-react';

interface OverallScoreCardProps {
  score: number | null;
}

export const OverallScoreCard: React.FC<OverallScoreCardProps> = ({ score }) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-6 flex flex-col items-center justify-center text-center">
      {score !== null ? (
        <div className="w-32 h-32 rounded-full border-8 border-border border-t-primary flex flex-col items-center justify-center mb-4 relative">
          <span className="font-headline font-bold text-4xl text-white">{score}</span>
          <span className="text-[10px] text-zinc-400 uppercase tracking-wider font-mono">Score</span>
        </div>
      ) : (
        <div className="w-32 h-32 rounded-full border-4 border-dashed border-border flex flex-col items-center justify-center mb-4 text-zinc-500">
          <Clock className="w-8 h-8 text-zinc-500 mb-1" />
          <span className="text-[11px] font-mono font-medium text-zinc-400">Pending</span>
        </div>
      )}

      <span className="px-3 py-1 rounded-full text-xs font-mono font-medium border border-zinc-700 bg-zinc-800/50 text-zinc-300">
        {score !== null ? 'Evaluation Complete' : 'Evaluation Pending'}
      </span>

      <p className="text-[11px] text-zinc-500 mt-3 max-w-[200px]">
        {score !== null
          ? 'Combined evaluation score derived from modular rubrics.'
          : 'Scoring engine module not yet executed for this project.'}
      </p>
    </div>
  );
};
