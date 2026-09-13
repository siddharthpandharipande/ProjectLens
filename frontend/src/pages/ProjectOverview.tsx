import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '../components/layout/Sidebar';
import { Header } from '../components/layout/Header';
import { UploadModal } from '../components/project-overview/UploadModal';
import { CodeQualityDetailModal } from '../components/project-overview/CodeQualityDetailModal';
import { SimilarityDetailModal } from '../components/project-overview/SimilarityDetailModal';
import { DocumentationDetailModal } from '../components/project-overview/DocumentationDetailModal';
import { FutureModuleModal } from '../components/project-overview/FutureModuleModal';
import { OverallScoreCard } from '../components/project-overview/OverallScoreCard';
import { EvaluationMetricCard } from '../components/project-overview/EvaluationMetricCard';
import { TechnologyStack } from '../components/project-overview/TechnologyStack';
import { CodeAnalytics } from '../components/project-overview/CodeAnalytics';
import { StrengthsPanel } from '../components/project-overview/StrengthsPanel';
import { ImprovementsPanel } from '../components/project-overview/ImprovementsPanel';
import { AnalysisStatus as AnalysisStatusComponent } from '../components/project-overview/AnalysisStatus';
import { useProjectOverview } from '../hooks/useProjectOverview';
import { UploadCloud, AlertCircle, RefreshCw, Layers } from 'lucide-react';

