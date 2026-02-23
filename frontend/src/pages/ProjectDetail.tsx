import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { projectsApi } from '../api/projects'
import { scansApi } from '../api/scans'
import { findingsApi } from '../api/findings'
import { StatusBadge, SeverityBadge } from '../components/common/StatusBadge'
import Modal from '../components/common/Modal'
import ScanConfigurator from '../components/scans/ScanConfigurator'
import { formatDate, formatDateTime } from '../utils/formatters'

export default function ProjectDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showScanConfig, setShowScanConfig] = useState(false)
  const [showAddScope, setShowAddScope] = useState(false)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [scopeForm, setScopeForm] = useState({ target_type: 'domain', target_value: '', is_excluded: false })
  const [activeTab, setActiveTab] = useState<'overview' | 'scope' | 'scans' | 'findings'>('overview')

  const { data: project } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
  })

  const { data: scans } = useQuery({
    queryKey: ['scans', id],
    queryFn: () => scansApi.listByProject(id!),
    enabled: !!id,
  })

  const { data: scope } = useQuery({
    queryKey: ['scope', id],
    queryFn: () => projectsApi.listScope(id!),
    enabled: !!id,
  })

  const { data: findings } = useQuery({
    queryKey: ['findings', id],
    queryFn: () => findingsApi.listByProject(id!),
    enabled: !!id,
  })

  const { data: stats } = useQuery({
    queryKey: ['finding-stats', id],
    queryFn: () => findingsApi.getStats(id!),
    enabled: !!id,
  })

  const createScanMutation = useMutation({
    mutationFn: (data: any) => scansApi.create(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans', id] })
      setShowScanConfig(false)
    },
  })

  const addScopeMutation = useMutation({
    mutationFn: (data: any) => projectsApi.addScope(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scope', id] })
      setShowAddScope(false)
      setScopeForm({ target_type: 'domain', target_value: '', is_excluded: false })
    },
  })

  const deleteMutation = useMutation({
    mutationFn: () => projectsApi.deletePermanent(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate('/projects')
    },
  })

  if (!project) return <div className="text-center py-12 text-gray-500">Loading...</div>

  const includedScope = scope?.filter((s: any) => !s.is_excluded) || []
  const excludedScope = scope?.filter((s: any) => s.is_excluded) || []

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'scope', label: `Scope (${scope?.length || 0})` },
    { key: 'scans', label: `Scans (${scans?.length || 0})` },
    { key: 'findings', label: `Findings (${findings?.length || 0})` },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">{project.name}</h1>
            <StatusBadge status={project.status} />
          </div>
          <p className="text-gray-500 mt-1">{project.client_name}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={() => setShowScanConfig(true)} className="btn-primary">🚀 New Scan</button>
          <div className="relative group">
            <button className="px-3 py-2 text-gray-400 hover:text-gray-200 border border-dark-700 rounded-lg text-sm">
              ⋮
            </button>
            <div className="absolute right-0 mt-1 w-48 bg-dark-800 border border-dark-700 rounded-lg shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="w-full text-left px-4 py-2 text-sm text-red-400 hover:bg-dark-700 rounded-lg"
              >
                🗑️ Delete Project
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-dark-700">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key as any)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="font-semibold mb-4">Project Info</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-gray-500">Client</dt>
                <dd>{project.client_name}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Status</dt>
                <dd><StatusBadge status={project.status} /></dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-500">Created</dt>
                <dd>{formatDate(project.created_at)}</dd>
              </div>
              {project.description && (
                <div>
                  <dt className="text-gray-500 mb-1">Description</dt>
                  <dd className="text-gray-300">{project.description}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="card">
            <h3 className="font-semibold mb-4">Finding Summary</h3>
            {stats ? (
              <div className="grid grid-cols-5 gap-2 text-center">
                {Object.entries(stats.by_severity).map(([sev, count]) => (
                  <div key={sev}>
                    <div className="text-2xl font-bold">
                      <SeverityBadge severity={sev} />
                    </div>
                    <div className="text-lg font-bold mt-1">{count as number}</div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6">
                <div className="text-3xl mb-2">🔍</div>
                <p className="text-gray-500 text-sm">No findings yet</p>
                <p className="text-gray-600 text-xs mt-1">Run a scan to discover vulnerabilities</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scope Tab */}
      {activeTab === 'scope' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded">
                ✓ {includedScope.length} included
              </span>
              {excludedScope.length > 0 && (
                <span className="text-xs bg-red-500/20 text-red-400 px-2 py-1 rounded">
                  ✕ {excludedScope.length} excluded
                </span>
              )}
            </div>
            <button onClick={() => setShowAddScope(true)} className="btn-primary text-sm">+ Add Target</button>
          </div>
          {scope && scope.length > 0 ? (
            <div className="space-y-2">
              {scope.map((s: any) => (
                <div key={s.id} className="card flex items-center justify-between py-3">
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${s.is_excluded ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
                      {s.is_excluded ? 'EXCLUDED' : s.target_type.toUpperCase()}
                    </span>
                    <span className="font-mono text-sm">{s.target_value}</span>
                  </div>
                  {s.notes && <span className="text-xs text-gray-500">{s.notes}</span>}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="text-3xl mb-2">🎯</div>
              <p className="text-gray-500">No scope targets defined</p>
              <p className="text-gray-600 text-xs mt-1">Add targets to define your engagement scope</p>
            </div>
          )}
        </div>
      )}

      {/* Scans Tab */}
      {activeTab === 'scans' && (
        <div className="space-y-3">
          {scans && scans.length > 0 ? (
            scans.map((scan: any) => (
              <div
                key={scan.id}
                onClick={() => navigate(`/scans/${scan.id}`)}
                className="card cursor-pointer hover:border-dark-500 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{scan.name || scan.profile}</div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatDateTime(scan.created_at)}
                    </div>
                  </div>
                  <StatusBadge status={scan.status} />
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8">
              <div className="text-3xl mb-2">📡</div>
              <p className="text-gray-500">No scans yet</p>
              <p className="text-gray-600 text-xs mt-1">Start a scan to begin reconnaissance</p>
            </div>
          )}
        </div>
      )}

      {/* Findings Tab */}
      {activeTab === 'findings' && (
        <div className="space-y-3">
          {findings && findings.length > 0 ? (
            <>
              <div className="flex justify-end">
                <button
                  onClick={() => navigate(`/projects/${id}/findings`)}
                  className="text-sm text-primary-400 hover:text-primary-300"
                >
                  View in Findings Explorer →
                </button>
              </div>
              {findings.map((f: any) => (
                <div key={f.id} className="card cursor-pointer hover:border-dark-500" onClick={() => navigate(`/findings/${f.id}`)}>
                  <div className="flex items-center gap-3">
                    <SeverityBadge severity={f.severity} />
                    <span className="font-medium text-sm flex-1 truncate">{f.title}</span>
                    <span className="text-xs text-gray-500">{f.source_tool}</span>
                    <StatusBadge status={f.status} />
                  </div>
                </div>
              ))}
            </>
          ) : (
            <div className="text-center py-8">
              <div className="text-3xl mb-2">🛡️</div>
              <p className="text-gray-500">No findings yet</p>
              <p className="text-gray-600 text-xs mt-1">Findings will appear here after scans complete</p>
            </div>
          )}
        </div>
      )}

      {/* Scan Config Modal */}
      <Modal open={showScanConfig} onClose={() => setShowScanConfig(false)} title="Configure Scan" size="lg">
        <ScanConfigurator
          scopeTargets={scope || []}
          onStart={(config) => createScanMutation.mutate(config)}
          onClose={() => setShowScanConfig(false)}
          loading={createScanMutation.isPending}
        />
      </Modal>

      {/* Add Scope Modal */}
      <Modal open={showAddScope} onClose={() => setShowAddScope(false)} title="Add Scope Target">
        <form onSubmit={(e) => { e.preventDefault(); addScopeMutation.mutate(scopeForm) }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Type</label>
            <select
              value={scopeForm.target_type}
              onChange={e => setScopeForm({ ...scopeForm, target_type: e.target.value })}
              className="input w-full"
            >
              <option value="domain">Domain</option>
              <option value="ip">IP Address</option>
              <option value="ip_range">IP Range (CIDR)</option>
              <option value="url">URL</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Target</label>
            <input
              type="text"
              value={scopeForm.target_value}
              onChange={e => setScopeForm({ ...scopeForm, target_value: e.target.value })}
              className="input w-full"
              placeholder="e.g., example.com"
              required
            />
          </div>
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={scopeForm.is_excluded}
              onChange={e => setScopeForm({ ...scopeForm, is_excluded: e.target.checked })}
            />
            <span className="text-gray-400">Exclude from scope</span>
          </label>
          <button type="submit" className="btn-primary w-full">Add Target</button>
        </form>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal open={showDeleteConfirm} onClose={() => setShowDeleteConfirm(false)} title="Delete Project">
        <div className="space-y-4">
          <p className="text-gray-300 text-sm">
            Delete project <strong>{project.name}</strong>? This will permanently remove all scans and findings.
          </p>
          <div className="flex gap-3 justify-end">
            <button
              onClick={() => setShowDeleteConfirm(false)}
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200"
            >
              Cancel
            </button>
            <button
              onClick={() => deleteMutation.mutate()}
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
