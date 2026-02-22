import { clsx } from 'clsx'
import { severityBg, statusColor } from '../../utils/formatters'

export function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={clsx('px-2 py-0.5 rounded text-xs font-medium border', severityBg(severity))}>
      {severity.toUpperCase()}
    </span>
  )
}

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={clsx('text-xs font-medium', statusColor(status))}>
      ● {status.replace('_', ' ')}
    </span>
  )
}
