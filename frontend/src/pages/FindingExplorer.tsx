import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useProjectFindings, useFindingStats } from '../hooks/useFindings'
import FindingCard from '../components/findings/FindingCard'
import FindingFilters from '../components/findings/FindingFilters'
import SeverityChart from '../components/findings/SeverityChart'

export default function FindingExplorer() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [tool, setTool] = useState('')

  const filters = {
    ...(severity && { severity }),
    ...(status && { status }),
    ...(tool && { source_tool: tool }),
  }

  const { data: findings, isLoading } = useProjectFindings(projectId, filters)
  const { data: stats } = useFindingStats(projectId)

  const tools = stats?.by_tool ? Object.keys(stats.by_tool) : []

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Finding Explorer</h1>
        <p className="text-gray-500 mt-1">{findings?.length || 0} findings</p>
      </div>

      {stats && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="card lg:col-span-2">
            <div className="grid grid-cols-5 gap-4 text-center">
              {Object.entries(stats.by_severity).map(([sev, count]) => (
                <div key={sev} className="cursor-pointer" onClick={() => setSeverity(severity === sev ? '' : sev)}>
                  <div className="text-2xl font-bold">{count as number}</div>
                  <div className="text-xs text-gray-500 capitalize">{sev}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <SeverityChart data={stats.by_severity} />
          </div>
        </div>
      )}

      <FindingFilters
        severity={severity}
        status={status}
        tool={tool}
        onSeverityChange={setSeverity}
        onStatusChange={setStatus}
        onToolChange={setTool}
        tools={tools}
      />

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-3">
          {findings?.map(f => (
            <FindingCard
              key={f.id}
              finding={f}
              onClick={() => navigate(`/findings/${f.id}`)}
            />
          ))}
          {findings?.length === 0 && (
            <div className="text-center py-12 text-gray-500">No findings match the current filters</div>
          )}
        </div>
      )}
    </div>
  )
}
