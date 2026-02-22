import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi } from '../api/reports'
import { projectsApi } from '../api/projects'
import ReportBuilder, { ReportConfig } from '../components/reports/ReportBuilder'
import ReportPreview from '../components/reports/ReportPreview'
import type { Project } from '../types/project'

export default function Reports() {
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const projectIdFromUrl = searchParams.get('project')
  const [selectedProject, setSelectedProject] = useState(projectIdFromUrl || '')

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['reports', selectedProject],
    queryFn: () => reportsApi.list(selectedProject || undefined),
  })

  const generateMutation = useMutation({
    mutationFn: (config: ReportConfig & { project_id: string }) => reportsApi.generate(config),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => reportsApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['reports'] }),
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

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Reports</h1>
        <p className="text-sm text-gray-500 mt-1">Generate and manage penetration test reports</p>
      </div>

      {/* Project Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Select Project</label>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50 w-full max-w-md"
        >
          <option value="">All Projects</option>
          {projects.map((p: Project) => (
            <option key={p.id} value={p.id}>{p.name} — {p.client_name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Builder */}
        {selectedProject && (
          <ReportBuilder
            projectId={selectedProject}
            onGenerate={(config) =>
              generateMutation.mutate({ ...config, project_id: selectedProject })
            }
            loading={generateMutation.isPending}
          />
        )}

        {/* Report List */}
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
            Generated Reports ({reports.length})
          </h3>
          {isLoading ? (
            <p className="text-gray-500 text-sm">Loading reports...</p>
          ) : reports.length === 0 ? (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-8 text-center text-gray-500 text-sm">
              No reports generated yet.{' '}
              {!selectedProject && 'Select a project to create one.'}
            </div>
          ) : (
            reports.map((report: any) => (
              <ReportPreview
                key={report.id}
                report={report}
                onDownload={handleDownload}
                onDelete={(id) => deleteMutation.mutate(id)}
              />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
