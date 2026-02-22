import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useParams } from 'react-router-dom'
import { reportsApi, ReportData } from '../api/reports'
import Modal from '../components/common/Modal'
import { formatDateTime } from '../utils/formatters'

export default function Reports() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({
    name: '',
    template: 'executive_summary',
    format: 'pdf',
  })

  const { data: reports, isLoading } = useQuery({
    queryKey: ['reports', projectId],
    queryFn: () => projectId ? reportsApi.listByProject(projectId) : Promise.resolve([]),
    enabled: !!projectId,
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => reportsApi.create(projectId!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reports', projectId] })
      setShowCreate(false)
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-gray-500 mt-1">
            {projectId ? `${reports?.length || 0} reports` : 'Select a project to view reports'}
          </p>
        </div>
        {projectId && (
          <button onClick={() => setShowCreate(true)} className="btn-primary">+ Generate Report</button>
        )}
      </div>

      {!projectId ? (
        <div className="card text-center py-12">
          <p className="text-gray-500">Navigate to a project to generate and view reports.</p>
        </div>
      ) : isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-3">
          {reports?.map((report: ReportData) => (
            <div key={report.id} className="card flex items-center justify-between">
              <div>
                <div className="font-medium">{report.name}</div>
                <div className="text-xs text-gray-500 mt-1">
                  {report.template} · {report.format.toUpperCase()} · {formatDateTime(report.created_at)}
                </div>
              </div>
              <div className="flex gap-2">
                {report.file_path && (
                  <button
                    onClick={() => reportsApi.download(report.id)}
                    className="btn-secondary text-sm"
                  >
                    ⬇ Download
                  </button>
                )}
                <span className={`text-xs px-2 py-1 rounded ${report.file_path ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-400'}`}>
                  {report.file_path ? 'Ready' : 'Generating...'}
                </span>
              </div>
            </div>
          ))}
          {reports?.length === 0 && (
            <div className="text-center py-12 text-gray-500">No reports yet</div>
          )}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Generate Report">
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Report Name</label>
            <input type="text" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} className="input w-full" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Template</label>
            <select value={form.template} onChange={e => setForm({ ...form, template: e.target.value })} className="input w-full">
              <option value="executive_summary">Executive Summary</option>
              <option value="technical_report">Technical Report</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Format</label>
            <select value={form.format} onChange={e => setForm({ ...form, format: e.target.value })} className="input w-full">
              <option value="pdf">PDF</option>
              <option value="html">HTML</option>
              <option value="json">JSON</option>
              <option value="csv">CSV</option>
            </select>
          </div>
          <button type="submit" disabled={createMutation.isPending} className="btn-primary w-full">
            {createMutation.isPending ? 'Generating...' : '📄 Generate Report'}
          </button>
        </form>
      </Modal>
    </div>
  )
}
