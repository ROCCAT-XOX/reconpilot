import apiClient from './client'
import type { Finding, FindingComment, FindingStats } from '../types/finding'

export const findingsApi = {
  get: (id: string) => apiClient.get<Finding>(`/findings/${id}`).then(r => r.data),
  list: (params?: { severity?: string; status?: string; source_tool?: string }) =>
    apiClient.get<Finding[]>('/findings', { params }).then(r => r.data),
  update: (id: string, data: Partial<Finding>) =>
    apiClient.put<Finding>(`/findings/${id}`, data).then(r => r.data),
  verify: (id: string) => apiClient.put(`/findings/${id}/verify`).then(r => r.data),

  // Comments
  listComments: (findingId: string) =>
    apiClient.get<FindingComment[]>(`/findings/${findingId}/comments`).then(r => r.data),
  addComment: (findingId: string, content: string) =>
    apiClient.post<FindingComment>(`/findings/${findingId}/comments`, { content }).then(r => r.data),

  // Project-scoped
  listByProject: (projectId: string, params?: { severity?: string; status?: string; source_tool?: string }) =>
    apiClient.get<Finding[]>(`/projects/${projectId}/findings`, { params }).then(r => r.data),
  getStats: (projectId: string) =>
    apiClient.get<FindingStats>(`/projects/${projectId}/findings/stats`).then(r => r.data),
  compareScan: (projectId: string, scanAId: string, scanBId: string) =>
    apiClient.post(`/projects/${projectId}/compare`, { scan_a_id: scanAId, scan_b_id: scanBId }).then(r => r.data),
}
