import { useQuery } from '@tanstack/react-query'
import { findingsApi } from '../api/findings'

export function useProjectFindings(projectId: string | undefined, filters?: { severity?: string; status?: string; source_tool?: string }) {
  return useQuery({
    queryKey: ['findings', projectId, filters],
    queryFn: () => findingsApi.listByProject(projectId!, filters),
    enabled: !!projectId,
  })
}

export function useFindingStats(projectId: string | undefined) {
  return useQuery({
    queryKey: ['finding-stats', projectId],
    queryFn: () => findingsApi.getStats(projectId!),
    enabled: !!projectId,
  })
}
