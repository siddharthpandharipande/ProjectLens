import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorBannerProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export default function ErrorBanner({
  title = 'Something went wrong',
  message,
  onRetry,
}: ErrorBannerProps) {
  return (
    <div
      className="w-full bg-[#ffdad6] border-[2.5px] border-[#121212] p-4 flex items-start gap-3"
      style={{ boxShadow: '3px 3px 0px #121212' }}
      role="alert"
    >
      <AlertTriangle size={20} className="text-[#ba1a1a] shrink-0 mt-0.5" />
      <div className="flex-1 flex flex-col gap-1">
        <strong className="font-display font-bold text-sm text-[#1c1b1b]">{title}</strong>
        <p className="font-sans text-sm text-[#1c1b1b]">{message}</p>
      </div>
      {onRetry && (
        <button
          className="btn-secondary text-sm px-3 py-1.5 shrink-0"
          onClick={onRetry}
          aria-label="Retry"
        >
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}
