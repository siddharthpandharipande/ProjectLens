import { Clock } from 'lucide-react';

interface UnavailablePanelProps {
  featureName: string;
  reason?: string;
}

export default function UnavailablePanel({
  featureName,
  reason = 'This analysis module is not yet implemented on the backend.',
}: UnavailablePanelProps) {
  return (
    <div className="w-full bg-[#F2ECE1] border-[2px] border-[#121212] p-6 flex items-start gap-4">
      <Clock size={24} className="text-[#4b4731] shrink-0 mt-0.5" />
      <div>
        <p className="font-mono text-[11px] font-bold uppercase tracking-widest text-[#4b4731] mb-1">
          NOT AVAILABLE YET
        </p>
        <h4 className="font-display font-bold text-base text-[#1c1b1b] mb-1">{featureName}</h4>
        <p className="font-sans text-sm text-[#4b4731]">{reason}</p>
      </div>
    </div>
  );
}
