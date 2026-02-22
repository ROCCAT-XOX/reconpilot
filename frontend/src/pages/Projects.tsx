import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { projectsApi } from '../api/projects'
import type { Project, CreateProjectPayload } from '../types/project'
import { StatusBadge } from '../components/common/StatusBadge'
import { formatDate } from '../utils/formatters'
import Button from '../components/common/Button'
import Modal from '../components/common/Modal'

export default function Projects() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState<CreateProjectPayload>({ name: '', client_name: '', description: '' })

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: projectsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setForm({ name: '', client_name: '', description: '' })
    },
  })

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Projects</h1>
          <p className="text-sm text-gray-500 mt-1">Manage your penetration testing engagements</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>+ New Project</Button>
      </div>

      {/* Projects Table */}
      <div className="bg-dark-900 rounded-xl border border-dark-700 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700 text-left">
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Project</th>
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Client</th>
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Period</th>
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Scans</th>
              <th className="px-6 py-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">Findings</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-dark-800">
            {isLoading ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-500">Loading projects...</td></tr>
            ) : projects.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-12 text-center text-gray-500">No projects yet. Create your first engagement.</td></tr>
            ) : (
              projects.map((project: Project) => (
                <tr
                  key={project.id}
                  onClick={() => navigate(`/projects/${project.id}`)}
                  className="hover:bg-dark-800/50 cursor-pointer transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-200">{project.name}</div>
                    {project.description && (
                      <div className="text-xs text-gray-500 mt-0.5 truncate max-w-xs">{project.description}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{project.client_name}</td>
                  <td className="px-6 py-4"><StatusBadge status={project.status} /></td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {formatDate(project.start_date)} — {formatDate(project.end_date)}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-400">{project.scan_count ?? '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-400">{project.finding_count ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Project">
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Project Name</label>
            <input
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              required
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="External Pentest — Acme Corp"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Client Name</label>
            <input
              value={form.client_name}
              onChange={(e) => setForm((p) => ({ ...p, client_name: e.target.value }))}
              required
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Acme Corporation"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
            <textarea
              value={form.description || ''}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
              rows={3}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Scope and objectives..."
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">Start Date</label>
              <input
                type="date"
                value={form.start_date || ''}
                onChange={(e) => setForm((p) => ({ ...p, start_date: e.target.value }))}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-400 mb-1">End Date</label>
              <input
                type="date"
                value={form.end_date || ''}
                onChange={(e) => setForm((p) => ({ ...p, end_date: e.target.value }))}
                className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              />
            </div>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowCreate(false)}>Cancel</Button>
            <Button type="submit" loading={createMutation.isPending}>Create Project</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
