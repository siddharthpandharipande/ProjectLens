import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sparkles, Cpu, Layers, ShieldAlert, CheckCircle2, Clock } from 'lucide-react';

export interface FutureModuleConfig {
  id: string;
  title: string;
  phase: string;
  icon: React.ReactNode;
  tagline: string;
  description: string;
  plannedCapabilities: string[];
  plannedInputs: string[];
  plannedOutputs: string[];
}

export const FUTURE_MODULES_CONFIG: Record<string, FutureModuleConfig> = {
  git: {
    id: 'git',
    title: 'Git Development Analysis',
    phase: 'Phase 6',
    icon: <Clock className="w-5 h-5 text-amber-400" />,
    tagline: 'Track repository commit velocity, contributor split, and progression over time.',
    description:
      'Analyzes how the project was actually developed by inspecting raw Git commit graphs, author distributions, and delivery timelines.',
    plannedCapabilities: [
      'Commit Frequency & Activity Histograms',
      'Contributor Balance & Code Addition/Deletion Splits',
      'One-shot Upload vs. Incremental Development Classifier',
      'Repository Activity Timeline'
    ],
    plannedInputs: ['Raw .git directory tree', 'git log --numstat output', 'Author email distributions'],
    plannedOutputs: ['Development Span (Days)', 'Active Contributor Count', 'Commit Progression Curve']
  },
  ai_assistance: {
    id: 'ai_assistance',
    title: 'AI Assistance Signals',
    phase: 'Phase 7',
    icon: <Cpu className="w-5 h-5 text-purple-400" />,
    tagline: 'Multi-signal evidence engine assessing AI code generation likelihood.',
    description:
      'Provides objective evidence regarding the likelihood of significant AI code assistance using structural AST entropy and style consistency deltas.',
    plannedCapabilities: [
      'Style Consistency & Structural Entropy Analysis',
      'Generic Boilerplate AST Subtree Resemblance',
      'Commit Progression vs. Feature Complexity Delta',
      'Documentation-Code Claim Inconsistency Flags'
    ],
    plannedInputs: ['AST Subtree Vectors', 'Naming Entropy Metrics', 'Code Comments & Docstrings'],
    plannedOutputs: ['Assistance Likelihood Level (Low/Med/High)', 'Evidence Itemized Breakdown', 'Confidence Score']
  },
  innovation: {
    id: 'innovation',
    title: 'Innovation DNA Engine',
    phase: 'Phase 8',
    icon: <Sparkles className="w-5 h-5 text-cyan-400" />,
    tagline: 'Measure technical distinction, architectural complexity, and problem originality.',
    description:
      'Evaluates how original and technically distinctive a project is by assessing architecture uniqueness, non-trivial algorithms, and specialized features.',
    plannedCapabilities: [
      'Problem Statement Originality Analysis',
      'Custom Algorithm vs. Wrapper Classifier',
      'Architecture Differentiation Score (Microservices / PubSub / Custom State)',
      'Interoperable Technology Integration Depth'
    ],
    plannedInputs: ['Project AST Architecture', 'Tech Stack Interoperability Matrix', 'Framework Dependencies'],
    plannedOutputs: ['Innovation DNA Score (0-100)', '5-Dimension Breakdown Matrix', 'Key Distinction Signals']
  },
  viva: {
    id: 'viva',
    title: 'Viva Voice & Interactive Q&A',
    phase: 'Phase 9',
    icon: <Layers className="w-5 h-5 text-indigo-400" />,
    tagline: 'Dynamic project-specific oral examination driven by actual repository ASTs.',
    description:
      'Generates intelligent, code-grounded examination questions based on exact project files, dependencies, and doc claims with voice STT/TTS integration.',
    plannedCapabilities: [
      'Project Architecture & Technology Rationale Questions',
      'Code Functionality & Complexity Probe Questions',
      'Documentation Claim Verification Questions',
      'Browser Speech-to-Text & Adaptive Difficulty Engine'
    ],
    plannedInputs: ['Project Code ASTs', 'Database Models & Routes', 'PDF Documentation Claims'],
    plannedOutputs: ['Viva Score Breakdown', 'Student Response Accuracy Log', 'Concept Mastery Radar']
  },
  final_eval: {
    id: 'final_eval',
    title: 'Final Evaluation Engine',
    phase: 'Phase 10',
    icon: <ShieldAlert className="w-5 h-5 text-emerald-400" />,
    tagline: 'Faculty-configurable weighted scoring matrix across all evaluation dimensions.',
    description:
      'Aggregates code quality, similarity, documentation, development process, AI signals, innovation, and viva results into a final academic mark.',
    plannedCapabilities: [
      'Faculty-Customizable Weight Allocation',
      'Weighted Metric Fusion Engine',
      'Grade Boundary Classifier (A / B / C / Pass / Fail)',
      'Comprehensive Grade Justification Log'
    ],
    plannedInputs: ['Phases 1-9 Metric Results', 'Faculty Weight Configurations'],
    plannedOutputs: ['Final Grade (0-100)', 'Dimension Weight Allocation Map', 'Academic Recommendation']
  },
  final_report: {
    id: 'final_report',
    title: 'Final Report Generator',
    phase: 'Phase 11',
    icon: <CheckCircle2 className="w-5 h-5 text-blue-400" />,
    tagline: 'Export faculty-ready evaluation dossiers in Web, PDF, and JSON formats.',
    description:
      'Compiles executive evaluation summaries, structural diagrams, evidence logs, and grade justifications into printable reports for college boards.',
    plannedCapabilities: [
      'Printable PDF Evaluation Dossier',
      'Interactive Web Summary Dashboard',
      'JSON Export for University ERP Integration',
      'Audit Trail & Evidence Archival'
    ],
    plannedInputs: ['Full Evaluation Database Object Graph'],
    plannedOutputs: ['Downloadable PDF', 'Web Executive Dossier', 'University ERP Payload']
  }
};

