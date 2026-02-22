import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { findingsApi } from '../api/findings'
import FindingCard from '../components/findings/FindingCard'
import FindingDetail from '../components/findings/FindingDetail'
import FindingFilters from '../components/findings/FindingFilters'
import SeverityChart from '../components/findings/SeverityChart'
import type { Finding } from '../types/finding'

export default function Findings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [severity, setSeverity] = useState('')
  const [status, setStatus] = useState('')
  const [tool, setTool] = useState('')
  const [selectedFinding, setSelectedFinding] = useState<Finding | null>(null)

  const { data: findings = [], isLoading } = useQuery({
    queryKey: ['findings', severity, status, tool],
    queryFn: () =>
      findingsApi.list({
        severity: severity || undefined,
        status: status || undefined,
        source_tool: tool || undefined,
      }),
  })

  // Auto-open finding from URL param
  const findingIdFromUrl = searchParams.get('id')
  const { data: urlFinding } = useQuery({
    queryKey: ['finding', findingIdFromUrl],
    queryFn: () => findingsApi.get(findingIdFromUrl!),
    enabled: !!findingIdFromUrl && !selectedFinding,
  })

  if (urlFinding && !selectedFinding) {
    setSelectedFinding(urlFinding)
  }

  const severityData: Record<string, number> = {}
  findings.forEach((f: Finding) => {
    severityData[f.severity] = (severityData[f.severity] || 0) + 1
  })

  const totalFindings = findings.length
  const criticalCount = severityData.critical || 0
  const highCount = severityData.high || 0

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Findings Explorer</h1>
        <p className="text-sm text-gray-500 mt-1">Browse and manage discovered vulnerabilities across all projects</p>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-4 gap-4">
        {[
          { label: 'Total Findings', value: totalFindings, color: 'text-gray-100' },
          { label: 'Critical', value: criticalCount, color: 'text-red-400' },
          { label: 'High', value: highCount, color: 'text-orange-400' },
          { label: 'Open', value: findings.filter((f: Finding) => f.status === 'open').length, color: 'text-yellow-400' },
        ].map((stat) => (
          <div key={stat.label} className="bg-dark-900 rounded-xl border border-dark-700 p-4 text-center">
            <p className={`text-3xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar: Filters + Chart */}
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
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Severity Distribution</h3>
            <SeverityChart data={severityData} />
          </div>
        </div>

        {/* Findings List */}
        <div className="lg:col-span-3 space-y-3">
          {isLoading ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center text-gray-500">
              Loading findings...
            </div>
          ) : findings.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center text-gray-500">
              No findings match your filters. Try adjusting the criteria.
            </div>
          ) : (
            findings.map((finding: Finding) => (
              <FindingCard
                key={finding.id}
                finding={finding}
                onClick={() => setSelectedFinding(finding)}
              />
            ))
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {selectedFinding && (
        <FindingDetail
          finding={selectedFinding}
          onClose={() => {
            setSelectedFinding(null)
            if (findingIdFromUrl) setSearchParams({})
          }}
        />
      )}
    </div>
  )
}
