import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi, ReportData } from '../api/reports'
import { projectsApi } from '../api/projects'
import Button from '../components/common/Button'
import Modal from '../components/common/Modal'
import { SkeletonCard } from '../components/common/Skeleton'
import { formatDateTime } from '../utils/formatters'
import type { Project } from '../types/project'

const TEMPLATES = [
  { key: 'executive' as const, label: 'Executive Summary', icon: '📊', desc: 'High-level overview for management' },
  { key: 'technical' as const, label: 'Technical Detail', icon: '🔧', desc: 'Full technical findings & evidence' },
  { key: 'full' as const, label: 'Full Report', icon: '📋', desc: 'Complete report with all sections' },
]

export default function Reports() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selectedProject, setSelectedProject] = useState(searchParams.get('project') || '')
  const [reportType, setReportType] = useState<'executive' | 'technical' | 'full'>('full')
  const [title, setTitle] = useState('')
  const [severityFilter, setSeverityFilter] = useState<string[]>([])
  const [previewReport, setPreviewReport] = useState<ReportData | null>(null)
  const [previewHtml, setPreviewHtml] = useState<string>('')

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['reports', selectedProject],
    queryFn: () => selectedProject
      ? reportsApi.listByProject(selectedProject)
      : reportsApi.list(),
  })

  const generateMutation = useMutation({
    mutationFn: () =>
      reportsApi.generate({
        project_id: selectedProject,
        report_type: reportType,
        title: title || `${reportType.charAt(0).toUpperCase() + reportType.slice(1)} Report`,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports'] })
      setTitle('')
    },
  })

  const handleDownload = async (id: string) => {
    const blob = await reportsApi.download(id)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `report-${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handlePreview = async (report: ReportData) => {
    setPreviewReport(report)
    try {
      const blob = await reportsApi.download(report.id)
      const text = await blob.text()
      setPreviewHtml(text)
    } catch {
      setPreviewHtml('<p style="color:#999;text-center">Preview not available</p>')
    }
  }

  const statusStyles: Record<string, string> = {
    generating: 'text-yellow-400 bg-yellow-400/10',
    completed: 'text-green-400 bg-green-400/10',
    failed: 'text-red-400 bg-red-400/10',
  }

  const toggleSeverity = (sev: string) => {
    setSeverityFilter(prev =>
      prev.includes(sev) ? prev.filter(s => s !== sev) : [...prev, sev]
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl md:text-2xl font-bold text-gray-100">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Generate and download penetration test reports</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generator */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-4 md:p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-200">Generate Report</h3>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Project</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 min-h-[44px]"
            >
              <option value="">Select a project...</option>
              {projects.map((p: Project) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-2">Report Template</label>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              {TEMPLATES.map((t) => (
                <button
                  key={t.key}
                  onClick={() => setReportType(t.key)}
                  className={`p-3 rounded-lg text-left border transition-all min-h-[44px] ${
                    reportType === t.key
                      ? 'border-primary-500 bg-primary-500/10'
                      : 'border-dark-700 hover:border-dark-500'
                  }`}
                >
                  <div className="text-lg mb-1">{t.icon}</div>
                  <div className="text-sm font-medium">{t.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{t.desc}</div>
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Finding Severity Filter</label>
            <div className="flex flex-wrap gap-2">
              {['critical', 'high', 'medium', 'low', 'info'].map((sev) => (
                <button
                  key={sev}
                  onClick={() => toggleSeverity(sev)}
                  className={`px-3 py-1.5 rounded text-xs font-medium capitalize border transition-colors min-h-[36px] ${
                    severityFilter.includes(sev)
                      ? 'bg-primary-500/20 border-primary-500/50 text-primary-400'
                      : 'border-dark-600 text-gray-400 hover:border-dark-400'
                  }`}
                >
                  {sev}
                </button>
              ))}
              {severityFilter.length > 0 && (
                <button
                  onClick={() => setSeverityFilter([])}
                  className="px-2 py-1 text-xs text-gray-500 hover:text-gray-300"
                >
                  Clear
                </button>
              )}
            </div>
            <p className="text-xs text-gray-600 mt-1">
              {severityFilter.length === 0 ? 'All severities included' : `Filtering: ${severityFilter.join(', ')}`}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Title (optional)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Penetration Test Report — Q1 2026"
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 min-h-[44px]"
            />
          </div>

          <Button
            onClick={() => generateMutation.mutate()}
            loading={generateMutation.isPending}
            disabled={!selectedProject}
            className="w-full"
          >
            📄 Generate Report
          </Button>
        </div>

        {/* List */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Reports ({reports.length})
          </h3>
          {isLoading ? (
            <div className="space-y-3">
              <SkeletonCard />
              <SkeletonCard />
            </div>
          ) : reports.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-8 text-center">
              <div className="text-4xl mb-3">📄</div>
              <p className="text-gray-400">No reports yet</p>
              <p className="text-gray-600 text-xs mt-1">Generate your first report from a project</p>
            </div>
          ) : (
            reports.map((report: ReportData) => (
              <div key={report.id} className="bg-dark-900 rounded-xl border border-dark-700 p-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="min-w-0">
                    <h4 className="text-sm font-semibold text-gray-200 truncate">{report.title || 'Untitled'}</h4>
                    <div className="flex items-center gap-3 mt-1 flex-wrap">
                      <span className="text-xs text-gray-500 capitalize">{report.report_type}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${statusStyles[report.status] || ''}`}>
                        {report.status}
                      </span>
                      <span className="text-xs text-gray-600">{formatDateTime(report.created_at)}</span>
                    </div>
                  </div>
                  <div className="flex gap-2 shrink-0">
                    {report.status === 'completed' && (
                      <>
                        <Button size="sm" variant="ghost" onClick={() => handlePreview(report)}>
                          Preview
                        </Button>
                        <Button size="sm" onClick={() => handleDownload(report.id)}>
                          Download
                        </Button>
                      </>
                    )}
                    {report.status === 'generating' && (
                      <span className="text-yellow-400 text-xs flex items-center gap-1">
                        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                        </svg>
                        Generating...
                      </span>
                    )}
                    {report.status === 'failed' && (
                      <span className="text-red-400 text-xs">Generation failed</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Preview Modal */}
      <Modal
        open={!!previewReport}
        onClose={() => { setPreviewReport(null); setPreviewHtml('') }}
        title={previewReport?.title || 'Report Preview'}
        size="xl"
      >
        <div className="bg-white rounded-lg p-4 min-h-[400px] overflow-auto">
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="secondary" onClick={() => { setPreviewReport(null); setPreviewHtml('') }}>
            Close
          </Button>
          {previewReport && (
            <Button onClick={() => handleDownload(previewReport.id)}>
              Download PDF
            </Button>
          )}
        </div>
      </Modal>
    </div>
  )
}
