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
};
