import { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, PlusSquare, History, Menu, X } from 'lucide-react';
import { checkHealth } from '../../services/projectsApi';

export default function Navbar() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Poll backend health every 30 seconds
  useEffect(() => {
    let cancelled = false;

    const ping = async () => {
      const ok = await checkHealth();
      if (!cancelled) setBackendOnline(ok);
    };

    ping();
    const interval = setInterval(ping, 30_000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-bold font-display border-2 transition-all ${
      isActive
        ? 'bg-[#ffe600] border-[#121212] shadow-[2px_2px_0px_#121212] text-[#1c1b1b]'
        : 'border-transparent text-[#4b4731] hover:text-[#1c1b1b] hover:bg-[#F2ECE1]'
    }`;

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50 bg-white border-b-[2.5px] border-[#121212]"
      style={{ boxShadow: '0 4px 0 #121212' }}
    >
      <div className="h-20 max-w-[1280px] mx-auto px-5 md:px-10 flex items-center justify-between gap-6">
        {/* Logo + Brand */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-[#ffe600] border-2 border-[#121212] shadow-[2px_2px_0px_#121212] flex items-center justify-center font-bold font-display text-sm">
              PL
            </div>
            <span className="font-display font-bold text-xl tracking-tight text-[#1c1b1b]">
              ProjectLens
            </span>
            <span className="hidden lg:inline-block font-mono text-[11px] font-bold bg-[#F2ECE1] text-[#1c1b1b] px-2 py-0.5 border-[1.5px] border-[#121212] shadow-[2px_2px_0px_#121212] uppercase tracking-widest">
              Faculty Assistant v1.0
            </span>
          </div>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-1 ml-4" aria-label="Main navigation">
            <NavLink to="/" end className={navLinkClass}>
              <LayoutDashboard size={15} />
              Dashboard
            </NavLink>
            <NavLink to="/projects/new" className={navLinkClass}>
              <PlusSquare size={15} />
              New Evaluation
            </NavLink>
            <NavLink to="/history" className={navLinkClass}>
              <History size={15} />
              History &amp; Reports
            </NavLink>
          </nav>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {/* Backend status pill */}
          <div
            className="hidden sm:flex items-center gap-1.5 bg-white border-[1.5px] border-[#121212] px-2.5 py-1 rounded-full shadow-[2px_2px_0px_#121212]"
            title={backendOnline === null ? 'Checking...' : backendOnline ? 'Backend connected' : 'Backend offline'}
          >
            <span
              className={`w-2.5 h-2.5 rounded-full border border-[#121212] ${
                backendOnline === null
                  ? 'bg-[#F2ECE1] animate-pulse'
                  : backendOnline
                  ? 'bg-[#00E5BE]'
                  : 'bg-[#FF5C8D]'
              }`}
            />
            <span className="font-mono text-[11px] font-bold text-[#1c1b1b]">
              {backendOnline === null
                ? 'Checking...'
                : backendOnline
                ? 'FastAPI: Connected'
                : 'FastAPI: Offline'}
            </span>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden w-9 h-9 flex items-center justify-center border-2 border-[#121212] bg-white shadow-[2px_2px_0px_#121212] hover:bg-[#F2ECE1] transition-colors"
            aria-label="Toggle menu"
            onClick={() => setMobileOpen((v) => !v)}
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden bg-white border-t-2 border-[#121212] px-5 py-4 flex flex-col gap-2">
          <NavLink to="/" end className={navLinkClass}>
            <LayoutDashboard size={15} />
            Dashboard
          </NavLink>
          <NavLink to="/projects/new" className={navLinkClass}>
            <PlusSquare size={15} />
            New Evaluation
          </NavLink>
          <NavLink to="/history" className={navLinkClass}>
            <History size={15} />
            History &amp; Reports
          </NavLink>
        </div>
      )}
    </header>
  );
}
