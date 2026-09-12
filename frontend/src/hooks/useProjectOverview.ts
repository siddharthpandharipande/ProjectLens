import { useState, useEffect, useCallback, useRef } from 'react';
import { ProjectOverview, AnalysisStatus } from '../types/overview';
import { projectService } from '../services/projectService';

export function useProjectOverview(initialProjectId?: string | null) {
  const [projectId, setProjectId] = useState<string | null>(initialProjectId || null);
  const [overview, setOverview] = useState<ProjectOverview | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isReanalyzing, setIsReanalyzing] = useState<boolean>(false);

  const pollTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current);
      pollTimerRef.current = null;
    }
  }, []);

  const fetchOverview = useCallback(async (id: string) => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await projectService.getProjectOverview(id);
      setOverview(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch project overview.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const pollStatus = useCallback((id: string) => {
    stopPolling();

    pollTimerRef.current = setInterval(async () => {
      try {
        const statusData = await projectService.getAnalysisStatus(id);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          stopPolling();
          setIsReanalyzing(false);
          await fetchOverview(id);
        } else if (statusData.status === 'failed') {
          stopPolling();
          setIsReanalyzing(false);
          setError(statusData.error || 'Analysis job failed.');
        }
      } catch (err: any) {
        stopPolling();
        setIsReanalyzing(false);
        setError(err.message || 'Error checking analysis status.');
      }
    }, 1200);
  }, [stopPolling, fetchOverview]);

  useEffect(() => {
    if (!projectId) {
      setOverview(null);
      setStatus(null);
      return;
    }

    // Initial check
    (async () => {
      try {
        setIsLoading(true);
        setError(null);
        const statusData = await projectService.getAnalysisStatus(projectId);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          await fetchOverview(projectId);
        } else if (statusData.status === 'analyzing' || statusData.status === 'queued') {
          pollStatus(projectId);
        } else if (statusData.status === 'failed') {
          setError(statusData.error || 'Analysis failed.');
          setIsLoading(false);
        }
      } catch (err: any) {
        setError(err.message || 'Failed to load project status.');
        setIsLoading(false);
      }
    })();

    return () => stopPolling();
  }, [projectId, pollStatus, fetchOverview, stopPolling]);

  const triggerReanalyze = async () => {
    if (!projectId) return;
    try {
      setIsReanalyzing(true);
      setError(null);
      const newStatus = await projectService.reanalyzeProject(projectId);
      setStatus(newStatus);
      pollStatus(projectId);
    } catch (err: any) {
      setIsReanalyzing(false);
      setError(err.message || 'Failed to re-trigger analysis.');
    }
  };

  const handleUploadSuccess = (newProjectId: string) => {
    setOverview(null);
    setProjectId(newProjectId);
  };

  return {
    projectId,
    setProjectId,
    overview,
    status,
    isLoading,
    isReanalyzing,
    error,
    triggerReanalyze,
    handleUploadSuccess,
  };
}