export const ProjectOverviewPage: React.FC = () => {
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [isCodeQualityOpen, setIsCodeQualityOpen] = useState(false);
  const [isSimilarityOpen, setIsSimilarityOpen] = useState(false);
  const [isDocumentationOpen, setIsDocumentationOpen] = useState(false);
  const [selectedFutureModuleId, setSelectedFutureModuleId] = useState<string | null>(null);
  const {
    projectId,
    overview,
    status,
    isLoading,
    isReanalyzing,
    error,
    triggerReanalyze,
    handleUploadSuccess,
  } = useProjectOverview(null);

  return (
    <div className="flex bg-bg-main min-h-screen">
      {/* Sidebar */}
      <Sidebar
        onOpenUpload={() => setIsUploadOpen(true)}
        onSelectFutureModule={(id) => setSelectedFutureModuleId(id)}
        onOpenCodeQuality={() => setIsCodeQualityOpen(true)}
        onOpenSimilarity={() => setIsSimilarityOpen(true)}
        onOpenDocumentation={() => setIsDocumentationOpen(true)}
      />

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col min-w-0">
        <Header
          projectName={overview?.project.name}
          studentName={overview?.project.student_name}
          course={overview?.project.course}
          isReanalyzing={isReanalyzing}
          onReanalyze={projectId ? triggerReanalyze : undefined}
          onOpenUpload={() => setIsUploadOpen(true)}
        />

        <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto w-full space-y-8">
          {/* 1. Empty State (No project selected/uploaded yet) */}
          {!projectId && !isLoading && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-bg-card border border-border rounded-xl p-12 text-center flex flex-col items-center justify-center my-12"
            >
              <div className="w-16 h-16 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary mb-4">
                <UploadCloud className="w-8 h-8" />
              </div>
              <h2 className="font-headline font-bold text-2xl text-white mb-2">
                No Project Selected
              </h2>
              <p className="text-sm text-zinc-400 max-w-md mb-6">
                Upload a student project ZIP file to extract real code metrics, AST complexity analysis, technology signatures, and documentation structure.
              </p>
              <button
                onClick={() => setIsUploadOpen(true)}
                className="py-2.5 px-6 rounded-md bg-primary text-white font-semibold text-sm hover:bg-primary-hover transition-all shadow-lg shadow-primary/25"
              >
                Upload Project ZIP &rarr;
              </button>
            </motion.div>
          )}

          {/* 2. Loading / Analyzing Status State */}
          <AnimatePresence>
            {(status?.status === 'analyzing' || status?.status === 'queued') && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="bg-bg-card border border-primary/40 rounded-xl p-6 shadow-lg relative overflow-hidden"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center text-primary shrink-0">
                    <RefreshCw className="w-5 h-5 animate-spin text-primary" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <h4 className="font-headline font-bold text-sm text-white">
                        Analysis in Progress...
                      </h4>
                      <span className="font-mono text-xs font-semibold text-primary">
                        {status.progress}%
                      </span>
                    </div>
                    <p className="text-xs text-zinc-400 font-mono">
                      {status.current_stage || 'Initializing parser...'}
                    </p>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-bg-main h-2 rounded-full overflow-hidden border border-border">
                  <motion.div
                    className="bg-primary h-full rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${status.progress}%` }}
                    transition={{ duration: 0.3 }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* 3. Error State */}
          {error && (
            <div className="bg-status-red/10 border border-status-red/30 rounded-xl p-6 text-status-red flex items-start gap-4">
              <AlertCircle className="w-6 h-6 shrink-0 mt-0.5" />
              <div>
                <h4 className="font-headline font-bold text-sm text-white mb-1">
                  Analysis Pipeline Error
                </h4>
                <p className="text-xs text-zinc-300 mb-4">{error}</p>
                {projectId && (
                  <button
                    onClick={triggerReanalyze}
                    className="py-1.5 px-3 rounded bg-status-red/20 border border-status-red/40 text-xs font-semibold text-white hover:bg-status-red/30 transition-colors"
                  >
                    Retry Analysis
                  </button>
                )}
              </div>
            </div>
          )}

          {/* 4. Complete Overview Content Display */}
          {overview && (
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="space-y-8"
            >
              {/* Top Summary Grid (Overall Score + Subscores) */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Overall Score Card */}
                <OverallScoreCard
                  score={overview.evaluation.overall_score}
                  evaluation={overview.evaluation}
                />

                {/* Subscores 2x2 Grid */}
                <div className="lg:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <EvaluationMetricCard
                    title="Technical Execution"
                    score={overview.evaluation.technical_execution}
                    detail={overview.evaluation.technical_execution_detail}
                    strokeColor="#3157D5"
                    onOpenDetailModal={() => setIsCodeQualityOpen(true)}
                  />
                  <EvaluationMetricCard
                    title="Originality"
                    score={overview.evaluation.originality}
                    detail={overview.evaluation.originality_detail}
                    subtext="Click to compare with baseline projects"
                    strokeColor="#E9785B"
                    onOpenDetailModal={() => setIsSimilarityOpen(true)}
                  />
                  <EvaluationMetricCard
                    title="Documentation Integrity"
                    score={overview.evaluation.documentation_integrity}
                    detail={overview.evaluation.documentation_integrity_detail}
                    strokeColor="#10B981"
                    onOpenDetailModal={() => setIsDocumentationOpen(true)}
                  />
                  <EvaluationMetricCard
                    title="Development Process"
                    score={overview.evaluation.development_process}
                    detail={overview.evaluation.development_process_detail}
                    subtext={overview.evaluation.development_process === null ? "Git history not included" : undefined}
                    strokeColor="#F59E0B"
                  />
                </div>
              </div>

              {/* Technology Stack & Code Analytics */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-1">
                  <TechnologyStack technologies={overview.technology_stack} />
                </div>
                <div className="lg:col-span-2">
                  <CodeAnalytics metrics={overview.code_metrics} />
                </div>
              </div>

              {/* Strengths & Areas for Improvement */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <StrengthsPanel strengths={overview.strengths} />
                <ImprovementsPanel improvements={overview.improvements} />
              </div>

              {/* Analysis Metadata & Status */}
              <AnalysisStatusComponent
                analysis={overview.analysis}
                onReanalyze={triggerReanalyze}
                isReanalyzing={isReanalyzing}
              />
            </motion.div>
          )}
        </main>
      </div>

      {/* Modals */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      <FutureModuleModal
        isOpen={!!selectedFutureModuleId}
        onClose={() => setSelectedFutureModuleId(null)}
        moduleId={selectedFutureModuleId}
      />

      {projectId && (
        <>
          <CodeQualityDetailModal
            isOpen={isCodeQualityOpen}
            onClose={() => setIsCodeQualityOpen(false)}
            projectId={projectId}
          />
          <SimilarityDetailModal
            isOpen={isSimilarityOpen}
            onClose={() => setIsSimilarityOpen(false)}
            projectId={projectId}
          />
          <DocumentationDetailModal
            isOpen={isDocumentationOpen}
            onClose={() => setIsDocumentationOpen(false)}
            projectId={projectId}
          />
        </>
      )}
    </div>
  );
};
