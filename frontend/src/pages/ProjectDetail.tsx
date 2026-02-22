import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../api/projects'
import { useProjectScans, useStartScan } from '../hooks/useScans'
import { useProjectFindings } from '../hooks/useFindings'
import { StatusBadge } from '../components/common/StatusBadge'
import SeverityChart from '../components/findings/SeverityChart'
import ScanConfigurator from '../components/scans/ScanConfigurator'
import ScanTimeline from '../components/scans/ScanTimeline'
import FindingCard from '../components/findings/FindingCard'
import Button from '../components/common/Button'
import { formatDate } from '../utils/formatters'
import type { Project } from '../types/project'

export default function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [tab, setTab] = useState<'overview' | 'scans' | 'findings' | 'scope'>('overview')
  const [showScanConfig, setShowScanConfig] = useState(false)

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectsApi.get(projectId!),
    enabled: !!projectId,
  })

  const { data: scans = [] } = useProjectScans(projectId)
  const { data: findings = [] } = useProjectFindings(projectId)
  const startScan = useStartScan()

  const severityData: Record<string, number> = {}
  findings.forEach((f: any) => {
    severityData[f.severity] = (severityData[f.severity] || 0) + 1
  })

  if (isLoading) {
    return <div className="p-6 text-gray-500">Loading project...</div>
  }

  if (!project) {
    return <div className="p-6 text-gray-500">Project not found.</div>
  }

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'scans', label: `Scans (${scans.length})` },
    { key: 'findings', label: `Findings (${findings.length})` },
    { key: 'scope', label: 'Scope' },
  ] as const

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <button onClick={() => navigate('/projects')} className="text-sm text-gray-500 hover:text-gray-300 mb-2 flex items-center gap-1">
            ← Back to Projects
          </button>
          <h1 className="text-2xl font-bold text-gray-100">{project.name}</h1>
          <div className="flex items-center gap-3 mt-2">
            <StatusBadge status={project.status} />
            <span className="text-sm text-gray-500">{project.client_name}</span>
            <span className="text-sm text-gray-600">|</span>
            <span className="text-sm text-gray-500">{formatDate(project.start_date)} — {formatDate(project.end_date)}</span>
          </div>
          {project.description && <p className="text-sm text-gray-400 mt-2 max-w-2xl">{project.description}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => navigate(`/reports?project=${projectId}`)}>Generate Report</Button>
          <Button onClick={() => setShowScanConfig(true)}>New Scan</Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-dark-700">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {tab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Stats */}
          <div className="grid grid-cols-2 gap-4">
            {[
              { label: 'Total Scans', value: scans.length, icon: '🔍' },
              { label: 'Findings', value: findings.length, icon: '🐛' },
              { label: 'Critical', value: severityData.critical || 0, icon: '🔴' },
              { label: 'High', value: severityData.high || 0, icon: '🟠' },
            ].map((stat) => (
              <div key={stat.label} className="bg-dark-900 rounded-xl border border-dark-700 p-4">
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{stat.icon}</span>
                  <span className="text-2xl font-bold text-gray-100">{stat.value}</span>
                </div>
                <p className="text-xs text-gray-500 mt-2">{stat.label}</p>
              </div>
            ))}
          </div>

          {/* Severity Chart */}
          <div className="bg-dark-900 rounded-xl border border-dark-700 p-4">
            <h3 className="text-sm font-semibold text-gray-400 mb-3">Findings by Severity</h3>
            <SeverityChart data={severityData} />
          </div>
        </div>
      )}

      {tab === 'scans' && (
        <div className="space-y-4">
          {scans.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center">
              <p className="text-gray-500 mb-4">No scans yet. Start your first scan.</p>
              <Button onClick={() => setShowScanConfig(true)}>Configure Scan</Button>
            </div>
          ) : (
            scans.map((scan: any) => (
              <div
                key={scan.id}
                onClick={() => navigate(`/scans/${scan.id}`)}
                className="bg-dark-900 rounded-xl border border-dark-700 p-4 hover:bg-dark-800/50 cursor-pointer transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-200">{scan.name || `Scan ${scan.id.slice(0, 8)}`}</h4>
                    <div className="flex items-center gap-3 mt-1">
                      <StatusBadge status={scan.status} />
                      <span className="text-xs text-gray-500 capitalize">{scan.profile} profile</span>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">{formatDate(scan.created_at)}</span>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {tab === 'findings' && (
        <div className="space-y-3">
          {findings.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-12 text-center text-gray-500">
              No findings discovered yet.
            </div>
          ) : (
            findings.map((f: any) => (
              <FindingCard key={f.id} finding={f} onClick={() => navigate(`/findings?id=${f.id}`)} />
            ))
          )}
        </div>
      )}

      {tab === 'scope' && (
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6">
          <h3 className="text-sm font-semibold text-gray-400 mb-4">Scope Targets</h3>
          <p className="text-gray-500 text-sm">Scope management coming soon. Define targets via the API.</p>
        </div>
      )}

      {/* Scan Config Modal */}
      {showScanConfig && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 w-full max-w-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-gray-100">New Scan</h3>
              <button onClick={() => setShowScanConfig(false)} className="text-gray-500 hover:text-gray-300">✕</button>
            </div>
            <ScanConfigurator
              onStart={(config) => {
                startScan.mutate(
                  { projectId: projectId!, ...config },
                  { onSuccess: () => setShowScanConfig(false) }
                )
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}
