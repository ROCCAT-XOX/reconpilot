import { StatusBadge } from '../common/StatusBadge'
import type { ScanJob } from '../../types/scan'

interface Props {
  jobs: ScanJob[]
  status: string
}

export default function ScanProgress({ jobs, status }: Props) {
  const total = jobs.length
  const completed = jobs.filter(j => j.status === 'completed').length
  const failed = jobs.filter(j => j.status === 'failed').length
  const running = jobs.filter(j => j.status === 'running').length
  const progress = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold">Scan Progress</h3>
        <StatusBadge status={status} />
      </div>

      <div className="w-full bg-dark-700 rounded-full h-3 mb-4">
        <div
          className="bg-primary-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        />
      </div>

      <div className="grid grid-cols-4 gap-4 text-center text-sm">
        <div>
          <div className="text-2xl font-bold text-gray-200">{total}</div>
          <div className="text-gray-500">Total</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-green-400">{completed}</div>
          <div className="text-gray-500">Done</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-yellow-400">{running}</div>
          <div className="text-gray-500">Running</div>
        </div>
        <div>
          <div className="text-2xl font-bold text-red-400">{failed}</div>
          <div className="text-gray-500">Failed</div>
        </div>
      </div>
    </div>
  )
}
