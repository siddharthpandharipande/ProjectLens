import React from 'react';
import { Technology } from '../../types/overview';
import { Layers, Code2, Database, Wrench } from 'lucide-react';

interface TechnologyStackProps {
  technologies: Technology[];
}

export const TechnologyStack: React.FC<TechnologyStackProps> = ({ technologies }) => {
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'language':
        return <Code2 className="w-3.5 h-3.5 text-primary" />;
      case 'framework':
        return <Layers className="w-3.5 h-3.5 text-secondary" />;
      case 'database':
        return <Database className="w-3.5 h-3.5 text-status-yellow" />;
      default:
        return <Wrench className="w-3.5 h-3.5 text-zinc-400" />;
    }
  };

  return (
    <div className="bg-bg-card border border-border rounded-xl p-6">
      <h3 className="font-headline font-bold text-base text-white mb-2">
        Technology Stack
      </h3>
      <p className="text-xs text-zinc-400 mb-4">
        Technologies and frameworks detected from static AST code evidence.
      </p>

      {technologies.length > 0 ? (
        <div className="flex flex-wrap gap-2.5">
          {technologies.map((tech, idx) => (
            <div
              key={idx}
              className="group relative flex items-center gap-2 py-1.5 px-3 rounded-md bg-bg-main border border-border hover:border-border-active transition-all cursor-help"
            >
              {getCategoryIcon(tech.category)}
              <span className="font-mono text-xs font-medium text-white">{tech.name}</span>
              <span className="text-[10px] text-zinc-500 capitalize">({tech.category})</span>

              {/* Hover Tooltip showing evidence */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block w-48 p-2 rounded bg-zinc-900 border border-zinc-700 shadow-xl text-[10px] text-zinc-300 pointer-events-none z-20">
                <span className="font-bold text-white block mb-0.5">{tech.name} Evidence:</span>
                <span>{tech.evidence}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="p-4 rounded border border-dashed border-border text-center text-xs text-zinc-500 font-mono">
          No specific technology manifests or frameworks detected.
        </div>
      )}
    </div>
  );
};
