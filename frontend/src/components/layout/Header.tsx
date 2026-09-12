import React from 'react';
import { Search, RotateCw, User } from 'lucide-react';

interface HeaderProps {
  projectName?: string;
  studentName?: string;
  course?: string;
  isReanalyzing?: boolean;
  onReanalyze?: () => void;
  onOpenUpload?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  projectName = 'Smart Attendance System',
  studentName = 'Alex Chen',
  course = 'CS499 Final Project',
  isReanalyzing = false,
  onReanalyze,
  onOpenUpload,
}) => {
  return (
    <header className="h-[70px] border-b border-border bg-bg-main/80 backdrop-blur-md px-8 flex items-center justify-between sticky top-0 z-30">
      {/* Title Area */}
      <div className="flex items-baseline gap-4">
        <h1 className="font-headline font-bold text-xl text-white tracking-tight">
          {projectName}
        </h1>
        <span className="text-sm text-zinc-400 font-body">
          Submitted by <strong className="text-white font-medium">{studentName}</strong> &bull; {course}
        </span>
      </div>

      {/* Header Actions */}
      <div className="flex items-center gap-4">
        {/* Re-Analyze Button */}
        {onReanalyze && (
          <button
            onClick={onReanalyze}
            disabled={isReanalyzing}
            className="flex items-center gap-2 py-2 px-4 rounded-md bg-bg-card border border-border text-white text-xs font-semibold hover:bg-bg-cardHover hover:border-border-active transition-all disabled:opacity-50"
          >
            <RotateCw className={`w-3.5 h-3.5 text-primary ${isReanalyzing ? 'animate-spin' : ''}`} />
            {isReanalyzing ? 'Analyzing...' : 'Re-Analyze'}
          </button>
        )}

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search metrics..."
            className="w-52 py-1.5 pl-9 pr-3 bg-bg-card border border-border rounded-md text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-border-active focus:w-64 transition-all"
          />
        </div>

        {/* Profile */}
        <div className="flex items-center gap-2 pl-2 border-l border-border">
          <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-white text-xs font-bold font-mono">
            {studentName.split(' ').map(n => n[0]).join('')}
          </div>
        </div>
      </div>
    </header>
  );
};
