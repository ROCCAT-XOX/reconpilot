export default function Dashboard() {
  const stats = [
    { label: 'Active Projects', value: '0', icon: '📁', color: 'text-blue-400' },
    { label: 'Running Scans', value: '0', icon: '🔍', color: 'text-yellow-400' },
    { label: 'Open Findings', value: '0', icon: '🐛', color: 'text-red-400' },
    { label: 'Reports Generated', value: '0', icon: '📄', color: 'text-green-400' },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-gray-500 mt-1">Welcome to ReconForge</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
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
          <h3 className="text-lg font-semibold mb-4">Recent Activity</h3>
          <p className="text-gray-500 text-sm">No recent activity. Start a new project to begin.</p>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <button className="btn-primary w-full text-left">
              + New Project
            </button>
            <button className="btn-secondary w-full text-left">
              📊 View All Findings
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
