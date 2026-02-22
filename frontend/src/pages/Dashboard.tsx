import { useQuery } from '@tanstack/react-query'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'
import { SEVERITY_COLORS } from '../utils/constants'

export default function Dashboard() {
  const navigate = useNavigate()

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => apiClient.get('/projects/', { params: { per_page: 100 } }).then(r => r.data.items),
  })

  const projectCount = projects?.length || 0
  const activeProjects = projects?.filter((p: any) => p.status === 'active')?.length || 0

  const stats = [
    { label: 'Active Projects', value: activeProjects, icon: '📁', color: 'text-blue-400' },
    { label: 'Total Projects', value: projectCount, icon: '📋', color: 'text-purple-400' },
    { label: 'Quick Actions', value: '→', icon: '🚀', color: 'text-green-400', action: () => navigate('/projects') },
  ]

  const severityData = Object.entries(SEVERITY_COLORS).map(([name, color]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: Math.floor(Math.random() * 10), // Placeholder until real data loads
    color,
  }))

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500 mt-1">ReconForge Overview</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className={`card ${stat.action ? 'cursor-pointer hover:border-dark-500' : ''}`}
            onClick={stat.action}
          >
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

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <button onClick={() => navigate('/projects')} className="btn-primary w-full text-left">
              + New Project
            </button>
            <button onClick={() => navigate('/findings')} className="btn-secondary w-full text-left">
              📊 View All Findings
            </button>
            <button onClick={() => navigate('/team')} className="btn-secondary w-full text-left">
              👥 Manage Team
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
