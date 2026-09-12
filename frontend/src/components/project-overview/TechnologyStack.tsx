import React, { useState, useEffect } from 'react';
import { Technology, TechnologyStack as TechnologyStackType } from '../../types/overview';
import { Layers, X, Sparkles, ShieldCheck, FileCheck, ExternalLink } from 'lucide-react';

interface TechnologyStackProps {
  technologies: TechnologyStackType | Technology[] | undefined | null;
}

export const TechnologyStack: React.FC<TechnologyStackProps> = ({ technologies: rawTechProp }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Normalize incoming tech stack data
  const rawList: Technology[] = Array.isArray(rawTechProp)
    ? rawTechProp
    : rawTechProp?.technologies || [];

  // Deduplicate items by lowercased technology name
  const uniqueTechs = rawList.reduce<Technology[]>((acc, item) => {
    if (!item || !item.name) return acc;
    const exists = acc.some(t => t.name.toLowerCase() === item.name.toLowerCase());
    if (!exists) acc.push(item);
    return acc;
  }, []);

  const totalCount = !Array.isArray(rawTechProp) && rawTechProp?.total_count
    ? rawTechProp.total_count
    : uniqueTechs.length;

  const categoryCount = !Array.isArray(rawTechProp) && rawTechProp?.category_count
    ? rawTechProp.category_count
    : new Set(uniqueTechs.map(t => t.category?.toUpperCase() || 'OTHER')).size;

  // Category Color Dot & Border Map
  const getCategoryDot = (category: string) => {
    const catUpper = category?.toUpperCase() || 'OTHER';
    switch (catUpper) {
      case 'LANGUAGE':
        return 'bg-indigo-400 border-indigo-500/40';
      case 'FRONTEND':
        return 'bg-emerald-400 border-emerald-500/40';
      case 'BACKEND':
        return 'bg-purple-400 border-purple-500/40';
      case 'AI / ML':
      case 'AI/ML':
        return 'bg-pink-400 border-pink-500/40';
      case 'DATABASE':
        return 'bg-amber-400 border-amber-500/40';
      case 'STORAGE':
        return 'bg-cyan-400 border-cyan-500/40';
      case 'INFRASTRUCTURE':
        return 'bg-blue-400 border-blue-500/40';
      case 'TESTING':
        return 'bg-rose-400 border-rose-500/40';
      case 'BUILD / PACKAGE MANAGEMENT':
      case 'BUILD':
        return 'bg-orange-400 border-orange-500/40';
      default:
        return 'bg-zinc-400 border-zinc-500/40';
    }
  };

  const getCategoryLabel = (category: string) => {
    const catUpper = category?.toUpperCase() || 'OTHER';
    switch (catUpper) {
      case 'LANGUAGE': return 'Languages';
      case 'FRONTEND': return 'Frontend';
      case 'BACKEND': return 'Backend';
      case 'AI / ML':
      case 'AI/ML': return 'ML / AI';
      case 'DATABASE': return 'Database';
      case 'STORAGE': return 'Storage';
      case 'INFRASTRUCTURE': return 'Infrastructure';
      case 'TESTING': return 'Testing';
      case 'BUILD / PACKAGE MANAGEMENT': return 'Build & Package';
      default: return category;
    }
  };

  // Group technologies for modal breakdown
  const groupedTechs = uniqueTechs.reduce<Record<string, Technology[]>>((acc, tech) => {
    const cat = tech.category?.toUpperCase() || 'OTHER';
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(tech);
    return acc;
  }, {});

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
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-headline font-bold text-base text-white tracking-wide">
            Technology Stack
          </h3>
          {uniqueTechs.length > 0 && (
            <button
              onClick={() => setIsModalOpen(true)}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-medium flex items-center gap-1 transition-colors"
              title="View full evidence breakdown"
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Details</span>
            </button>
          )}
        </div>

        {/* Compact Badges Grid */}
        {uniqueTechs.length > 0 ? (
          <div className="flex flex-wrap gap-2 mb-4">
            {uniqueTechs.map((tech, idx) => {
              const dotStyle = getCategoryDot(tech.category);
              const evidenceList = Array.isArray(tech.evidence)
                ? tech.evidence
                : [tech.evidence];

              return (
                <div
                  key={idx}
                  className="group relative flex items-center gap-2 py-1.5 px-3 rounded-lg bg-[#0F1014] border border-[#262933] hover:border-zinc-600 transition-all cursor-help"
                >
                  <span className={`w-2 h-2 rounded-full ${dotStyle}`} />
                  <span className="font-mono text-xs font-semibold text-white tracking-tight">
                    {tech.name}
                  </span>

                  {/* Clean Hover Tooltip */}
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-56 p-2.5 rounded-lg bg-[#0D0E12] border border-zinc-700 shadow-2xl text-xs text-zinc-300 pointer-events-none z-30">
                    <div className="flex items-center justify-between mb-1 pb-1 border-b border-zinc-800">
                      <span className="font-mono font-bold text-white text-xs">{tech.name}</span>
                      <span className="text-[10px] text-zinc-400 uppercase font-medium">
                        {getCategoryLabel(tech.category)}
                      </span>
                    </div>

                    <div className="space-y-1 text-[11px] text-zinc-300">
                      {evidenceList.map((ev, eIdx) => (
                        <div key={eIdx} className="flex items-start gap-1 text-[11px]">
                          <span className="text-indigo-400 font-bold">•</span>
                          <span>{ev}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="p-4 rounded-lg border border-dashed border-zinc-800 text-center text-xs text-zinc-500 font-mono mb-4">
            No technologies detected in uploaded project.
          </div>
        )}
      </div>

      {/* Summary Line Footer */}
      {uniqueTechs.length > 0 && (
        <div className="pt-3 border-t border-[#262933] flex items-center justify-between text-xs text-zinc-400 font-medium">
          <div className="flex items-center gap-1.5 text-zinc-400">
            <span className="font-semibold text-white">{totalCount} technologies detected</span>
            <span>·</span>
            <span>{categoryCount} categories</span>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="text-zinc-500 hover:text-white transition-colors"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Detailed Modal Breakdown Popover */}
      {isModalOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-150"
          onClick={() => setIsModalOpen(false)}
        >
          <div
            className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-xl max-h-[80vh] flex flex-col shadow-2xl overflow-hidden"
            onClick={e => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="p-5 border-b border-[#2A2D38] flex items-center justify-between bg-[#13151A]">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-400" />
                  <h2 className="font-headline font-bold text-base text-white">
                    Technology Stack Breakdown
                  </h2>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">
                  {totalCount} technologies detected across {categoryCount} categories.
                </p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="p-1.5 rounded-lg bg-[#21242D] hover:bg-[#2B2F3B] text-zinc-400 hover:text-white transition-colors"
                aria-label="Close modal"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Modal Content / Categories */}
            <div className="p-5 overflow-y-auto space-y-5 max-h-[calc(80vh-120px)]">
              {Object.entries(groupedTechs).map(([categoryName, techs]) => (
                <div key={categoryName} className="space-y-2">
                  <div className="flex items-center gap-2 pb-1 border-b border-zinc-800">
                    <span className={`w-2.5 h-2.5 rounded-full ${getCategoryDot(categoryName)}`} />
                    <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-white">
                      {getCategoryLabel(categoryName)} ({techs.length})
                    </h4>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {techs.map((t, idx) => {
                      const evidenceList = Array.isArray(t.evidence)
                        ? t.evidence
                        : [t.evidence];

                      return (
                        <div
                          key={idx}
                          className="p-3 rounded-lg bg-[#0F1014] border border-[#262933] space-y-1.5"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-mono font-bold text-xs text-white">{t.name}</span>
                            {t.confidence === 'HIGH' ? (
                              <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                                <ShieldCheck className="w-2.5 h-2.5" /> High
                              </span>
                            ) : (
                              <span className="inline-flex items-center gap-1 text-[10px] text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded border border-amber-500/20">
                                <FileCheck className="w-2.5 h-2.5" /> Medium
                              </span>
                            )}
                          </div>

                          <div className="space-y-0.5 text-[11px] text-zinc-400">
                            {evidenceList.map((ev, eIdx) => (
                              <div key={eIdx} className="flex items-start gap-1">
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
              ))}
            </div>

            {/* Modal Footer */}
            <div className="p-3 border-t border-[#2A2D38] bg-[#13151A] flex items-center justify-between text-xs text-zinc-400">
              <span className="text-[11px]">Evidence verified via static AST & manifest scan</span>
              <button
                onClick={() => setIsModalOpen(false)}
                className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
