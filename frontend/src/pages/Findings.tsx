import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { findingsApi } from '../api/findings'
import FindingCard from '../components/findings/FindingCard'
import FindingFilters from '../components/findings/FindingFilters'
import SeverityChart from '../components/findings/SeverityChart'
import type { Finding } from '../types/finding'

export default function Findings() {
  const [searchParams] = useSearchParams()
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [tool, setTool] = useState('')
  const projectId = searchParams.get('project') || undefined

  const { data: findings = [], isLoading } = useQuery({
    queryKey: ['findings', projectId, severity, status, tool],
    queryFn: () => {
      if (projectId) {
        return findingsApi.listByProject(projectId, {
          severity: severity || undefined,
          status: status || undefined,
          source_tool: tool || undefined,
        })
      }
      return findingsApi.list({
        severity: severity || undefined,
        status: status || undefined,
        source_tool: tool || undefined,
      })
    },
  })

  const severityData: Record<string, number> = {}
  findings.forEach((f: Finding) => {
    severityData[f.severity] = (severityData[f.severity] || 0) + 1
  })

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Findings Explorer</h1>
        <p className="text-sm text-gray-500 mt-1">Browse and manage discovered vulnerabilities</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total', value: findings.length, color: 'text-gray-100' },
          { label: 'Critical', value: severityData.critical || 0, color: 'text-red-400' },
          { label: 'High', value: severityData.high || 0, color: 'text-orange-400' },
          { label: 'Open', value: findings.filter((f: Finding) => f.status === 'open').length, color: 'text-yellow-400' },
        ].map((stat) => (
          <div key={stat.label} className="bg-dark-900 rounded-xl border border-dark-700 p-4 text-center">
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="space-y-6">
          <div className="bg-dark-900 rounded-xl border border-dark-700 p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Filters</h3>
            <FindingFilters
              severity={severity}
              status={status}
              tool={tool}
              onSeverityChange={setSeverity}
              onStatusChange={setStatus}
              onToolChange={setTool}
            />
          </div>
          <div className="bg-dark-900 rounded-xl border border-dark-700 p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Distribution</h3>
            <SeverityChart data={severityData} />
          </div>
        </div>

        <div className="lg:col-span-3 space-y-3">
          {isLoading ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center text-gray-500">Loading...</div>
          ) : findings.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center text-gray-500">No findings found.</div>
          ) : (
            findings.map((f: Finding) => <FindingCard key={f.id} finding={f} />)
          )}
        </div>
      </div>
    </div>
  )
}
