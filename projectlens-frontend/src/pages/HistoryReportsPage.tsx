import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { Search, Filter, Download, FolderOpen, ArrowRight } from 'lucide-react';
import { fetchProjects } from '../services/projectsApi';
import { downloadReport } from '../services/analysisApi';
import type { Project, ProjectStatus } from '../types/project';
import StatusBadge from '../components/ui/StatusBadge';
import LoadingSpinner from '../components/ui/LoadingSpinner';
import ErrorBanner from '../components/ui/ErrorBanner';
import EmptyState from '../components/ui/EmptyState';

function formatDate(iso: string) {
  try {
    return new Date(iso).toLocaleDateString('en-GB', { dateStyle: 'medium' });
  } catch { return iso; }
}

const STATUS_FILTERS: { label: string; value: string }[] = [
  { label: 'All', value: 'all' },
  { label: 'Completed', value: 'completed' },
  { label: 'Processing', value: 'processing' },
  { label: 'Flagged', value: 'flagged' },
  { label: 'Failed', value: 'failed' },
  { label: 'Pending', value: 'pending' },
];

export default function HistoryReportsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchProjects();
      setProjects(data.projects ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Filter + search ───────────────────────────────────────────────────────
  const filtered = projects.filter((p) => {
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter;
    const q = search.toLowerCase();
    const matchesSearch =
      !q ||
      (p.title ?? '').toLowerCase().includes(q) ||
      p.id.toLowerCase().includes(q) ||
      (p.course ?? '').toLowerCase().includes(q) ||
      (p.team ?? '').toLowerCase().includes(q);
    return matchesStatus && matchesSearch;
  });

  // ── Aggregated stats ──────────────────────────────────────────────────────
  const statsMap: Record<ProjectStatus, number> = {
    pending: 0, processing: 0, completed: 0, failed: 0, flagged: 0,
  };
  for (const p of projects) statsMap[p.status] = (statsMap[p.status] ?? 0) + 1;

  async function handleDownload(project: Project) {
    setDownloadingId(project.id);
    try {
      await downloadReport(project.id, `${project.title || project.id}_report.pdf`);
    } catch {
      // silently ignore — user can retry from workspace
    } finally {
      setDownloadingId(null);
    }
  }

  return (
    <div className="max-w-[1280px] w-full mx-auto px-5 md:px-10 py-10 flex flex-col gap-8">

      {/* Header */}
      <section
        className="bg-white border-[2.5px] border-[#121212] p-6 md:p-10"
        style={{ boxShadow: '5px 5px 0px #121212' }}
      >
        <div
          className="inline-block bg-[#F2ECE1] text-[#1c1b1b] px-3 py-0.5 font-mono text-[11px] font-bold uppercase tracking-widest mb-3 border-[1.5px] border-[#121212]"
          style={{ boxShadow: '2px 2px 0px #121212' }}
        >
          Longitudinal Records Archive
        </div>
        <h1 className="font-display font-bold text-3xl md:text-4xl text-[#1c1b1b] tracking-tight mb-2">
          History &amp; Evaluation Reports
        </h1>
        <p className="font-sans text-base text-[#4b4731] max-w-2xl">
          Complete archive of all submitted project evaluations. Search, filter by status, and access individual evaluation reports or re-open project workspaces.
        </p>
      </section>

      {/* Stats pills */}
      {!loading && !error && (
        <div className="flex flex-wrap gap-3">
          {STATUS_FILTERS.slice(1).map(({ label, value }) => (
            <div
              key={value}
              className={`flex items-center gap-1.5 px-3 py-1.5 border-[1.5px] border-[#121212] font-mono text-[11px] font-bold cursor-pointer transition-all
                ${statusFilter === value ? 'bg-[#ffe600] shadow-[2px_2px_0px_#121212]' : 'bg-white hover:bg-[#F2ECE1]'}`}
              onClick={() => setStatusFilter(statusFilter === value ? 'all' : value)}
            >
              <span className={`w-2 h-2 rounded-full border border-[#121212] ${
                value === 'completed'  ? 'bg-[#00E5BE]' :
                value === 'processing' ? 'bg-[#D8B4FE]' :
                value === 'flagged'    ? 'bg-[#FF5C8D]' :
                value === 'failed'     ? 'bg-[#ba1a1a]' :
                'bg-[#7c775f]'
              }`} />
              {label}: {statsMap[value as ProjectStatus] ?? 0}
            </div>
          ))}
        </div>
      )}

      {/* Search + filter bar */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4b4731] pointer-events-none" />
          <input
            id="historySearch"
            type="text"
            className="input-field pl-9"
            placeholder="Search by project title, ID, course, or team..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Filter size={16} className="text-[#4b4731] shrink-0" />
          {STATUS_FILTERS.map(({ label, value }) => (
            <button
              key={value}
              className={`font-mono text-[11px] font-bold px-3 py-1.5 border-[1.5px] border-[#121212] transition-all ${
                statusFilter === value ? 'bg-[#ffe600] shadow-[2px_2px_0px_#121212]' : 'bg-white hover:bg-[#F2ECE1]'
              }`}
              onClick={() => setStatusFilter(value)}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      {!loading && (
        <div className="font-mono text-[11px] text-[#4b4731] font-bold">
          Showing {filtered.length} of {projects.length} submission{projects.length !== 1 ? 's' : ''}
          {search && ` matching "${search}"`}
        </div>
      )}

      {/* Content area */}
      {loading && <LoadingSpinner message="Loading evaluation history..." />}

      {!loading && error && (
        <ErrorBanner
          title="Could not load history"
          message={error}
          onRetry={load}
        />
      )}

      {!loading && !error && filtered.length === 0 && (
        <EmptyState
          title={search || statusFilter !== 'all' ? 'No results found' : 'No evaluation history yet'}
          description={
            search || statusFilter !== 'all'
              ? 'Try adjusting your search query or filter settings.'
              : 'Submit a project evaluation to populate this archive.'
          }
          actionLabel={!search && statusFilter === 'all' ? '+ New Evaluation' : undefined}
          actionTo={!search && statusFilter === 'all' ? '/projects/new' : undefined}
        />
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className="flex flex-col gap-4">
          {filtered.map((project) => (
            <div
              key={project.id}
              className="bg-white border-[2.5px] border-[#121212] p-4 flex flex-col lg:flex-row lg:items-center justify-between gap-4 hover:-translate-y-0.5 hover:shadow-[6px_6px_0px_#121212] transition-all"
              style={{ boxShadow: '4px 4px 0px #121212' }}
            >
              {/* Left */}
              <div className="flex items-center gap-4 min-w-0">
                <div
                  className="w-10 h-10 bg-[#F2ECE1] border-2 border-[#121212] flex items-center justify-center shrink-0"
                  style={{ boxShadow: '2px 2px 0px #121212' }}
                >
                  <FolderOpen size={18} className="text-[#1c1b1b]" />
                </div>
                <div className="flex flex-col gap-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-display font-bold text-base text-[#1c1b1b] truncate">
                      {project.title || project.id}
                    </span>
                    <StatusBadge status={project.status} />
                  </div>
                  <div className="flex flex-wrap items-center gap-x-4 font-mono text-[11px] text-[#4b4731]">
                    <span>#{project.id}</span>
                    {project.course && <span className="font-bold text-[#1c1b1b]">{project.course}</span>}
                    {project.team && <span>{project.team}</span>}
                    {project.score !== undefined && (
                      <span className="font-bold text-[#1c1b1b] bg-[#ffe600] px-1 border border-[#121212]">
                        Score: {project.score}/100
                      </span>
                    )}
                    <span>Submitted {formatDate(project.createdAt)}</span>
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex flex-wrap items-center gap-2 shrink-0">
                {project.status === 'completed' && (
                  <button
                    className="btn-secondary text-sm px-3 py-1.5"
                    onClick={() => handleDownload(project)}
                    disabled={downloadingId === project.id}
                    title="Download PDF Report"
                  >
                    {downloadingId === project.id ? (
                      <span className="w-4 h-4 border-2 border-[#121212] border-t-transparent animate-spin" style={{ borderRadius: '50%' }} />
                    ) : (
                      <Download size={14} />
                    )}
                    Download PDF
                  </button>
                )}
                <Link
                  to={`/projects/${project.id}`}
                  className="btn-secondary text-sm px-3 py-1.5"
                >
                  Open Workspace
                  <ArrowRight size={14} />
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
