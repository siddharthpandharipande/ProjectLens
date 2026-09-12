import React from 'react';
import { CodeMetrics } from '../../types/overview';

interface CodeAnalyticsProps {
  metrics: CodeMetrics;
}

export const CodeAnalytics: React.FC<CodeAnalyticsProps> = ({ metrics }) => {
  return (
    <div className="bg-bg-card border border-border rounded-xl p-6">
      <h3 className="font-headline font-bold text-base text-white mb-2">
        Code Analytics
      </h3>
      <p className="text-xs text-zinc-400 mb-6">
        Deterministic metrics calculated directly from parsed project files.
      </p>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 divide-x-0 sm:divide-x divide-border">
        {/* LOC */}
        <div className="text-center sm:px-2">
          <div className="font-headline font-bold text-2xl text-white mb-1">
            {metrics.loc.toLocaleString()}
          </div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            LOC
          </div>
          <div className="text-[10px] text-zinc-500 mt-1 font-mono">
            {metrics.code_lines.toLocaleString()} Code / {metrics.comment_lines.toLocaleString()} Comments
          </div>
        </div>

        {/* Avg Complexity */}
        <div className="text-center sm:px-2">
          <div className="font-headline font-bold text-2xl text-white mb-1">
            {metrics.average_complexity}
          </div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            Avg Complexity
          </div>
          <div className="text-[10px] text-zinc-500 mt-1 font-mono">
            Max: {metrics.maximum_complexity}
          </div>
        </div>

        {/* Test Coverage */}
        <div className="text-center sm:px-2">
          <div className="font-headline font-bold text-xl text-zinc-300 mb-1">
            {metrics.test_coverage}
          </div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            Test Coverage
          </div>
          <div className="text-[10px] text-zinc-500 mt-1 font-mono">
            No coverage report detected
          </div>
        </div>

        {/* AI Assistance */}
        <div className="text-center sm:px-2">
          <div className="font-headline font-bold text-xl text-zinc-400 mb-1">
            {metrics.ai_assistance}
          </div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-400">
            AI Assistance
          </div>
          <div className="text-[10px] text-zinc-500 mt-1 font-mono">
            Requires AI Signals module
          </div>
        </div>
      </div>
    </div>
  );
};
