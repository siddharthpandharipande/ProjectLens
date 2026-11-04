import { FolderOpen } from 'lucide-react';
import { Link } from 'react-router-dom';

interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  actionTo?: string;
  onAction?: () => void;
}

export default function EmptyState({
  title = 'No data found',
  description = 'Nothing to display here yet.',
  actionLabel,
  actionTo,
  onAction,
}: EmptyStateProps) {
  return (
    <div
      className="w-full bg-white flex flex-col items-center justify-center text-center gap-4 p-10 border-[3px] border-dashed border-[#121212]"
      style={{ boxShadow: '4px 4px 0px #121212' }}
    >
      <div
        className="w-16 h-16 bg-[#ffe600] flex items-center justify-center border-[2.5px] border-[#121212]"
        style={{ boxShadow: '3px 3px 0px #121212' }}
      >
        <FolderOpen size={32} className="text-[#1c1b1b]" />
      </div>
      <div className="max-w-md flex flex-col gap-1">
        <h3 className="font-display font-bold text-lg text-[#1c1b1b]">{title}</h3>
        <p className="font-sans text-sm text-[#4b4731]">{description}</p>
      </div>
      {actionLabel && (actionTo || onAction) && (
        actionTo ? (
          <Link
            to={actionTo}
            className="btn-primary text-sm"
          >
            {actionLabel}
          </Link>
        ) : (
          <button className="btn-primary text-sm" onClick={onAction}>
            {actionLabel}
          </button>
        )
      )}
    </div>
  );
}
