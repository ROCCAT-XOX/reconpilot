import apiClient from './client'
import type { Scan, ScanJob, ScanProfile } from '../types/scan'

export const scansApi = {
  get: (id: string) => apiClient.get<Scan>(`/scans/${id}`).then(r => r.data),
  getJobs: (id: string) => apiClient.get<ScanJob[]>(`/scans/${id}/jobs`).then(r => r.data),
  getTimeline: (id: string) => apiClient.get(`/scans/${id}/timeline`).then(r => r.data),
  pause: (id: string) => apiClient.put(`/scans/${id}/pause`).then(r => r.data),
  resume: (id: string) => apiClient.put(`/scans/${id}/resume`).then(r => r.data),
  cancel: (id: string) => apiClient.put(`/scans/${id}/cancel`).then(r => r.data),

  // Project-scoped
  listByProject: (projectId: string) =>
    apiClient.get<Scan[]>(`/projects/${projectId}/scans`).then(r => r.data),
  create: (projectId: string, data: { name?: string; profile: string; config?: Record<string, any>; targets?: string[] }) =>
    apiClient.post<Scan>(`/projects/${projectId}/scans`, data).then(r => r.data),

  // Profiles
  getProfiles: () => apiClient.get<ScanProfile[]>('/scans/profiles/available').then(r => r.data),
  getTools: () => apiClient.get('/scans/tools/available').then(r => r.data),
}
