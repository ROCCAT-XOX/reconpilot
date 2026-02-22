import { useAuth } from '../../hooks/useAuth'

export default function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="h-14 bg-dark-950 border-b border-dark-700 flex items-center justify-between px-6">
      <div />
      <div className="flex items-center gap-4">
        {user && (
          <>
            <span className="text-sm text-gray-400">{user.full_name}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              user.role === 'admin' ? 'bg-red-500/20 text-red-400' : 'bg-primary-500/20 text-primary-400'
            }`}>
              {user.role}
            </span>
          </>
        )}
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-300">
          Logout
        </button>
      </div>
    </header>
  )
}
