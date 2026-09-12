import React, { useState, useEffect } from 'react';
import { Technology, TechnologyStack as TechnologyStackType } from '../../types/overview';
import {
  Code2,
  Layers,
  Server,
  Cpu,
  Database,
  HardDrive,
  Box,
  CheckCircle2,
  Wrench,
  FileCode,
  Sparkles,
  X,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  FileCheck
} from 'lucide-react';

interface TechnologyStackProps {
  technologies: TechnologyStackType | Technology[] | undefined | null;
}

export const TechnologyStack: React.FC<TechnologyStackProps> = ({ technologies: rawTechProp }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Normalize incoming tech stack data
  const rawList: Technology[] = Array.isArray(rawTechProp)
    ? rawTechProp
    : rawTechProp?.technologies || [];

  const totalCount = !Array.isArray(rawTechProp) && rawTechProp?.total_count
    ? rawTechProp.total_count
    : rawList.length;

  const categoryCount = !Array.isArray(rawTechProp) && rawTechProp?.category_count
    ? rawTechProp.category_count
    : new Set(rawList.map(t => t.category)).size;

  // Primary display limit: 8 items
  const PRIMARY_LIMIT = 8;
  const displayedTechs = rawList.slice(0, PRIMARY_LIMIT);
  const remainingCount = Math.max(0, rawList.length - PRIMARY_LIMIT);

  // Group technologies by category for the modal drawer
  const groupedTechs = rawList.reduce<Record<string, Technology[]>>((acc, tech) => {
    const cat = tech.category?.toUpperCase() || 'OTHER';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tech);
    return acc;
  }, {});

  // Category Configuration
  const getCategoryConfig = (category: string) => {
    const catUpper = category?.toUpperCase() || 'OTHER';
    switch (catUpper) {
      case 'LANGUAGE':
        return {
          label: 'Language',
          icon: <Code2 className="w-3.5 h-3.5 text-indigo-400" />,
          badgeBg: 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300',
        };
      case 'FRONTEND':
        return {
          label: 'Frontend',
          icon: <Layers className="w-3.5 h-3.5 text-emerald-400" />,
          badgeBg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300',
        };
      case 'BACKEND':
        return {
          label: 'Backend',
          icon: <Server className="w-3.5 h-3.5 text-purple-400" />,
          badgeBg: 'bg-purple-500/10 border-purple-500/30 text-purple-300',
        };
      case 'AI / ML':
      case 'AI/ML':
        return {
          label: 'AI / ML',
          icon: <Cpu className="w-3.5 h-3.5 text-pink-400" />,
          badgeBg: 'bg-pink-500/10 border-pink-500/30 text-pink-300',
        };
      case 'DATABASE':
        return {
          label: 'Database',
          icon: <Database className="w-3.5 h-3.5 text-amber-400" />,
          badgeBg: 'bg-amber-500/10 border-amber-500/30 text-amber-300',
        };
      case 'STORAGE':
        return {
          label: 'Storage',
          icon: <HardDrive className="w-3.5 h-3.5 text-cyan-400" />,
          badgeBg: 'bg-cyan-500/10 border-cyan-500/30 text-cyan-300',
        };
      case 'INFRASTRUCTURE':
        return {
          label: 'Infrastructure',
          icon: <Box className="w-3.5 h-3.5 text-blue-400" />,
          badgeBg: 'bg-blue-500/10 border-blue-500/30 text-blue-300',
        };
      case 'TESTING':
        return {
          label: 'Testing',
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-rose-400" />,
          badgeBg: 'bg-rose-500/10 border-rose-500/30 text-rose-300',
        };
      case 'BUILD / PACKAGE MANAGEMENT':
      case 'BUILD':
      case 'PACKAGE':
        return {
          label: 'Build & Package',
          icon: <Wrench className="w-3.5 h-3.5 text-orange-400" />,
          badgeBg: 'bg-orange-500/10 border-orange-500/30 text-orange-300',
        };
      default:
        return {
          label: category,
          icon: <FileCode className="w-3.5 h-3.5 text-zinc-400" />,
          badgeBg: 'bg-zinc-800 border-zinc-700 text-zinc-400',
        };
    }
  };

  const getConfidenceBadge = (confidence?: 'HIGH' | 'MEDIUM' | 'LOW') => {
    switch (confidence) {
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
            <ShieldCheck className="w-2.5 h-2.5" /> High Confidence
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-500/15 border border-amber-500/30 text-amber-400">
            <FileCheck className="w-2.5 h-2.5" /> Medium Confidence
          </span>
        );
      case 'LOW':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-zinc-700/30 border border-zinc-700 text-zinc-400">
            Inferred
          </span>
        );
    }
  };

  // Close modal on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsModalOpen(false);
    };
    if (isModalOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isModalOpen]);

  return (
    <div className="bg-[#17191F] border border-[#262933] rounded-xl p-6 shadow-md flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <h3 className="font-headline font-bold text-base text-white">
              Technology Stack
            </h3>
          </div>
          {rawList.length > 0 && (
            <span className="text-[11px] font-mono font-medium px-2 py-0.5 rounded bg-[#21242D] text-zinc-400 border border-zinc-800">
              {totalCount} Total
            </span>
          )}
        </div>

        {/* Dynamic summary line */}
        <p className="text-xs text-zinc-400 mb-4">
          {totalCount > 0 ? (
            <span>
              Detected <strong className="text-white">{totalCount} technologies</strong> across{' '}
              <strong className="text-white">{categoryCount} categories</strong> from static code & manifest evidence.
            </span>
          ) : (
            'Technologies and frameworks detected from static code & manifest evidence.'
          )}
        </p>

        {/* Display Primary Technologies */}
        {rawList.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {displayedTechs.map((tech, idx) => {
              const cfg = getCategoryConfig(tech.category);
              const evidenceList = Array.isArray(tech.evidence)
                ? tech.evidence
                : [tech.evidence];

              return (
                <div
                  key={idx}
                  className="group relative flex items-center gap-2 py-1.5 px-3 rounded-lg bg-[#0F1014] border border-[#2A2D38] hover:border-indigo-500/50 transition-all cursor-help"
                >
                  {cfg.icon}
                  <span className="font-mono text-xs font-semibold text-white">{tech.name}</span>
                  <span className={`text-[9px] px-1.5 py-0.2 rounded border font-sans ${cfg.badgeBg}`}>
                    {cfg.label}
                  </span>

                  {/* Rich Floating Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2.5 hidden group-hover:block w-64 p-3 rounded-lg bg-[#0D0E12] border border-zinc-700 shadow-2xl text-xs text-zinc-300 pointer-events-none z-30">
                    <div className="flex items-center justify-between mb-1.5 pb-1.5 border-b border-zinc-800">
                      <span className="font-mono font-bold text-white text-xs">{tech.name}</span>
                      {getConfidenceBadge(tech.confidence)}
                    </div>

                    <div className="space-y-1 text-[11px] text-zinc-300">
                      <div className="text-zinc-400 font-medium text-[10px] uppercase tracking-wider mb-0.5">
                        Evidence Found:
                      </div>
                      {evidenceList.map((ev, eIdx) => (
                        <div key={eIdx} className="flex items-start gap-1.5 text-[11px]">
                          <span className="text-indigo-400 font-bold">•</span>
                          <span>{ev}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* "+ X more" Drawer Toggle Button */}
            {remainingCount > 0 && (
              <button
                onClick={() => setIsModalOpen(true)}
                className="flex items-center gap-1.5 py-1.5 px-3 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 font-mono text-xs font-semibold transition-all group"
              >
                <span>+{remainingCount} more</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </button>
            )}
          </div>
        ) : (
          <div className="p-4 rounded-lg border border-dashed border-zinc-800 text-center text-xs text-zinc-500 font-mono">
            No specific technology manifests or frameworks detected.
          </div>
        )}
      </div>

      {/* Footer link to view full drawer modal */}
      {rawList.length > 0 && (
        <div className="mt-4 pt-3 border-t border-[#262933] flex items-center justify-between text-xs">
          <span className="text-zinc-500 text-[11px]">Categorized AST & Manifest Evidence</span>
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors text-[11px]"
          >
            Full Stack Breakdown <ExternalLink className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Modal Drawer Popover Overlay */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
          <div
            className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-5 border-b border-[#2A2D38] flex items-center justify-between bg-[#13151A]">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  <h2 className="font-headline font-bold text-lg text-white">
                    Complete Technology Stack Evidence
                  </h2>
                </div>
                <p className="text-xs text-zinc-400 mt-1">
                  {totalCount} technologies detected across {categoryCount} categories.
                </p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-2 rounded-lg bg-[#21242D] hover:bg-[#2B2F3B] text-zinc-400 hover:text-white transition-colors"
                aria-label="Close modal"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content / Grouped Categories */}
            <div className="p-6 overflow-y-auto space-y-6 max-h-[calc(85vh-120px)]">
              {Object.entries(groupedTechs).map(([categoryName, techs]) => {
                const cfg = getCategoryConfig(categoryName);

                return (
                  <div key={categoryName} className="space-y-3">
                    <div className="flex items-center gap-2 pb-1.5 border-b border-zinc-800/80">
                      {cfg.icon}
                      <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">
                        {cfg.label} ({techs.length})
                      </h4>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {techs.map((t, idx) => {
                        const evidenceList = Array.isArray(t.evidence)
                          ? t.evidence
                          : [t.evidence];

                        return (
                          <div
                            key={idx}
                            className="p-3 rounded-xl bg-[#0F1014] border border-[#262933] space-y-2 hover:border-zinc-700 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <span className="font-mono font-bold text-sm text-white">{t.name}</span>
                              {getConfidenceBadge(t.confidence)}
                            </div>

                            <div className="space-y-1 text-xs text-zinc-400">
                              {evidenceList.map((ev, eIdx) => (
                                <div key={eIdx} className="flex items-start gap-1.5 text-xs text-zinc-300">
                                  <span className="text-indigo-400 font-bold">•</span>
                                  <span>{ev}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-[#2A2D38] bg-[#13151A] flex items-center justify-between text-xs text-zinc-400">
              <span>Deterministic static code & dependency analysis</span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors"
              >
                Close Breakdown
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
