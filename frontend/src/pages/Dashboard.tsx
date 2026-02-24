import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'

interface DashboardStats {
  projects_count: number
  active_scans: number
  total_findings: number
  critical_findings: number
  high_findings: number
  recent_scans: {
    id: string
    name: string | null
    profile: string
    status: string
    project_id: string
    created_at: string | null
  }[]
}

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: () => apiClient.get('/dashboard/stats').then(r => r.data),
  })

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.get('/projects/', { params: { per_page: 100 } }).then(r => r.data.items),
  })

  const isLoading = !stats

  const statCards = [
    { label: 'Projects', value: stats?.projects_count ?? '—', icon: '📁', color: 'text-blue-400' },
    { label: 'Active Scans', value: stats?.active_scans ?? '—', icon: '📡', color: 'text-green-400' },
    { label: 'Total Findings', value: stats?.total_findings ?? '—', icon: '🛡️', color: 'text-purple-400' },
    { label: 'Critical', value: stats?.critical_findings ?? '—', icon: '🔴', color: 'text-red-400' },
    { label: 'High', value: stats?.high_findings ?? '—', icon: '🟠', color: 'text-orange-400' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500 mt-1">ReconForge Overview</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 md:gap-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className={`text-3xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
              </div>
              <span className="text-3xl">{stat.icon}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Scans</h3>
          {stats?.recent_scans && stats.recent_scans.length > 0 ? (
            <div className="space-y-3">
              {stats.recent_scans.slice(0, 5).map((scan) => (
                <div
                  key={scan.id}
                  className="flex items-center justify-between p-3 bg-dark-800/50 rounded-lg cursor-pointer hover:bg-dark-800"
                  onClick={() => navigate(`/scans/${scan.id}`)}
                >
                  <div>
                    <div className="font-medium text-sm">{scan.name || scan.profile}</div>
                    <div className="text-xs text-gray-500">{scan.created_at ? new Date(scan.created_at).toLocaleString() : ''}</div>
                  </div>
                  <span className={`text-xs ${scan.status === 'running' ? 'text-green-400' : scan.status === 'completed' ? 'text-blue-400' : 'text-gray-500'}`}>
                    {scan.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No scans yet. Start one from a project.</p>
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Recent Projects</h3>
          {projects && projects.length > 0 ? (
            <div className="space-y-3">
              {projects.slice(0, 5).map((p: any) => (
                <div
                  key={p.id}
                  className="flex items-center justify-between p-3 bg-dark-800/50 rounded-lg cursor-pointer hover:bg-dark-800"
                  onClick={() => navigate(`/projects/${p.id}`)}
                >
                  <div>
                    <div className="font-medium text-sm">{p.name}</div>
                    <div className="text-xs text-gray-500">{p.client_name}</div>
                  </div>
                  <span className={`text-xs ${p.status === 'active' ? 'text-green-400' : 'text-gray-500'}`}>
                    {p.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">No projects yet. Create one to get started.</p>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="flex flex-col sm:flex-row gap-3">
          <button onClick={() => navigate('/projects')} className="btn-primary min-h-[44px]">
            + New Project
          </button>
          <button onClick={() => navigate('/findings')} className="btn-secondary min-h-[44px]">
            📊 View All Findings
          </button>
          <button onClick={() => navigate('/team')} className="btn-secondary min-h-[44px]">
            👥 Manage Team
          </button>
        </div>
      </div>
    </div>
  )
}
