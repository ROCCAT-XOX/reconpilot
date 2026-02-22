import apiClient from './client'

export interface ReportData {
  id: string
  project_id: string
  title: string
  report_type: string
  status: 'generating' | 'completed' | 'failed'
  file_path: string | null
  created_at: string
}

export const reportsApi = {
  get: (id: string) => apiClient.get<ReportData>(`/reports/${id}`).then(r => r.data),
  list: () => apiClient.get<ReportData[]>('/reports/').then(r => r.data),
  listByProject: (projectId: string) =>
    apiClient.get<ReportData[]>(`/projects/${projectId}/reports`).then(r => r.data),
  generate: (data: { project_id: string; report_type: string; title: string }) =>
    apiClient.post<ReportData>('/reports/', data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/reports/${id}`).then(r => r.data),
  download: (id: string) =>
    apiClient.get(`/reports/${id}/download`, { responseType: 'blob' }).then(r => r.data),
}
