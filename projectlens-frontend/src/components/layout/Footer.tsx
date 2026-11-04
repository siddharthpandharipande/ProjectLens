export default function Footer() {
  return (
    <footer className="w-full bg-[#F2ECE1] border-t-[2.5px] border-[#121212] py-4">
      <div className="max-w-[1280px] mx-auto px-5 md:px-10 flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[#1c1b1b]">
            <circle cx="12" cy="12" r="10" /><path d="M12 16v-4M12 8h.01" />
          </svg>
          <p className="font-mono text-[11px] text-[#4b4731]">
            ProjectLens assists faculty evaluation — findings are analytical signals for review, not definitive judgements.
          </p>
        </div>
        <div className="font-mono text-[11px] text-[#4b4731] font-bold">
          © 2025 ProjectLens Faculty Suite
        </div>
      </div>
    </footer>
  );
}
