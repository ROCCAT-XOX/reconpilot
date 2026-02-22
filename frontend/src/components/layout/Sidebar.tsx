import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/projects', label: 'Projects', icon: '📁' },
  { path: '/scans', label: 'Scans', icon: '🔍' },
  { path: '/findings', label: 'Findings', icon: '🐛' },
  { path: '/reports', label: 'Reports', icon: '📄' },
  { path: '/team', label: 'Team', icon: '👥' },
  { path: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function Sidebar() {
  return (
    <aside className="w-64 bg-dark-950 border-r border-dark-700 flex flex-col h-full">
      <div className="p-6">
        <h1 className="text-xl font-bold text-primary-400">
          ⚒️ ReconForge
        </h1>
        <p className="text-xs text-gray-500 mt-1">Reconnaissance Orchestrator</p>
      </div>

      <nav className="flex-1 px-3 space-y-1">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary-600/20 text-primary-400'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              )
            }
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-dark-700">
        <p className="text-xs text-gray-600">v0.2.0 · ReconForge</p>
      </div>
    </aside>
  )
}
