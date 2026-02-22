import { formatDateTime } from '../../utils/formatters'
import type { ScanJob } from '../../types/scan'

interface Props {
  jobs: ScanJob[]
}

export default function ScanTimeline({ jobs }: Props) {
  const phases = [...new Set(jobs.map(j => j.phase))]

  return (
    <div className="card">
      <h3 className="font-semibold mb-4">Timeline</h3>
      <div className="space-y-4">
        {phases.map(phase => {
          const phaseJobs = jobs.filter(j => j.phase === phase)
          const allDone = phaseJobs.every(j => ['completed', 'failed', 'skipped'].includes(j.status))
          const anyRunning = phaseJobs.some(j => j.status === 'running')

          return (
            <div key={phase} className="border-l-2 border-dark-600 pl-4 ml-2">
              <div className="flex items-center gap-2 mb-2">
                <span className={`text-lg ${anyRunning ? 'animate-pulse' : ''}`}>
                  {anyRunning ? '🔄' : allDone ? '✅' : '⏳'}
                </span>
                <span className="font-medium">{phase}</span>
              </div>
              <div className="space-y-1 ml-6">
                {phaseJobs.map(job => (
                  <div key={job.id} className="flex items-center gap-3 text-sm">
                    <span className={
                      job.status === 'completed' ? 'text-green-400' :
                      job.status === 'running' ? 'text-yellow-400' :
                      job.status === 'failed' ? 'text-red-400' :
                      'text-gray-500'
                    }>
                      {job.status === 'completed' ? '✓' : job.status === 'running' ? '●' : job.status === 'failed' ? '✗' : '○'}
                    </span>
                    <span className="text-gray-300">{job.tool_name}</span>
                    <span className="text-gray-600">→</span>
                    <span className="text-gray-500 text-xs">{job.target}</span>
                    {job.duration_seconds != null && (
                      <span className="text-gray-600 text-xs ml-auto">{job.duration_seconds}s</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
