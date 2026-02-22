import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi, ReportData } from '../api/reports'
import { projectsApi } from '../api/projects'
import Button from '../components/common/Button'
import type { Project } from '../types/project'

export default function Reports() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const [selectedProject, setSelectedProject] = useState(searchParams.get('project') || '')
  const [reportType, setReportType] = useState<'executive' | 'technical' | 'full'>('full')
  const [title, setTitle] = useState('')

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

  const statusStyles: Record<string, string> = {
    generating: 'text-yellow-400 bg-yellow-400/10',
    completed: 'text-green-400 bg-green-400/10',
    failed: 'text-red-400 bg-red-400/10',
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Generate and download penetration test reports</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generator */}
        <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-200">Generate Report</h3>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Project</label>
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="">Select a project...</option>
              {projects.map((p: Project) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Report Type</label>
            <div className="flex gap-2">
              {(['executive', 'technical', 'full'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setReportType(t)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-colors ${
                    reportType === t ? 'bg-primary-600 text-white' : 'bg-dark-800 text-gray-400 hover:bg-dark-700'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Title (optional)</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Penetration Test Report — Q1 2026"
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>

          <Button
            onClick={() => generateMutation.mutate()}
            loading={generateMutation.isPending}
            disabled={!selectedProject}
            className="w-full"
          >
            Generate Report
          </Button>
        </div>

        {/* List */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Reports ({reports.length})
          </h3>
          {isLoading ? (
            <p className="text-gray-500 text-sm">Loading...</p>
          ) : reports.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-8 text-center text-gray-500 text-sm">
              No reports yet.
            </div>
          ) : (
            reports.map((report: ReportData) => (
              <div key={report.id} className="bg-dark-900 rounded-xl border border-dark-700 p-4 flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-semibold text-gray-200">{report.title || 'Untitled'}</h4>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="text-xs text-gray-500 capitalize">{report.report_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full capitalize ${statusStyles[report.status] || ''}`}>
                      {report.status}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  {report.status === 'completed' && (
                    <Button size="sm" onClick={() => handleDownload(report.id)}>Download</Button>
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
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  )
}