interface FutureModuleModalProps {
  isOpen: boolean;
  onClose: () => void;
  moduleId: string | null;
}

export const FutureModuleModal: React.FC<FutureModuleModalProps> = ({
  isOpen,
  onClose,
  moduleId
}) => {
  if (!isOpen || !moduleId || !FUTURE_MODULES_CONFIG[moduleId]) return null;

  const config = FUTURE_MODULES_CONFIG[moduleId];

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="bg-[#17191F] border border-[#2A2D38] rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl"
        >
          {/* Header Bar */}
          <div className="p-6 bg-gradient-to-r from-[#1C1F2B] to-[#17191F] border-b border-[#2A2D38] flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center">
                {config.icon}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-headline font-bold text-lg text-white">{config.title}</h3>
                  <span className="font-mono text-[10px] uppercase px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-semibold border border-indigo-500/30">
                    {config.phase} &bull; Preparation
                  </span>
                </div>
                <p className="text-xs text-zinc-400 mt-0.5">{config.tagline}</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-zinc-400 hover:text-white bg-[#21242D] hover:bg-[#2A2D38] transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body Content */}
          <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
            {/* Architectural Notice Banner */}
            <div className="bg-indigo-950/40 border border-indigo-500/30 rounded-xl p-4 flex items-start gap-3">
              <Sparkles className="w-5 h-5 text-indigo-400 shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h4 className="font-headline font-semibold text-xs text-indigo-200 uppercase tracking-wider">
                  Future Module Blueprint
                </h4>
                <p className="text-xs text-zinc-300 leading-relaxed">
                  This evaluation feature is part of the ProjectLens expansion roadmap. Its UI navigation shell is active and ready, but backend analysis execution remains unactivated in Phases 1–5 to prevent ungrounded or synthetic score calculations.
                </p>
              </div>
            </div>

            {/* Description */}
            <div>
              <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 mb-2">
                Overview & Purpose
              </h4>
              <p className="text-sm text-zinc-300 bg-[#0F1014] border border-[#262933] rounded-xl p-4 leading-relaxed">
                {config.description}
              </p>
            </div>

            {/* Planned Capabilities */}
            <div>
              <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3">
                Planned Capabilities
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {config.plannedCapabilities.map((cap, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 p-3 rounded-lg bg-[#0F1014] border border-[#262933] text-xs text-zinc-300"
                  >
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                    <span>{cap}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Technical Inputs & Outputs */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
                  Planned Analysis Inputs
                </h4>
                <div className="space-y-1.5 font-mono text-xs text-zinc-400">
                  {config.plannedInputs.map((input, idx) => (
                    <div key={idx} className="p-2 rounded bg-[#0F1014] border border-zinc-800/80 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                      <span>{input}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="font-mono text-xs font-bold uppercase tracking-wider text-zinc-400">
                  Planned Evaluation Outputs
                </h4>
                <div className="space-y-1.5 font-mono text-xs text-zinc-400">
                  {config.plannedOutputs.map((output, idx) => (
                    <div key={idx} className="p-2 rounded bg-[#0F1014] border border-zinc-800/80 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-purple-400 shrink-0" />
                      <span>{output}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="p-4 bg-[#111318] border-t border-[#2A2D38] flex items-center justify-between">
            <span className="font-mono text-xs text-zinc-500">
              ProjectLens Architecture &bull; {config.phase} Shell
            </span>
            <button
              onClick={onClose}
              className="py-2 px-5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-colors"
            >
              Got it
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
