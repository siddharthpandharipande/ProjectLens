import { useState, useRef, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Archive, Badge, Sliders, CheckSquare, ArrowRight,
  RefreshCw, Upload, X, Lock, HelpCircle,
} from 'lucide-react';
import { uploadProject } from '../services/projectsApi';
import { ApiError } from '../services/apiClient';
import ErrorBanner from '../components/ui/ErrorBanner';

const MAX_FILE_SIZE_MB = 50;

// ─── Analysis module choices (shown to user, sent to backend) ────────────────
const MODULES = [
  { id: 'code_quality',   label: 'Code Quality & Structure',         desc: 'Evaluates code clarity, maintainability, and architectural complexity.' },
  { id: 'similarity',     label: 'Similarity & Originality Check',   desc: 'Checks source files against current and previous semester submissions.' },
  { id: 'documentation',  label: 'Documentation Verification',       desc: 'Cross-checks README/SRS setup guides against actual codebase.' },
  { id: 'git_history',    label: 'Git History & Collaboration Flow',  desc: 'Reviews commit logs and author distribution if Git bundle is present.' },
  { id: 'ai_assistance',  label: 'AI Generation Patterns',           desc: 'Highlights boilerplates and large multi-file code diffs.' },
  { id: 'viva',           label: 'Suggested Viva Voce Questions',     desc: 'Generates defense questions targeting tricky implementation decisions.' },
];

