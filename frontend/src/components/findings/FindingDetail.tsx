import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Finding } from '../../types/finding'
import { SeverityBadge, StatusBadge } from '../common/StatusBadge'
import { formatDateTime } from '../../utils/formatters'
import { findingsApi } from '../../api/findings'
import Button from '../common/Button'

interface Props {
  finding: Finding
  onClose: () => void
}

export default function FindingDetail({ finding, onClose }: Props) {
  const queryClient = useQueryClient()
  const [comment, setComment] = useState('')

  const updateStatus = useMutation({
    mutationFn: (status: string) => findingsApi.update(finding.id, { status } as any),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['findings'] }),
  })

  const addComment = useMutation({
    mutationFn: () => findingsApi.addComment(finding.id, comment),
    onSuccess: () => {
      setComment('')
      queryClient.invalidateQueries({ queryKey: ['findings'] })
    },
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-dark-900 rounded-xl border border-dark-700 w-full max-w-3xl max-h-[85vh] overflow-y-auto shadow-2xl">
        <div className="flex items-start justify-between p-6 border-b border-dark-700">
          <div className="flex-1 min-w-0">
            <h2 className="text-xl font-bold text-gray-100 truncate">{finding.title}</h2>
            <div className="flex items-center gap-3 mt-2">
              <SeverityBadge severity={finding.severity} />
              <StatusBadge status={finding.status} />
              <span className="text-xs text-gray-500">via {finding.source_tool}</span>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl ml-4">✕</button>
        </div>

        <div className="p-6 space-y-6">
          <section>
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Description</h3>
            <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {finding.description || 'No description provided.'}
            </p>
          </section>

          <section className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Target Host</h3>
              <p className="text-gray-200 text-sm font-mono">{finding.target_host ?? '—'}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Target URL</h3>
              <p className="text-gray-200 text-sm font-mono break-all">{finding.target_url ?? '—'}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Port</h3>
              <p className="text-gray-200 text-sm font-mono">{finding.target_port ?? '—'}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">Discovered</h3>
              <p className="text-gray-200 text-sm">{formatDateTime(finding.created_at)}</p>
            </div>
          </section>

          {finding.raw_evidence && (
            <section>
              <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Evidence</h3>
              <pre className="bg-dark-950 border border-dark-700 rounded-lg p-4 text-xs text-green-400 overflow-x-auto font-mono">
                {JSON.stringify(finding.raw_evidence, null, 2)}
              </pre>
            </section>
          )}

          {(finding.cve_id || finding.cwe_id) && (
            <section className="flex gap-6">
              {finding.cve_id && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">CVE</h3>
                  <p className="text-orange-400 text-sm font-mono">{finding.cve_id}</p>
                </div>
              )}
              {finding.cwe_id && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">CWE</h3>
                  <p className="text-orange-400 text-sm font-mono">{finding.cwe_id}</p>
                </div>
              )}
              {finding.cvss_score != null && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-1">CVSS</h3>
                  <p className="text-yellow-400 text-sm font-mono">{finding.cvss_score}</p>
                </div>
              )}
            </section>
          )}

          <section>
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Update Status</h3>
            <div className="flex gap-2 flex-wrap">
              {['open', 'confirmed', 'false_positive', 'accepted_risk', 'remediated'].map((s) => (
                <Button
                  key={s}
                  variant={finding.status === s ? 'primary' : 'secondary'}
                  size="sm"
                  onClick={() => updateStatus.mutate(s)}
                  loading={updateStatus.isPending}
                >
                  {s.replace(/_/g, ' ')}
                </Button>
              ))}
            </div>
          </section>

          <section>
            <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Add Comment</h3>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={3}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
              placeholder="Write a comment..."
            />
            <div className="mt-2 flex justify-end">
              <Button size="sm" onClick={() => addComment.mutate()} disabled={!comment.trim()} loading={addComment.isPending}>
                Post Comment
              </Button>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
