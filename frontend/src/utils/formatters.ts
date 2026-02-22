export function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleDateString('de-DE', {
    year: 'numeric', month: '2-digit', day: '2-digit',
  })
}

export function formatDateTime(dateStr: string | null): string {
  if (!dateStr) return '—'
  return new Date(dateStr).toLocaleString('de-DE', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
  })
}

export function formatDuration(seconds: number | null): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}h ${m}m`
}

export function severityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-500',
    high: 'text-orange-500',
    medium: 'text-yellow-500',
    low: 'text-blue-400',
    info: 'text-gray-400',
  }
  return colors[severity] || 'text-gray-400'
}

export function severityBg(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'bg-red-500/20 text-red-400 border-red-500/30',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    info: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
  }
  return colors[severity] || 'bg-gray-500/20 text-gray-400 border-gray-500/30'
}

export function statusColor(status: string): string {
  const colors: Record<string, string> = {
    running: 'text-green-400',
    completed: 'text-blue-400',
    failed: 'text-red-400',
    pending: 'text-yellow-400',
    paused: 'text-orange-400',
    cancelled: 'text-gray-500',
    open: 'text-yellow-400',
    confirmed: 'text-red-400',
    false_positive: 'text-gray-500',
    remediated: 'text-green-400',
    active: 'text-green-400',
    archived: 'text-gray-500',
  }
  return colors[status] || 'text-gray-400'
}
