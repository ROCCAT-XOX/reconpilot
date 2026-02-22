import apiClient from './client'
import type { Project, ProjectMember, ScopeTarget } from '../types/project'

export const projectsApi = {
  list: () => apiClient.get<Project[]>('/projects').then(r => r.data),
  get: (id: string) => apiClient.get<Project>(`/projects/${id}`).then(r => r.data),
  create: (data: { name: string; client_name: string; description?: string }) =>
    apiClient.post<Project>('/projects', data).then(r => r.data),
  update: (id: string, data: Partial<Project>) =>
    apiClient.put<Project>(`/projects/${id}`, data).then(r => r.data),
  delete: (id: string) => apiClient.delete(`/projects/${id}`).then(r => r.data),

  // Members
  listMembers: (projectId: string) =>
    apiClient.get<ProjectMember[]>(`/projects/${projectId}/members`).then(r => r.data),
  addMember: (projectId: string, data: { user_id: string; role: string }) =>
    apiClient.post<ProjectMember>(`/projects/${projectId}/members`, data).then(r => r.data),
  removeMember: (projectId: string, userId: string) =>
    apiClient.delete(`/projects/${projectId}/members/${userId}`).then(r => r.data),

  // Scope
  listScope: (projectId: string) =>
    apiClient.get<ScopeTarget[]>(`/projects/${projectId}/scope`).then(r => r.data),
  addScope: (projectId: string, data: { target_type: string; target_value: string; is_excluded?: boolean; notes?: string }) =>
    apiClient.post<ScopeTarget>(`/projects/${projectId}/scope`, data).then(r => r.data),
  removeScope: (projectId: string, targetId: string) =>
    apiClient.delete(`/projects/${projectId}/scope/${targetId}`).then(r => r.data),
}
