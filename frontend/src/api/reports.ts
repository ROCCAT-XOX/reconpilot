import apiClient from './client'

export interface ReportData {
  id: string
  project_id: string
  scan_id: string | null
  name: string
  template: string
  format: string
  file_path: string | null
  config: Record<string, any>
  generated_by: string | null
  created_at: string
}

export const reportsApi = {
  get: (id: string) => apiClient.get<ReportData>(`/reports/${id}`).then(r => r.data),
  listByProject: (projectId: string) =>
    apiClient.get<ReportData[]>(`/projects/${projectId}/reports`).then(r => r.data),
  create: (projectId: string, data: { name: string; template: string; format: string; scan_id?: string; config?: Record<string, any> }) =>
    apiClient.post<ReportData>(`/projects/${projectId}/reports`, data).then(r => r.data),
  download: (id: string) =>
    apiClient.get(`/reports/${id}/download`, { responseType: 'blob' }).then(r => r.data),
}
