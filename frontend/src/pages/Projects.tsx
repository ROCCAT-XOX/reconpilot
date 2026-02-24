import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../api/projects'
import { StatusBadge } from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import { formatDate } from '../utils/formatters'
import type { Project } from '../types/project'

export default function Projects() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<Project | null>(null)
  const [form, setForm] = useState({ name: '', client_name: '', description: '' })

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: projectsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => projectsApi.create(data),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setShowCreate(false)
      setForm({ name: '', client_name: '', description: '' })
      navigate(`/projects/${project.id}`)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => projectsApi.deletePermanent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      setDeleteTarget(null)
    },
  })

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(form)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Projects</h1>
          <p className="text-gray-500 mt-1">{projects?.length || 0} projects</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary min-h-[44px]">+ New Project</button>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1,2,3].map(i => (
            <div key={i} className="card animate-pulse">
              <div className="h-5 bg-dark-700 rounded w-1/2 mb-3" />
              <div className="h-4 bg-dark-700 rounded w-1/3 mb-3" />
              <div className="h-3 bg-dark-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      ) : projects && projects.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project: Project) => (
            <div
              key={project.id}
              className="card cursor-pointer hover:border-dark-500 transition-colors relative group"
            >
              <div onClick={() => navigate(`/projects/${project.id}`)} className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold truncate">{project.name}</h3>
                  <StatusBadge status={project.status} />
                </div>
                <p className="text-sm text-gray-500 mb-3">{project.client_name}</p>
                {project.description && (
                  <p className="text-xs text-gray-600 line-clamp-2 mb-3">{project.description}</p>
                )}
                <div className="text-xs text-gray-600">Created {formatDate(project.created_at)}</div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); setDeleteTarget(project) }}
                className="absolute top-3 right-3 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete project"
              >
                🗑️
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <div className="text-4xl mb-3">📁</div>
          <p className="text-gray-400 text-lg">No projects yet</p>
          <p className="text-gray-600 text-sm mt-1">Create your first project to get started</p>
          <button onClick={() => setShowCreate(true)} className="btn-primary mt-4">+ New Project</button>
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="New Project">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Project Name</label>
            <input
              type="text"
              value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })}
              className="input w-full"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Client Name</label>
            <input
              type="text"
              value={form.client_name}
              onChange={e => setForm({ ...form, client_name: e.target.value })}
              className="input w-full"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Description</label>
            <textarea
              value={form.description}
              onChange={e => setForm({ ...form, description: e.target.value })}
              className="input w-full h-24"
            />
          </div>
          <button type="submit" disabled={createMutation.isPending} className="btn-primary w-full">
            {createMutation.isPending ? 'Creating...' : 'Create Project'}
          </button>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <Modal open={!!deleteTarget} onClose={() => setDeleteTarget(null)} title="Delete Project">
        <div className="space-y-4">
          <p className="text-gray-300 text-sm">
            Delete project <strong>{deleteTarget?.name}</strong>? This will permanently remove all scans and findings.
          </p>
          <div className="flex gap-3 justify-end">
            <button onClick={() => setDeleteTarget(null)} className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200">
              Cancel
            </button>
            <button
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
              disabled={deleteMutation.isPending}
              className="px-4 py-2 text-sm bg-red-500/20 text-red-400 border border-red-500/30 rounded-lg hover:bg-red-500/30 disabled:opacity-50"
            >
              {deleteMutation.isPending ? 'Deleting...' : '🗑️ Delete Permanently'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
