import { ConnectionStatus as Status } from '../../api/websocket'

const statusConfig = {
  connected: { color: 'bg-green-500', label: 'Connected' },
  disconnected: { color: 'bg-red-500', label: 'Disconnected' },
  reconnecting: { color: 'bg-yellow-500 animate-pulse', label: 'Reconnecting...' },
}

export default function ConnectionIndicator({ status }: { status: Status }) {
  const config = statusConfig[status]

  return (
    <div className="flex items-center gap-1.5" title={config.label}>
      <span className={`w-2 h-2 rounded-full ${config.color}`} />
      <span className="text-xs text-gray-500">{config.label}</span>
    </div>
  )
}
