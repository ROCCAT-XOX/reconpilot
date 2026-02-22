import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { scansApi } from '../api/scans'
import { useWebSocket } from '../hooks/useWebSocket'
import { StatusBadge } from '../components/common/StatusBadge'
import ScanProgress from '../components/scans/ScanProgress'
import ScanTimeline from '../components/scans/ScanTimeline'
import { formatDateTime } from '../utils/formatters'
import type { Scan, ScanJob } from '../types/scan'

export default function ScanView() {
  const { scanId } = useParams<{ scanId: string }>()
  const navigate = useNavigate()

  const { data: scan, isLoading } = useQuery({
    queryKey: ['scan', scanId],
    queryFn: () => scansApi.get(scanId!),
    enabled: !!scanId,
    refetchInterval: (query) => {
      const s = query.state.data as Scan | undefined
      return s && ['running', 'pending'].includes(s.status) ? 3000 : false
    },
  })

  const { data: jobs = [] } = useQuery({
    queryKey: ['scan-jobs', scanId],
    queryFn: () => scansApi.getJobs(scanId!),
    enabled: !!scanId,
    refetchInterval: (query) => {
      const j = query.state.data as ScanJob[] | undefined
      return j?.some((job) => ['running', 'pending'].includes(job.status)) ? 2000 : false
    },
  })

  // WebSocket for live updates
  const { lastEvent } = useWebSocket(scan?.project_id)

  if (isLoading) {
    return <div className="p-6 text-gray-500">Loading scan...</div>
  }

  if (!scan) {
    return <div className="p-6 text-gray-500">Scan not found.</div>
  }

  const completedJobs = jobs.filter((j: ScanJob) => j.status === 'completed').length
  const totalJobs = jobs.length
  const progressPct = totalJobs > 0 ? Math.round((completedJobs / totalJobs) * 100) : 0

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <button onClick={() => navigate(-1)} className="text-sm text-gray-500 hover:text-gray-300 mb-2 flex items-center gap-1">
          ← Back
        </button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">{scan.name || `Scan ${scan.id.slice(0, 8)}`}</h1>
            <div className="flex items-center gap-3 mt-2">
              <StatusBadge status={scan.status} />
              <span className="text-sm text-gray-500 capitalize">{scan.profile} profile</span>
              <span className="text-sm text-gray-600">•</span>
              <span className="text-sm text-gray-500">Started {formatDateTime(scan.created_at)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-dark-900 rounded-xl border border-dark-700 p-6">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-400">Overall Progress</h3>
          <span className="text-sm font-bold text-primary-400">{progressPct}%</span>
        </div>
        <div className="w-full bg-dark-700 rounded-full h-3 overflow-hidden">
          <div
            className="bg-gradient-to-r from-primary-600 to-primary-400 h-3 rounded-full transition-all duration-500 ease-out"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>{completedJobs} of {totalJobs} jobs completed</span>
          {scan.completed_at && <span>Finished {formatDateTime(scan.completed_at)}</span>}
        </div>
      </div>

      {/* Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Job Progress List */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Tool Execution</h3>
          <ScanProgress jobs={jobs} />
        </div>

        {/* Timeline */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Timeline</h3>
          <ScanTimeline jobs={jobs} />
        </div>
      </div>

      {/* Live Events */}
      {lastEvent && (
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-4">
          <h3 className="text-sm font-semibold text-gray-400 mb-2">Latest Event</h3>
          <pre className="text-xs text-green-400 font-mono bg-dark-950 rounded-lg p-3 overflow-x-auto">
            {JSON.stringify(lastEvent, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
