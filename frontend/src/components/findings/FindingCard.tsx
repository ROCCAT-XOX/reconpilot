import { SeverityBadge, StatusBadge } from '../common/StatusBadge'
import type { Finding } from '../../types/finding'

interface Props {
  finding: Finding
  onClick?: () => void
}

export default function FindingCard({ finding, onClick }: Props) {
  return (
    <div
      onClick={onClick}
      className="card cursor-pointer hover:border-dark-500 transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <SeverityBadge severity={finding.severity} />
            <StatusBadge status={finding.status} />
          </div>
          <h4 className="font-medium text-sm truncate">{finding.title}</h4>
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            {finding.target_host && <span>🖥 {finding.target_host}</span>}
            {finding.target_port && <span>:{finding.target_port}</span>}
            <span>🔧 {finding.source_tool}</span>
            {finding.cve_id && <span className="text-orange-400">{finding.cve_id}</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
