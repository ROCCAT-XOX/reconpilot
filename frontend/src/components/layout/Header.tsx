export default function Header() {
  return (
    <header className="h-16 bg-dark-800 border-b border-dark-700 flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <h2 className="text-lg font-semibold text-gray-100">ReconForge</h2>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-400">
          <span className="w-2 h-2 bg-green-500 rounded-full"></span>
          <span>System Healthy</span>
        </div>

        <div className="flex items-center gap-3 pl-4 border-l border-dark-600">
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-sm font-bold">
            A
          </div>
          <div className="text-sm">
            <p className="text-gray-200 font-medium">Admin</p>
            <p className="text-gray-500 text-xs">admin@reconforge.local</p>
          </div>
        </div>
      </div>
    </header>
  )
}
