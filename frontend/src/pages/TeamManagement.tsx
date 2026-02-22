import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import type { User } from '../types/user'
import Button from '../components/common/Button'
import Modal from '../components/common/Modal'
import { StatusBadge } from '../components/common/StatusBadge'
import { formatDateTime } from '../utils/formatters'

const usersApi = {
  list: () => apiClient.get<User[]>('/users').then((r) => r.data),
  create: (data: { email: string; full_name: string; role: string; password: string }) =>
    apiClient.post('/users', data).then((r) => r.data),
  update: (id: string, data: Partial<User>) =>
    apiClient.patch(`/users/${id}`, data).then((r) => r.data),
  deactivate: (id: string) =>
    apiClient.delete(`/users/${id}`).then((r) => r.data),
}

export default function TeamManagement() {
  const queryClient = useQueryClient()
  const [showInvite, setShowInvite] = useState(false)
  const [form, setForm] = useState({ email: '', full_name: '', role: 'pentester', password: '' })

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: usersApi.list,
  })

  const createMutation = useMutation({
    mutationFn: usersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowInvite(false)
      setForm({ email: '', full_name: '', role: 'pentester', password: '' })
    },
  })

  const toggleActive = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      usersApi.update(id, { is_active } as any),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  const roleColors: Record<string, string> = {
    admin: 'bg-red-500/10 text-red-400',
    lead: 'bg-purple-500/10 text-purple-400',
    pentester: 'bg-blue-500/10 text-blue-400',
    viewer: 'bg-gray-500/10 text-gray-400',
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Team Management</h1>
          <p className="text-sm text-gray-500 mt-1">Manage team members and access roles</p>
        </div>
        <Button onClick={() => setShowInvite(true)}>+ Add Member</Button>
      </div>

      {/* Team Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {isLoading ? (
          <p className="text-gray-500 col-span-3 text-center py-12">Loading team...</p>
        ) : (
          users.map((user: User) => (
            <div key={user.id} className="bg-dark-900 rounded-xl border border-dark-700 p-5">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-primary-600/20 flex items-center justify-center text-primary-400 font-bold text-sm">
                    {user.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-gray-200">{user.full_name}</h4>
                    <p className="text-xs text-gray-500">{user.email}</p>
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full capitalize ${roleColors[user.role] || roleColors.viewer}`}>
                  {user.role}
                </span>
              </div>
              <div className="flex items-center justify-between mt-4 pt-3 border-t border-dark-700">
                <span className="text-xs text-gray-500">
                  Joined {formatDateTime(user.created_at)}
                </span>
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${user.is_active ? 'bg-green-400' : 'bg-gray-600'}`} />
                  <button
                    onClick={() => toggleActive.mutate({ id: user.id, is_active: !user.is_active })}
                    className="text-xs text-gray-500 hover:text-gray-300"
                  >
                    {user.is_active ? 'Active' : 'Inactive'}
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Invite Modal */}
      <Modal open={showInvite} onClose={() => setShowInvite(false)} title="Add Team Member">
        <form
          onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }}
          className="space-y-4"
        >
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
            <input
              value={form.full_name}
              onChange={(e) => setForm((p) => ({ ...p, full_name: e.target.value }))}
              required
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))}
              required
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setForm((p) => ({ ...p, password: e.target.value }))}
              required
              minLength={8}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
            <select
              value={form.role}
              onChange={(e) => setForm((p) => ({ ...p, role: e.target.value }))}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
            >
              <option value="admin">Admin</option>
              <option value="lead">Lead</option>
              <option value="pentester">Pentester</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" type="button" onClick={() => setShowInvite(false)}>Cancel</Button>
            <Button type="submit" loading={createMutation.isPending}>Add Member</Button>
          </div>
        </form>
      </Modal>
    </div>
  )
}
