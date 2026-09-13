import React from 'react';
import {
  LayoutDashboard,
  Code2,
  GitCompare,
  FileCheck,
  Clock,
  Cpu,
  Sparkles,
  Mic,
  ShieldCheck,
  FileText,
  PlusCircle
} from 'lucide-react';

interface SidebarProps {
  onOpenUpload: () => void;
  onSelectFutureModule: (moduleId: string) => void;
  onOpenCodeQuality?: () => void;
  onOpenSimilarity?: () => void;
  onOpenDocumentation?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  onOpenUpload,
  onSelectFutureModule,
  onOpenCodeQuality,
  onOpenSimilarity,
  onOpenDocumentation
}) => {
  return (
    <aside className="w-[280px] bg-bg-sidebar border-r border-border flex flex-col p-4 shrink-0 h-screen sticky top-0">
      {/* Brand Logo */}
      <div className="flex items-center gap-3 px-3 py-4 mb-4 border-b border-border">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-white shadow-md shadow-primary/20">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div className="flex flex-col">
          <span className="font-headline font-bold text-lg leading-tight tracking-tight text-white">ProjectLens</span>
          <span className="font-mono text-[10px] text-zinc-400 uppercase tracking-widest">Academic Suite</span>
        </div>
      </div>

      {/* New Analysis Action */}
      <button
        onClick={onOpenUpload}
        className="w-full mb-6 flex items-center justify-center gap-2 py-2.5 px-4 rounded-md bg-primary/10 border border-primary/40 text-primary font-semibold text-sm hover:bg-primary/20 transition-all duration-200"
      >
        <PlusCircle className="w-4 h-4 text-primary" />
        New Analysis
      </button>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-1">
        {/* Overview Section */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Overview
          </div>
          <ul className="space-y-1">
            <li>
              <button
                className="w-full flex items-center gap-3 px-3 py-2 rounded-md bg-primary text-white text-sm font-medium shadow-sm transition-all"
              >
                <LayoutDashboard className="w-4 h-4 text-white" />
                Project Overview
              </button>
            </li>
          </ul>
        </div>

        {/* Analysis Section */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Analysis
          </div>
          <ul className="space-y-1">
            {/* Active Analysis Modules */}
            <li>
              <button
                onClick={onOpenCodeQuality}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-300 hover:text-white text-sm font-medium hover:bg-[#1E212B] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Code2 className="w-4 h-4 text-indigo-400" />
                  Code Quality
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                  Active
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={onOpenSimilarity}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-300 hover:text-white text-sm font-medium hover:bg-[#1E212B] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <GitCompare className="w-4 h-4 text-amber-400" />
                  Code Similarity
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                  Active
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={onOpenDocumentation}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-300 hover:text-white text-sm font-medium hover:bg-[#1E212B] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileCheck className="w-4 h-4 text-emerald-400" />
                  Documentation
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                  Active
                </span>
              </button>
            </li>

            {/* Future Modules */}
            <li>
              <button
                onClick={() => onSelectFutureModule('git')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="Git Development Analysis (Phase 6)"
              >
                <div className="flex items-center gap-3">
                  <Clock className="w-4 h-4 text-zinc-500 group-hover:text-amber-400 transition-colors" />
                  Git Development
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 6
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={() => onSelectFutureModule('ai_assistance')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="AI Assistance Signals (Phase 7)"
              >
                <div className="flex items-center gap-3">
                  <Cpu className="w-4 h-4 text-zinc-500 group-hover:text-purple-400 transition-colors" />
                  AI Assistance
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 7
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={() => onSelectFutureModule('innovation')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="Innovation DNA Engine (Phase 8)"
              >
                <div className="flex items-center gap-3">
                  <Sparkles className="w-4 h-4 text-zinc-500 group-hover:text-cyan-400 transition-colors" />
                  Innovation DNA
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 8
                </span>
              </button>
            </li>
          </ul>
        </div>

        {/* Assessment Section */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Assessment
          </div>
          <ul className="space-y-1">
            <li>
              <button
                onClick={() => onSelectFutureModule('viva')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="Viva Voice Q&A (Phase 9)"
              >
                <div className="flex items-center gap-3">
                  <Mic className="w-4 h-4 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
                  Viva Voice Q&A
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 9
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={() => onSelectFutureModule('final_eval')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="Final Evaluation Engine (Phase 10)"
              >
                <div className="flex items-center gap-3">
                  <ShieldCheck className="w-4 h-4 text-zinc-500 group-hover:text-emerald-400 transition-colors" />
                  Final Evaluation
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 10
                </span>
              </button>
            </li>

            <li>
              <button
                onClick={() => onSelectFutureModule('final_report')}
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-400 hover:text-zinc-200 text-sm font-medium hover:bg-[#1C1F28] transition-colors group"
                title="Final Report Generator (Phase 11)"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4 text-zinc-500 group-hover:text-blue-400 transition-colors" />
                  Final Report
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  Phase 11
                </span>
              </button>
            </li>
          </ul>
        </div>
      </div>

      {/* Footer Info */}
      <div className="mt-auto pt-4 border-t border-border px-3 text-[11px] text-zinc-500 font-mono">
        v2.4 &bull; Deterministic Core Engine
      </div>
    </aside>
  );
};
