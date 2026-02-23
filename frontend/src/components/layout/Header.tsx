import { useAuth } from '../../hooks/useAuth'

interface HeaderProps {
  onMenuToggle: () => void
}

export default function Header({ onMenuToggle }: HeaderProps) {
  const { user, logout } = useAuth()

  return (
    <header className="h-14 bg-dark-950 border-b border-dark-700 flex items-center justify-between px-4 md:px-6">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="md:hidden text-gray-400 hover:text-gray-200 min-h-[44px] min-w-[44px] flex items-center justify-center text-xl"
        >
          ☰
        </button>
        <span className="md:hidden text-sm font-bold text-primary-400">⚒️ ReconForge</span>
      </div>
      <div className="flex items-center gap-3 md:gap-4">
        {user && (
          <>
            <span className="text-sm text-gray-400 hidden sm:inline">{user.full_name}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              user.role === 'admin' ? 'bg-red-500/20 text-red-400' : 'bg-primary-500/20 text-primary-400'
            }`}>
              {user.role}
            </span>
          </>
        )}
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300 min-h-[44px] flex items-center">
          Logout
        </button>
      </div>
    </header>
  )
}
