import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import apiClient from '../api/client'
import { StatusBadge } from '../components/common/StatusBadge'
import { formatDateTime } from '../utils/formatters'

interface ScanItem {
  id: string
  project_id: string
  name: string | null
  profile: string
  status: string
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export default function Scans() {
  const navigate = useNavigate()

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.get('/projects/', { params: { per_page: 100 } }).then(r => r.data.items),
  })

  // Fetch scans for all projects
  const { data: allScans, isLoading } = useQuery({
    queryKey: ['all-scans', projects?.map((p: any) => p.id)],
    queryFn: async () => {
      if (!projects || projects.length === 0) return []
      const results = await Promise.all(
        projects.map((p: any) =>
          apiClient.get(`/projects/${p.id}/scans/`, { params: { per_page: 100 } })
            .then(r => r.data.items.map((s: ScanItem) => ({ ...s, project_name: p.name })))
            .catch(() => [])
        )
      )
      return results.flat().sort((a: any, b: any) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      )
    },
    enabled: !!projects,
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">Scans</h1>
          <p className="text-gray-400">{allScans?.length ?? 0} total scans</p>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1,2,3].map(i => (
            <div key={i} className="bg-dark-800 rounded-lg p-4 border border-dark-700 animate-pulse">
              <div className="h-5 bg-dark-700 rounded w-1/3 mb-2" />
              <div className="h-4 bg-dark-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : !allScans || allScans.length === 0 ? (
        <div className="bg-dark-800 rounded-lg p-8 text-center border border-dark-700">
          <div className="text-4xl mb-3">📡</div>
          <p className="text-gray-400 text-lg">No scans yet</p>
          <p className="text-gray-500 text-sm mt-2">Create a project and start a scan to see results here.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {allScans.map((scan: any) => (
            <div
              key={scan.id}
              onClick={() => navigate(`/scans/${scan.id}`)}
              className="bg-dark-800 rounded-lg p-4 hover:bg-dark-700 cursor-pointer transition-colors border border-dark-700"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="font-medium text-white truncate">
                    {scan.name || `${scan.profile} scan`}
                  </h3>
                  <p className="text-sm text-gray-400 mt-1 truncate">
                    Project: {scan.project_name} · Profile: {scan.profile}
                  </p>
                </div>
                <div className="flex items-center gap-3 sm:gap-4 shrink-0">
                  <StatusBadge status={scan.status} />
                  <span className="text-xs sm:text-sm text-gray-500">
                    {formatDateTime(scan.created_at)}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
