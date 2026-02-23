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

interface SidebarProps {
  open: boolean
  onClose: () => void
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed inset-y-0 left-0 z-50 w-64 bg-dark-950 border-r border-dark-700 flex flex-col h-full transform transition-transform duration-200 ease-in-out',
          'md:relative md:translate-x-0',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="p-6 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-primary-400">
              ⚒️ ReconForge
            </h1>
            <p className="text-xs text-gray-500 mt-1">Reconnaissance Orchestrator</p>
          </div>
          <button
            onClick={onClose}
            className="md:hidden text-gray-400 hover:text-gray-200 p-1 min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            ✕
          </button>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={onClose}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-3 rounded-lg text-sm font-medium transition-colors min-h-[44px]',
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
    </>
  )
}
