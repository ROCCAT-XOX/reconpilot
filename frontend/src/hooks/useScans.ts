import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { scansApi } from '../api/scans'

export function useProjectScans(projectId: string | undefined) {
  return useQuery({
    queryKey: ['scans', projectId],
    queryFn: () => scansApi.listByProject(projectId!),
    enabled: !!projectId,
  })
}

export function useScan(scanId: string | undefined) {
  return useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => scansApi.get(scanId!),
    enabled: !!scanId,
    refetchInterval: (query) => {
      const scan = query.state.data
      return scan?.status === 'running' ? 3000 : false
    },
  })
}

export function useScanJobs(scanId: string | undefined) {
  return useQuery({
    queryKey: ['scan-jobs', scanId],
    queryFn: () => scansApi.getJobs(scanId!),
    enabled: !!scanId,
    refetchInterval: 5000,
  })
}

export function useCreateScan(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name?: string; profile: string; targets?: string[] }) =>
      scansApi.create(projectId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans', projectId] })
    },
  })
}

export function useStartScan() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { projectId: string; name?: string; profile: string; targets?: string[] }) =>
      scansApi.create(data.projectId, { name: data.name, profile: data.profile, targets: data.targets }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['scans', variables.projectId] })
    },
  })
}
