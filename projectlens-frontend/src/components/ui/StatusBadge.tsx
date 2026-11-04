import type { ProjectStatus } from '../../types/project';

const CONFIG: Record<ProjectStatus, { label: string; bg: string; dot: string }> = {
  pending:    { label: 'Pending',    bg: 'bg-[#F2ECE1]',        dot: 'bg-[#7c775f]' },
  processing: { label: 'Processing', bg: 'bg-[#D8B4FE]',        dot: 'bg-[#1c1b1b] animate-pulse' },
  completed:  { label: 'Completed',  bg: 'bg-[#00E5BE]/30',     dot: 'bg-[#00E5BE]' },
  failed:     { label: 'Failed',     bg: 'bg-[#ffdad6]',        dot: 'bg-[#ba1a1a]' },
  flagged:    { label: 'Needs Review', bg: 'bg-[#ffd9df]',      dot: 'bg-[#b31f56]' },
};

interface StatusBadgeProps {
  status: ProjectStatus;
  stage?: string;
}

export default function StatusBadge({ status, stage }: StatusBadgeProps) {
  const { label, bg, dot } = CONFIG[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 ${bg} border-[1.5px] border-[#121212] font-mono text-[11px] font-bold tracking-widest uppercase shadow-[1.5px_1.5px_0px_#121212]`}
    >
      <span className={`w-2 h-2 rounded-full border border-[#121212] ${dot}`} />
      {stage ?? label}
    </span>
  );
}
