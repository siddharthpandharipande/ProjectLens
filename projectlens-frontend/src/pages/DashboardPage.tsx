import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PlusSquare, FolderOpen, ArrowRight, Folder, CheckSquare, ShieldCheck } from 'lucide-react';
import { fetchProjects } from '../services/projectsApi';
import type { Project } from '../types/project';
import StatusBadge from '../components/ui/StatusBadge';
import EmptyState from '../components/ui/EmptyState';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorBanner from '../components/ui/ErrorBanner';

// ─── Helper: format ISO date string ──────────────────────────────────────────
function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString('en-GB', {
      day: 'numeric', month: 'short', year: 'numeric',
    });
  } catch {
    return iso;
  }
}

// ─── Project row ──────────────────────────────────────────────────────────────
function ProjectRow({ project }: { project: Project }) {
  const navigate = useNavigate();
  const iconBg =
    project.status === 'flagged'
      ? 'bg-[#FF5C8D]/20'
      : project.status === 'processing'
      ? 'bg-[#D8B4FE]/30'
      : project.status === 'completed'
      ? 'bg-[#ffe600]'
      : 'bg-[#F2ECE1]';

  return (
    <div
      className="bg-white border-[2.5px] border-[#121212] p-4 hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[6px_6px_0px_#121212] transition-all flex flex-col lg:flex-row lg:items-center justify-between gap-4"
      style={{ boxShadow: '4px 4px 0px #121212' }}
    >
      {/* Left: icon + info */}
      <div className="flex items-center gap-4 min-w-0">
        <div
          className={`w-12 h-12 ${iconBg} border-2 border-[#121212] flex items-center justify-center shrink-0`}
          style={{ boxShadow: '2px 2px 0px #121212' }}
        >
          <Folder size={22} className="text-[#1c1b1b]" />
        </div>
        <div className="flex flex-col gap-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-display font-bold text-base text-[#1c1b1b] truncate">
              {project.title || project.id}
            </span>
            <StatusBadge
              status={project.status}
              stage={project.status === 'processing' ? project.processingStage : undefined}
            />
          </div>
          <div className="flex flex-wrap items-center gap-x-4 font-mono text-[11px] text-[#4b4731]">
            {project.course && <span>{project.course}</span>}
            {project.team && <span>{project.team}</span>}
            {project.score !== undefined && (
              <span className="font-bold text-[#1c1b1b]">Score: {project.score}/100</span>
            )}
            <span>Submitted {formatDate(project.createdAt)}</span>
          </div>
        </div>
      </div>

      {/* Right: action button */}
      <div className="shrink-0 self-end lg:self-center">
        <button
          onClick={() => navigate(`/projects/${project.id}`)}
          className="btn-secondary text-sm px-4 py-2"
        >
          {project.status === 'processing' ? 'View Status' : 'Open Workspace'}
          <ArrowRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ─── Dashboard page ───────────────────────────────────────────────────────────
export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<{ total: number; completed: number } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data.projects ?? []);
      if (data.stats) {
        setStats({
          total: data.stats.totalProjects,
          completed: data.stats.completedProjects,
        });
      } else {
        // Derive simple stats from list
        setStats({
          total: data.projects.length,
          completed: data.projects.filter((p) => p.status === 'completed').length,
        });
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? `Could not reach the backend: ${err.message}. Make sure FastAPI is running at ${import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8001'}.`
          : 'Unknown error connecting to backend.',
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const recent = projects.slice(0, 10);

  return (
    <div className="max-w-[1280px] w-full mx-auto px-5 md:px-10 py-10 flex flex-col gap-8">

      {/* ── Hero banner ── */}
      <section
        className="w-full bg-white border-[2.5px] border-[#121212] p-6 md:p-10 relative overflow-hidden"
        style={{ boxShadow: '5px 5px 0px #121212' }}
      >
        {/* Decorative circle */}
        <div className="absolute -right-12 -top-12 w-48 h-48 bg-[#ffe600]/20 rounded-full border-[2.5px] border-[#121212] pointer-events-none hidden md:block" />

        <div className="flex flex-col items-start gap-4 max-w-4xl relative z-10">
          <div
            className="inline-flex items-center gap-2 bg-[#F2ECE1] text-[#1c1b1b] border-[1.5px] border-[#121212] px-3 py-1"
            style={{ boxShadow: '2px 2px 0px #121212' }}
          >
            <ShieldCheck size={14} />
            <span className="font-mono text-[11px] font-bold uppercase tracking-wider">
              Faculty Evaluation Assistant
            </span>
          </div>

          <h1 className="font-display font-bold text-3xl md:text-5xl text-[#1c1b1b] tracking-tight leading-tight">
            Evaluate student code with{' '}
            <span
              className="bg-[#ffe600] px-2 inline-block border-2 border-[#121212]"
              style={{ boxShadow: '3px 3px 0px #121212' }}
            >
              analytical precision.
            </span>
          </h1>

          <p className="font-sans text-base text-[#4b4731] max-w-2xl leading-relaxed">
            Upload submitted project ZIP files to inspect code health, analyze
            documentation consistency, examine Git timelines, detect similarity signals,
            and generate project-specific viva questions.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-1">
            <Link to="/projects/new" className="btn-primary">
              <PlusSquare size={18} />
              + New Project Evaluation
            </Link>
            <Link to="/history" className="btn-secondary">
              <FolderOpen size={18} />
              Browse Evaluation History
            </Link>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      {!loading && !error && stats && (
        <section className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div
            className="bg-[#ffe600] border-[2.5px] border-[#121212] p-4 flex items-center justify-between min-h-[100px]"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex flex-col gap-0.5">
              <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-[#1c1b1b]">
                Total Submissions
              </span>
              <span className="font-display font-bold text-5xl text-[#1c1b1b] leading-none">
                {stats.total}
              </span>
            </div>
            <div
              className="w-12 h-12 bg-white border-2 border-[#121212] flex items-center justify-center"
              style={{ boxShadow: '2px 2px 0px #121212' }}
            >
              <Folder size={22} className="text-[#1c1b1b]" />
            </div>
          </div>
          <div
            className="bg-white border-[2.5px] border-[#121212] p-4 flex items-center justify-between min-h-[100px]"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex flex-col gap-0.5">
              <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-[#4b4731]">
                Evaluations Completed
              </span>
              <span className="font-display font-bold text-5xl text-[#1c1b1b] leading-none">
                {stats.completed}
              </span>
            </div>
            <div
              className="w-12 h-12 bg-[#ffe600] border-2 border-[#121212] flex items-center justify-center"
              style={{ boxShadow: '2px 2px 0px #121212' }}
            >
              <CheckSquare size={22} className="text-[#1c1b1b]" />
            </div>
          </div>
        </section>
      )}

      {/* ── Recent submissions ── */}
      <section className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b-[2.5px] border-[#121212] pb-3">
          <h2 className="font-display font-bold text-xl text-[#1c1b1b] uppercase tracking-wide">
            Recent Submissions
          </h2>
          {!loading && projects.length > 0 && (
            <Link to="/history" className="font-mono text-[11px] font-bold text-[#4b4731] hover:text-[#1c1b1b] underline">
              View All →
            </Link>
          )}
        </div>

        {loading && <LoadingSpinner message="Fetching projects from backend..." />}

        {!loading && error && (
          <ErrorBanner
            title="Backend not reachable"
            message={error}
            onRetry={load}
          />
        )}

        {!loading && !error && recent.length === 0 && (
          <EmptyState
            title="No projects evaluated yet"
            description="Upload a project ZIP to begin the evaluation pipeline."
            actionLabel="+ Upload Project"
            actionTo="/projects/new"
          />
        )}

        {!loading && !error && recent.length > 0 && (
          <div className="flex flex-col gap-4">
            {recent.map((p) => (
              <ProjectRow key={p.id} project={p} />
            ))}
          </div>
        )}
      </section>

      {/* ── Academic integrity notice ── */}
      <aside
        className="w-full bg-[#F2ECE1] border-2 border-[#121212] p-4 flex items-start gap-4"
        style={{ boxShadow: '3px 3px 0px #121212' }}
      >
        <div
          className="w-8 h-8 rounded-full bg-white border-[1.5px] border-[#121212] flex items-center justify-center shrink-0"
          style={{ boxShadow: '1px 1px 0px #121212' }}
        >
          <ShieldCheck size={16} className="text-[#1c1b1b]" />
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="font-mono text-[11px] font-bold uppercase tracking-widest text-[#1c1b1b]">
            Academic Integrity Notice &amp; Advisory Standard
          </span>
          <p className="font-sans text-sm text-[#4b4731] leading-relaxed">
            ProjectLens is an evaluation assistant. All similarity and AI signals are advisory
            metrics provided for faculty review. Final assessment, grade determination, and
            misconduct adjudication remain the exclusive responsibility of academic evaluators.
          </p>
        </div>
      </aside>
    </div>
  );
}
