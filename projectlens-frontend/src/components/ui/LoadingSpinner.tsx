interface LoadingSpinnerProps {
  message?: string;
}

export default function LoadingSpinner({ message = 'Loading...' }: LoadingSpinnerProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16">
      <div
        className="w-10 h-10 border-[3px] border-[#121212] border-t-[#ffe600] animate-spin"
        style={{ borderRadius: '50%' }}
        aria-label="Loading"
        role="status"
      />
      <p className="font-mono text-sm text-[#4b4731]">{message}</p>
    </div>
  );
}
