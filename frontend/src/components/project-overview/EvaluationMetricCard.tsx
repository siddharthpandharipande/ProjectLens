import React from 'react';
import { Clock } from 'lucide-react';

interface EvaluationMetricCardProps {
  title: string;
  score: number | null;
  strokeColor?: string;
}

export const EvaluationMetricCard: React.FC<EvaluationMetricCardProps> = ({
  title,
  score,
  strokeColor = '#3157D5',
}) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-5 flex items-center justify-between">
      <div>
        <h4 className="font-mono text-xs uppercase tracking-wider text-zinc-400 mb-1">
          {title}
        </h4>
        <div className="flex items-baseline gap-2">
          {score !== null ? (
            <span className="font-headline font-bold text-2xl text-white">{score}</span>
          ) : (
            <div className="flex items-center gap-1.5 text-zinc-400 mt-1">
              <Clock className="w-4 h-4 text-zinc-500" />
              <span className="font-mono text-sm text-zinc-400 font-medium">Pending</span>
            </div>
          )}
        </div>
      </div>

      <div className="w-12 h-12 relative flex items-center justify-center">
        {score !== null ? (
          <svg className="w-12 h-12 -rotate-90" viewBox="0 0 36 36">
            <path
              className="text-border"
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
          <div className="w-10 h-10 rounded-full border border-dashed border-border flex items-center justify-center text-[10px] font-mono text-zinc-600">
            N/A
          </div>
        )}
      </div>
    </div>
  );
};
