import { request } from './api';
import {
  UploadResponse,
  AnalysisStatus,
  ProjectOverview,
} from '../types/overview';

export const projectService = {
  async uploadProject(file: File, studentName: string = 'Alex Chen', course: string = 'CS499 Final Project'): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('student_name', studentName);
    formData.append('course', course);

    return request<UploadResponse>('/projects/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async submitRepositoryUrl(gitUrl: string, studentName: string = 'Alex Chen', course: string = 'CS499 Final Project'): Promise<UploadResponse> {
    return request<UploadResponse>('/projects/repository', {
      method: 'POST',
      body: JSON.stringify({
        git_url: gitUrl,
        student_name: studentName,
        course: course,
      }),
    });
  },

  async reanalyzeProject(projectId: string): Promise<AnalysisStatus> {
    return request<AnalysisStatus>(`/projects/${projectId}/analyze`, {
      method: 'POST',
    });
  },

  async getAnalysisStatus(projectId: string): Promise<AnalysisStatus> {
    return request<AnalysisStatus>(`/projects/${projectId}/analysis-status`, {
      method: 'GET',
    });
  },

  async getProjectOverview(projectId: string): Promise<ProjectOverview> {
    return request<ProjectOverview>(`/projects/${projectId}/overview`, {
      method: 'GET',
    });
  },

  async getCodeQualityAnalysis(projectId: string): Promise<any> {
    return request<any>(`/projects/${projectId}/code-quality`, {
      method: 'GET',
    });
  },

  async getSimilarityAnalysis(projectId: string): Promise<any> {
    return request<any>(`/projects/${projectId}/similarity`, {
      method: 'GET',
    });
  },

  async getDocumentationAnalysis(projectId: string): Promise<any> {
    return request<any>(`/projects/${projectId}/documentation`, {
      method: 'GET',
    });
  },

  async compareProjects(projectAId: string, projectBId: string): Promise<any> {
    return request<any>('/projects/compare', {
      method: 'POST',
      body: JSON.stringify({
        project_a_id: projectAId,
        project_b_id: projectBId,
      }),
    });
  },
};


