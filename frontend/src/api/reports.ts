import apiClient from './client'

export interface ReportData {
  id: string
  project_id: string
  scan_id: string | null
  title: string
  report_type: string
  status: 'generating' | 'completed' | 'failed'
  file_path: string | null
  config: Record<string, any>
  generated_by: string | null
  created_at: string
}

export const reportsApi = {
  get: (id: string) => apiClient.get<ReportData>(`/reports/${id}`).then(r => r.data),
  list: (projectId?: string) =>
    apiClient.get<ReportData[]>('/reports', { params: projectId ? { project_id: projectId } : {} }).then(r => r.data),
  listByProject: (projectId: string) =>
    apiClient.get<ReportData[]>(`/projects/${projectId}/reports`).then(r => r.data),
  generate: (data: { project_id: string; report_type: string; title: string; include_sections?: string[]; severity_filter?: string[] }) =>
    apiClient.post<ReportData>('/reports', data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/reports/${id}`).then(r => r.data),
  download: (id: string) =>
    apiClient.get(`/reports/${id}/download`, { responseType: 'blob' }).then(r => r.data),
}
