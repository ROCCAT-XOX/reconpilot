import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { findingsApi } from '../api/findings'
import { SeverityBadge, StatusBadge } from '../components/common/StatusBadge'
import { formatDateTime } from '../utils/formatters'
import { STATUS_OPTIONS } from '../utils/constants'
import type { Finding } from '../types/finding'

export default function FindingDetail() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()
  const [newComment, setNewComment] = useState('')

  const { data: finding } = useQuery({
    queryKey: ['finding', id],
    queryFn: () => findingsApi.get(id!),
    enabled: !!id,
  })

  const { data: comments } = useQuery({
    queryKey: ['finding-comments', id],
    queryFn: () => findingsApi.listComments(id!),
    enabled: !!id,
  })

  const updateMutation = useMutation({
    mutationFn: (data: Partial<Finding>) => findingsApi.update(id!, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['finding', id] }),
  })

  const commentMutation = useMutation({
    mutationFn: (content: string) => findingsApi.addComment(id!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['finding-comments', id] })
      setNewComment('')
    },
  })

  const verifyMutation = useMutation({
    mutationFn: () => findingsApi.verify(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['finding', id] }),
  })

  if (!finding) return <div className="text-center py-12 text-gray-500">Loading...</div>

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-3 mb-2">
          <SeverityBadge severity={finding.severity} />
          <StatusBadge status={finding.status} />
        </div>
        <h1 className="text-2xl font-bold">{finding.title}</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="card">
            <h3 className="font-semibold mb-3">Description</h3>
            <p className="text-sm text-gray-300 whitespace-pre-wrap">
              {finding.description || 'No description available'}
            </p>
          </div>

          {/* Evidence */}
          {finding.raw_evidence && (
            <div className="card">
              <h3 className="font-semibold mb-3">Evidence</h3>
              <pre className="text-xs text-gray-400 bg-dark-950 rounded-lg p-4 overflow-x-auto">
                {JSON.stringify(finding.raw_evidence, null, 2)}
              </pre>
            </div>
          )}

          {/* Comments */}
          <div className="card">
            <h3 className="font-semibold mb-4">Comments ({comments?.length || 0})</h3>
            <div className="space-y-3 mb-4">
              {comments?.map(c => (
                <div key={c.id} className="bg-dark-800/50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-500">{c.user_id || 'System'}</span>
                    <span className="text-xs text-gray-600">{formatDateTime(c.created_at)}</span>
                  </div>
                  <p className="text-sm text-gray-300">{c.content}</p>
                </div>
              ))}
            </div>
            <form onSubmit={(e) => { e.preventDefault(); commentMutation.mutate(newComment) }} className="flex gap-2">
              <input
                value={newComment}
                onChange={e => setNewComment(e.target.value)}
                className="input flex-1"
                placeholder="Add a comment..."
                required
              />
              <button type="submit" className="btn-primary text-sm">Send</button>
            </form>
          </div>
        </div>

        <div className="space-y-6">
          {/* Details */}
          <div className="card">
            <h3 className="font-semibold mb-3">Details</h3>
            <dl className="space-y-2 text-sm">
              {finding.target_host && (
                <div className="flex justify-between"><dt className="text-gray-500">Host</dt><dd className="font-mono">{finding.target_host}</dd></div>
              )}
              {finding.target_port && (
                <div className="flex justify-between"><dt className="text-gray-500">Port</dt><dd>{finding.target_port}</dd></div>
              )}
              {finding.target_url && (
                <div className="flex justify-between"><dt className="text-gray-500">URL</dt><dd className="font-mono text-xs truncate max-w-[200px]">{finding.target_url}</dd></div>
              )}
              {finding.cve_id && (
                <div className="flex justify-between"><dt className="text-gray-500">CVE</dt><dd className="text-orange-400">{finding.cve_id}</dd></div>
              )}
              {finding.cwe_id && (
                <div className="flex justify-between"><dt className="text-gray-500">CWE</dt><dd>{finding.cwe_id}</dd></div>
              )}
              <div className="flex justify-between"><dt className="text-gray-500">Tool</dt><dd>{finding.source_tool}</dd></div>
              <div className="flex justify-between"><dt className="text-gray-500">Found</dt><dd>{formatDateTime(finding.created_at)}</dd></div>
            </dl>
          </div>

          {/* Actions */}
          <div className="card">
            <h3 className="font-semibold mb-3">Actions</h3>
            <div className="space-y-2">
              <select
                value={finding.status}
                onChange={e => updateMutation.mutate({ status: e.target.value as any })}
                className="input w-full text-sm"
              >
                {STATUS_OPTIONS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
              {finding.status === 'open' && (
                <button onClick={() => verifyMutation.mutate()} className="btn-primary w-full text-sm">
                  ✓ Verify Finding
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
