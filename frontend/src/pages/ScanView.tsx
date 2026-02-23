import { useParams, useNavigate } from 'react-router-dom'
import { useScan, useScanJobs } from '../hooks/useScans'
import { useWebSocket } from '../hooks/useWebSocket'
import { StatusBadge } from '../components/common/StatusBadge'
import ScanProgress from '../components/scans/ScanProgress'
import ScanTimeline from '../components/scans/ScanTimeline'
import { scansApi } from '../api/scans'
import { formatDateTime, formatDuration } from '../utils/formatters'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function ScanView() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  const { data: scan } = useScan(id)
  const { data: jobs } = useScanJobs(id)
  const { events } = useWebSocket(scan?.project_id)

  const pauseMutation = useMutation({
    mutationFn: () => scansApi.pause(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scan', id] }),
  })

  const resumeMutation = useMutation({
    mutationFn: () => scansApi.resume(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scan', id] }),
  })

  const cancelMutation = useMutation({
    mutationFn: () => scansApi.cancel(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scan', id] }),
  })

  if (!scan) return <div className="text-center py-12 text-gray-500">Loading...</div>

  const duration = scan.started_at && scan.completed_at
    ? Math.round((new Date(scan.completed_at).getTime() - new Date(scan.started_at).getTime()) / 1000)
    : null

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold">{scan.name || scan.profile}</h1>
          <div className="flex items-center gap-2 md:gap-3 mt-1 text-sm text-gray-500 flex-wrap">
            <StatusBadge status={scan.status} />
            <span>Profile: {scan.profile}</span>
            {duration && <span>Duration: {formatDuration(duration)}</span>}
          </div>
        </div>
        <div className="flex gap-2 flex-wrap">
          {scan.status === 'running' && (
            <>
              <button onClick={() => pauseMutation.mutate()} className="btn-secondary text-sm min-h-[44px]">⏸ Pause</button>
              <button onClick={() => cancelMutation.mutate()} className="btn-secondary text-sm text-red-400 min-h-[44px]">✗ Cancel</button>
            </>
          )}
          {scan.status === 'paused' && (
            <button onClick={() => resumeMutation.mutate()} className="btn-primary text-sm min-h-[44px]">▶ Resume</button>
          )}
          <button onClick={() => navigate(`/projects/${scan.project_id}`)} className="btn-secondary text-sm min-h-[44px]">← Back</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <ScanProgress jobs={jobs || []} status={scan.status} />
          <ScanTimeline jobs={jobs || []} />
        </div>

        <div className="space-y-6">
          <div className="card">
            <h3 className="font-semibold mb-4">Details</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Started</dt>
                <dd>{formatDateTime(scan.started_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Completed</dt>
                <dd>{formatDateTime(scan.completed_at)}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Profile</dt>
                <dd>{scan.profile}</dd>
              </div>
            </dl>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-4">Live Events</h3>
            <div className="space-y-2 max-h-64 overflow-y-auto text-xs font-mono">
              {events.slice(-20).reverse().map((ev, i) => (
                <div key={i} className="text-gray-500">
                  <span className="text-primary-400">{ev.event}</span>
                  {ev.data?.tool && <span className="text-gray-400"> [{ev.data.tool}]</span>}
                </div>
              ))}
              {events.length === 0 && <p className="text-gray-600">No events yet</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