export default function NewEvaluationPage() {
  const navigate = useNavigate();

  // Form state
  const [file, setFile] = useState<File | null>(null);
  const [course, setCourse] = useState('');
  const [title, setTitle] = useState('');
  const [modules, setModules] = useState<Record<string, boolean>>(
    Object.fromEntries(MODULES.map((m) => [m.id, true])),
  );
  const [dragging, setDragging] = useState(false);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── File handling ─────────────────────────────────────────────────────────
  function validateAndSetFile(f: File) {
    if (!f.name.endsWith('.zip')) {
      setSubmitError('Only .zip files are accepted. Please select a ZIP archive.');
      return;
    }
    if (f.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
      setSubmitError(`File is too large. Maximum allowed size is ${MAX_FILE_SIZE_MB} MB.`);
      return;
    }
    setSubmitError(null);
    setFile(f);
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) validateAndSetFile(dropped);
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) validateAndSetFile(selected);
  }, []);

  // ── Submit ────────────────────────────────────────────────────────────────
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!file) { setSubmitError('Please select a ZIP file before submitting.'); return; }

    setSubmitting(true);
    setSubmitError(null);

    try {
      const response = await uploadProject({ file, course: course || undefined, title: title || undefined });
      navigate(`/projects/${response.projectId}`);
    } catch (err) {
      if (err instanceof ApiError) {
        let message = err.message;
        if (typeof err.detail === 'object' && err.detail !== null && 'detail' in err.detail) {
          message = String((err.detail as Record<string, unknown>).detail);
        } else if (typeof err.detail === 'string' && err.detail) {
          message = err.detail;
        }
        setSubmitError(`Upload error (HTTP ${err.status}): ${message}`);
      } else if (err instanceof TypeError) {
        setSubmitError('Upload request failed: network or connection error. Make sure FastAPI is reachable.');
      } else {
        setSubmitError(err instanceof Error ? err.message : 'Upload failed. Please try again.');
      }
      setSubmitting(false);
    }
  }

  const toggleModule = (id: string) => setModules((prev) => ({ ...prev, [id]: !prev[id] }));
  const setAll = (val: boolean) => setModules(Object.fromEntries(MODULES.map((m) => [m.id, val])));

  return (
    <div className="max-w-[1280px] w-full mx-auto px-5 md:px-10 py-10">

      {/* Breadcrumb */}
      <nav className="flex items-center gap-2 font-mono text-[11px] text-[#4b4731] mb-4">
        <Link to="/" className="hover:text-[#1c1b1b] hover:underline">Dashboard</Link>
        <span className="text-[#7c775f]">/</span>
        <span
          className="bg-[#F2ECE1] text-[#1c1b1b] font-bold px-2 py-0.5 border-[1.5px] border-[#121212]"
          style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
        >
          New Evaluation
        </span>
      </nav>

      {/* Header block */}
      <div
        className="bg-white p-6 md:p-10 border-[2.5px] border-[#121212] mb-8"
        style={{ boxShadow: '4px 4px 0px #121212' }}
      >
        <div
          className="inline-block bg-[#ffe600] text-[#1c1b1b] px-3 py-0.5 font-mono text-[11px] font-bold uppercase tracking-wider mb-3 border-[1.5px] border-[#121212]"
          style={{ boxShadow: '2px 2px 0px #121212' }}
        >
          Submission Ingestion Intake
        </div>
        <h1 className="font-display font-bold text-3xl md:text-4xl text-[#1c1b1b] tracking-tight mb-2">
          Submit Project Archive for Analysis
        </h1>
        <p className="font-sans text-base text-[#4b4731] max-w-2xl leading-relaxed">
          Upload a student submission ZIP file to trigger automated codebase decomposition,
          documentation consistency checking, cross-cohort similarity scanning, and viva question synthesis.
        </p>
      </div>

      {/* Error banner */}
      {submitError && (
        <div className="mb-6">
          <ErrorBanner message={submitError} onRetry={() => setSubmitError(null)} />
        </div>
      )}

      {/* Form */}
      <form
        id="evaluationUploadForm"
        onSubmit={handleSubmit}
        className="grid grid-cols-1 lg:grid-cols-12 gap-8"
      >
        {/* ── Left column (8 cols): upload zone + metadata ── */}
        <div className="lg:col-span-8 flex flex-col gap-8">

          {/* Drop zone card */}
          <div
            className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            {/* Card header */}
            <div className="flex items-center justify-between bg-[#F2ECE1] border-b-2 border-[#121212] px-6 py-3">
              <div className="flex items-center gap-2">
                <Archive size={18} className="text-[#1c1b1b]" />
                <span className="font-display font-bold uppercase tracking-wide text-sm">01. Codebase Archive (.ZIP)</span>
              </div>
              <span
                className="font-mono text-[10px] font-bold bg-[#ffe600] px-2 py-0.5 border-[1.5px] border-[#121212]"
                style={{ boxShadow: '1.5px 1.5px 0px #121212' }}
              >
                FASTAPI MULTIPART
              </span>
            </div>

            {/* Drop area */}
            <div className="p-6">
              <div
                className={`relative cursor-pointer border-[2.5px] border-dashed ${dragging ? 'bg-[#ffe600]/20 border-[#121212]' : 'bg-[#FAF6EE] border-[#121212]'} p-8 md:p-12 text-center transition-colors`}
                style={{ boxShadow: dragging ? '6px 6px 0px #ffe600' : '6px 6px 0px #121212' }}
                onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                onDragLeave={() => setDragging(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                {/* Corner decorators */}
                <div className="absolute -top-[3px] -left-[3px] w-4 h-4 bg-[#121212]" />
                <div className="absolute -top-[3px] -right-[3px] w-4 h-4 bg-[#121212]" />
                <div className="absolute -bottom-[3px] -left-[3px] w-4 h-4 bg-[#121212]" />
                <div className="absolute -bottom-[3px] -right-[3px] w-4 h-4 bg-[#121212]" />

                <input
                  ref={fileInputRef}
                  id="zipFileInput"
                  type="file"
                  accept=".zip"
                  className="hidden"
                  onChange={handleFileChange}
                />

                {file ? (
                  <div
                    className="bg-white border border-[#121212] p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-left"
                    style={{ boxShadow: '3px 3px 0px #121212' }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-9 h-9 bg-[#00E5BE] flex items-center justify-center border border-[#121212]"
                        style={{ boxShadow: '2px 2px 0px #121212' }}
                      >
                        <CheckSquare size={18} className="text-[#1c1b1b]" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-bold text-[#1c1b1b]">{file.name}</span>
                          <span
                            className="bg-[#00E5BE] text-[#1c1b1b] font-mono text-[10px] font-bold px-1.5 py-0.5 border border-[#121212]"
                            style={{ boxShadow: '1px 1px 0px #121212' }}
                          >
                            STAGED
                          </span>
                        </div>
                        <span className="font-mono text-[11px] text-[#4b4731]">
                          {(file.size / (1024 * 1024)).toFixed(1)} MB • Ready for multipart streaming
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="font-mono text-[11px] font-bold bg-[#F2ECE1] hover:bg-[#ffe600] px-3 py-1 border border-[#121212]"
                        style={{ boxShadow: '2px 2px 0px #121212' }}
                        onClick={() => fileInputRef.current?.click()}
                      >
                        Change File
                      </button>
                      <button
                        type="button"
                        className="w-7 h-7 flex items-center justify-center bg-[#ffd9df] hover:bg-[#FF5C8D] border border-[#121212]"
                        style={{ boxShadow: '2px 2px 0px #121212' }}
                        title="Remove file"
                        onClick={() => setFile(null)}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center gap-4">
                    <div
                      className="w-16 h-16 bg-[#ffe600] flex items-center justify-center border-2 border-[#121212]"
                      style={{ boxShadow: '4px 4px 0px #121212' }}
                    >
                      <Upload size={28} className="text-[#1c1b1b]" />
                    </div>
                    <div>
                      <h2 className="font-display font-bold text-base text-[#1c1b1b] mb-1">
                        Drag &amp; drop project archive (.ZIP), or click to browse
                      </h2>
                      <p className="font-sans text-sm text-[#4b4731]">
                        Accepted format: <strong>.ZIP only</strong> • Max size:{' '}
                        <strong>{MAX_FILE_SIZE_MB} MB</strong>
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Sandbox note */}
              <div className="mt-4 bg-[#F2ECE1] p-4 flex items-start gap-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
                <Lock size={18} className="text-[#1c1b1b] shrink-0 mt-0.5" />
                <p className="font-sans text-sm text-[#4b4731]">
                  <strong className="text-[#1c1b1b]">Zero Host Execution Sandbox:</strong>{' '}
                  Code is analyzed in an isolated container. No uploaded student scripts are compiled
                  or executed in the browser runtime or on host evaluation shells.
                </p>
              </div>
            </div>
          </div>

          {/* Metadata card */}
          <div
            className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex items-center justify-between bg-[#F2ECE1] border-b-2 border-[#121212] px-6 py-3">
              <div className="flex items-center gap-2">
                <Badge size={18} className="text-[#1c1b1b]" />
                <span className="font-display font-bold uppercase tracking-wide text-sm">02. Submission Metadata</span>
              </div>
              <span className="font-mono text-[10px] font-bold text-[#4b4731]">OPTIONAL</span>
            </div>
            <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label htmlFor="courseModule" className="block font-display font-bold text-sm text-[#1c1b1b] mb-1">
                  Course &amp; Section Code
                </label>
                <input
                  id="courseModule"
                  type="text"
                  className="input-field"
                  placeholder="e.g. CS-402 (Section A)"
                  value={course}
                  onChange={(e) => setCourse(e.target.value)}
                />
                <span className="font-mono text-[11px] text-[#4b4731] block mt-1">
                  Associates evaluation with course roster and rubric.
                </span>
              </div>
              <div>
                <label htmlFor="projectTitle" className="block font-display font-bold text-sm text-[#1c1b1b] mb-1">
                  Project Title{' '}
                  <span className="font-sans font-normal text-[#4b4731] text-xs">(Recommended)</span>
                </label>
                <input
                  id="projectTitle"
                  type="text"
                  className="input-field"
                  placeholder="e.g. Autonomous Drone Navigation System"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                />
                <span className="font-mono text-[11px] text-[#4b4731] block mt-1">
                  Defaults to root folder name if left blank.
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right column (4 cols): analysis scope + submit ── */}
        <div className="lg:col-span-4 flex flex-col gap-8">

          {/* Analysis scope */}
          <div
            className="bg-white border-[2.5px] border-[#121212] overflow-hidden"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <div className="flex items-center justify-between bg-[#ffe600] border-b-2 border-[#121212] px-4 py-3">
              <div className="flex items-center gap-2">
                <Sliders size={16} className="text-[#1c1b1b]" />
                <span className="font-display font-bold uppercase tracking-wide text-sm">Analysis Scope</span>
              </div>
              <span
                className="font-mono text-[10px] font-bold bg-white px-2 py-0.5 border-[1.5px] border-[#121212]"
                style={{ boxShadow: '1px 1px 0px #121212' }}
              >
                {Object.values(modules).filter(Boolean).length}/{MODULES.length} ACTIVE
              </span>
            </div>
            <div className="p-4">
              <p className="font-sans text-sm text-[#4b4731] mb-3">
                Select which analysis pipelines to run on this submission:
              </p>
              <div className="flex flex-col gap-2">
                {MODULES.map((m) => (
                  <label
                    key={m.id}
                    className="flex items-start gap-3 p-3 bg-[#FAF6EE] hover:bg-[#F2ECE1] cursor-pointer transition-colors border border-[#121212]"
                    style={{ boxShadow: '2px 2px 0px #121212' }}
                  >
                    <input
                      type="checkbox"
                      className="mt-0.5 w-4 h-4 accent-[#121212] cursor-pointer"
                      checked={modules[m.id]}
                      onChange={() => toggleModule(m.id)}
                    />
                    <div className="flex-1">
                      <span className="font-display font-bold text-sm text-[#1c1b1b] block leading-tight">
                        {m.label}
                      </span>
                      <span className="font-mono text-[10px] text-[#4b4731]">{m.desc}</span>
                    </div>
                  </label>
                ))}
              </div>
              {/* Presets */}
              <div className="mt-3 pt-3 border-t border-[#121212] flex items-center justify-between">
                <span className="font-mono text-[11px] font-bold text-[#4b4731]">PRESETS:</span>
                <div className="flex items-center gap-2 font-mono text-[11px]">
                  <button type="button" className="underline hover:text-[#1c1b1b] text-[#4b4731]" onClick={() => setAll(true)}>All (Full)</button>
                  <span className="text-[#4b4731]">/</span>
                  <button type="button" className="underline hover:text-[#1c1b1b] text-[#4b4731]" onClick={() => {
                    setModules({ code_quality: true, similarity: false, documentation: true, git_history: false, ai_assistance: false, viva: false });
                  }}>Fast Audit</button>
                </div>
              </div>
            </div>
          </div>

          {/* Submit button card */}
          <div
            className="bg-white border-[2.5px] border-[#121212] p-4"
            style={{ boxShadow: '4px 4px 0px #121212' }}
          >
            <button
              id="submitEvaluationBtn"
              type="submit"
              disabled={submitting}
              className="w-full bg-[#ffe600] text-[#1c1b1b] font-display font-bold py-4 px-6 border-[2.5px] border-[#121212] uppercase tracking-wide flex items-center justify-center gap-3 transition-all hover:-translate-x-0.5 hover:-translate-y-0.5 hover:shadow-[7px_7px_0px_#121212] active:translate-x-1 active:translate-y-1 active:shadow-none cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none"
              style={{ boxShadow: '5px 5px 0px #121212' }}
            >
              {submitting ? (
                <>
                  <span
                    className="w-5 h-5 border-2 border-[#121212] border-t-transparent animate-spin"
                    style={{ borderRadius: '50%' }}
                  />
                  Uploading to FastAPI...
                </>
              ) : (
                <>
                  Upload &amp; Run Evaluation
                  <ArrowRight size={22} />
                </>
              )}
            </button>

            {/* Status note */}
            <div className="mt-3 bg-[#FAF6EE] p-3" style={{ boxShadow: '2px 2px 0px #121212' }}>
              <div className="flex items-center gap-1.5 font-mono text-[10px] font-bold text-[#1c1b1b] mb-1">
                <span className="w-2 h-2 rounded-full bg-[#00E5BE] inline-block" />
                STATUS &amp; DISPATCH
              </div>
              <p className="font-mono text-[10px] text-[#4b4731] leading-relaxed">
                Submitting initiates asynchronous parsing in an isolated sandbox. Analysis time
                varies by repository size. Results stream to your dashboard as each module completes.
              </p>
            </div>

            <div className="mt-2 flex items-center justify-between text-[#4b4731]">
              <button
                type="button"
                className="font-mono text-[11px] hover:text-[#1c1b1b] hover:underline flex items-center gap-1"
                onClick={() => { setFile(null); setCourse(''); setTitle(''); setAll(true); setSubmitError(null); }}
              >
                <RefreshCw size={12} />
                Clear Form Inputs
              </button>
              <span className="font-mono text-[10px] text-[#4b4731]">Async Pipeline Ready</span>
            </div>
          </div>
        </div>
      </form>

      {/* Help banner */}
      <div
        className="mt-8 p-4 bg-[#F2ECE1] border-[2px] border-[#121212] flex flex-col md:flex-row md:items-center justify-between gap-4"
        style={{ boxShadow: '3px 3px 0px #121212' }}
      >
        <div className="flex items-start md:items-center gap-3">
          <HelpCircle size={22} className="text-[#1c1b1b] shrink-0" />
          <div className="text-[#1c1b1b]">
            <p className="font-display font-bold text-sm leading-tight">
              Need to upload full class section submissions concurrently?
            </p>
            <p className="font-sans text-sm text-[#4b4731]">
              Use the CLI ingestion script:{' '}
              <code className="bg-white px-1.5 py-0.5 text-[#1c1b1b] font-mono text-xs" style={{ boxShadow: '1px 1px 0px #121212' }}>
                projectlens-batch --course CS402 --zip-dir ./cohort_zips/
              </code>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
