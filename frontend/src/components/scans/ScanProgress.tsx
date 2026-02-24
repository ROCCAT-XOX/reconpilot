import { StatusBadge } from '../common/StatusBadge'
import { useScanStore, ToolProgress } from '../../store/scanStore'
import type { ScanJob } from '../../types/scan'

interface Props {
  jobs: ScanJob[]
  status: string
}

const toolStatusIcon: Record<string, string> = {
  queued: '○',
  running: '●',
  completed: '✓',
  failed: '✗',
  skipped: '—',
}

const toolStatusColor: Record<string, string> = {
  queued: 'text-gray-500',
  running: 'text-yellow-400 animate-pulse',
  completed: 'text-green-400',
  failed: 'text-red-400',
  skipped: 'text-gray-600',
}

export default function ScanProgress({ jobs, status }: Props) {
  const wsToolProgress = useScanStore((s) => s.toolProgress)
  const logLines = useScanStore((s) => s.logLines)

  const total = jobs.length
  const completed = jobs.filter(j => j.status === 'completed').length
  const failed = jobs.filter(j => j.status === 'failed').length
  const running = jobs.filter(j => j.status === 'running').length
  const progress = total > 0 ? Math.round(((completed + failed) / total) * 100) : 0

  // Merge WS tool progress with job data
  const getToolStatus = (job: ScanJob): ToolProgress => {
    const ws = wsToolProgress[job.tool_name]
    if (ws) return ws
    return {
      tool: job.tool_name,
      status: job.status as ToolProgress['status'],
      startedAt: job.started_at || undefined,
      completedAt: job.completed_at || undefined,
      error: job.error_message || undefined,
    }
  }

  return (
    <div className="space-y-4">
      {/* Progress card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold">Scan Progress</h3>
          <StatusBadge status={status} />
        </div>

        {/* Progress bar */}
        <div className="w-full bg-dark-700 rounded-full h-3 mb-1 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all duration-500 ${
              status === 'failed' ? 'bg-red-500' :
              status === 'completed' ? 'bg-green-500' :
              'bg-primary-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
        <div className="text-xs text-gray-500 text-right mb-4">{progress}%</div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center text-sm">
          <div>
            <div className="text-2xl font-bold text-gray-200">{total}</div>
            <div className="text-gray-500 text-xs">Total</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-400">{completed}</div>
            <div className="text-gray-500 text-xs">Done</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-yellow-400">{running}</div>
            <div className="text-gray-500 text-xs">Running</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-red-400">{failed}</div>
            <div className="text-gray-500 text-xs">Failed</div>
          </div>
        </div>
      </div>

      {/* Tool progress list */}
      {jobs.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Tool Progress</h3>
          <div className="space-y-2">
            {jobs.map((job) => {
              const tp = getToolStatus(job)
              const pct = tp.progress ?? (tp.status === 'completed' ? 100 : tp.status === 'running' ? undefined : 0)

              return (
                <div key={job.id} className="flex items-center gap-3 text-sm">
                  <span className={`w-4 text-center ${toolStatusColor[tp.status] || 'text-gray-500'}`}>
                    {toolStatusIcon[tp.status] || '○'}
                  </span>
                  <span className="text-gray-200 w-24 truncate font-medium">{job.tool_name}</span>
                  <div className="flex-1 bg-dark-700 rounded-full h-1.5 overflow-hidden">
                    {pct !== undefined ? (
                      <div
                        className={`h-full rounded-full transition-all duration-300 ${
                          tp.status === 'failed' ? 'bg-red-500' :
                          tp.status === 'completed' ? 'bg-green-500' :
                          'bg-primary-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    ) : tp.status === 'running' ? (
                      <div className="h-full bg-primary-500/60 rounded-full animate-pulse w-full" />
                    ) : null}
                  </div>
                  <span className="text-xs text-gray-500 w-16 text-right">
                    {tp.status === 'running' && pct !== undefined ? `${pct}%` : tp.status}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Live log output */}
      {logLines.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">Live Output</h3>
          <div className="bg-dark-950 rounded-lg p-3 max-h-48 overflow-y-auto font-mono text-xs text-gray-400 space-y-0.5">
            {logLines.slice(-50).map((line, i) => (
              <div key={i} className="whitespace-pre-wrap break-all">{line}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
