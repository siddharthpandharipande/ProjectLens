import React from 'react';
import {
  LayoutDashboard,
  Activity,
  Dna,
  Mic,
  FileText,
  Users,
  Palette,
  PlusCircle,
  ShieldCheck,
} from 'lucide-react';

interface SidebarProps {
  onOpenUpload: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onOpenUpload }) => {
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
        {/* Student Module */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Student Module
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

            {/* Pluggable modules explicitly marked as coming soon / disabled */}
            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
                title="AI Signals module will plug in here"
              >
                <div className="flex items-center gap-3">
                  <Activity className="w-4 h-4" />
                  AI Signals
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">Soon</span>
              </button>
            </li>

            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
                title="Innovation DNA module will plug in here"
              >
                <div className="flex items-center gap-3">
                  <Dna className="w-4 h-4" />
                  Innovation DNA
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">Soon</span>
              </button>
            </li>

            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
                title="Viva Voice Q&A module will plug in here"
              >
                <div className="flex items-center gap-3">
                  <Mic className="w-4 h-4" />
                  Viva Voice Q&A
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">Soon</span>
              </button>
            </li>

            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
                title="Final Evaluation module will plug in here"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-4 h-4" />
                  Final Evaluation
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">Soon</span>
              </button>
            </li>
          </ul>
        </div>

        {/* Faculty Module */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Faculty Module
          </div>
          <ul className="space-y-1">
            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
              >
                <div className="flex items-center gap-3">
                  <Users className="w-4 h-4" />
                  Faculty Dashboard
                </div>
                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">Soon</span>
              </button>
            </li>
          </ul>
        </div>

        {/* Utilities */}
        <div>
          <div className="font-mono text-[11px] uppercase tracking-wider text-zinc-500 px-3 mb-2 font-medium">
            Utilities
          </div>
          <ul className="space-y-1">
            <li>
              <button
                disabled
                className="w-full flex items-center justify-between px-3 py-2 rounded-md text-zinc-500 text-sm font-medium cursor-not-allowed opacity-60 hover:bg-transparent"
              >
                <div className="flex items-center gap-3">
                  <Palette className="w-4 h-4" />
                  Style Guide
                </div>
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
