import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import apiClient from '../api/client'
import Modal from '../components/common/Modal'
import { ROLES } from '../utils/constants'
import { formatDateTime } from '../utils/formatters'
import type { User } from '../types/user'

export default function Team() {
  const queryClient = useQueryClient()
  const [showCreate, setShowCreate] = useState(false)
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'pentester' })

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => apiClient.get('/users', { params: { per_page: 100 } }).then(r => r.data.items as User[]),
  })

  const createMutation = useMutation({
    mutationFn: (data: typeof form) => apiClient.post('/users', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] })
      setShowCreate(false)
      setForm({ email: '', full_name: '', password: '', role: 'pentester' })
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      apiClient.put(`/users/${id}`, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Team Management</h1>
          <p className="text-gray-500 mt-1">{users?.length || 0} members</p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn-primary">+ Add Member</button>
      </div>

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : (
        <div className="space-y-3">
          {users?.map((user: User) => (
            <div key={user.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-400 font-bold">
                  {user.full_name?.charAt(0)?.toUpperCase() || '?'}
                </div>
                <div>
                  <div className="font-medium">{user.full_name}</div>
                  <div className="text-xs text-gray-500">{user.email}</div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <span className={`text-xs px-2 py-0.5 rounded ${
                  user.role === 'admin' ? 'bg-red-500/20 text-red-400' :
                  user.role === 'lead' ? 'bg-purple-500/20 text-purple-400' :
                  user.role === 'pentester' ? 'bg-blue-500/20 text-blue-400' :
                  'bg-gray-500/20 text-gray-400'
                }`}>
                  {user.role}
                </span>
                <span className={`text-xs ${user.is_active ? 'text-green-400' : 'text-red-400'}`}>
                  {user.is_active ? '● Active' : '● Inactive'}
                </span>
                <button
                  onClick={() => toggleMutation.mutate({ id: user.id, is_active: !user.is_active })}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  {user.is_active ? 'Disable' : 'Enable'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="Add Team Member">
        <form onSubmit={(e) => { e.preventDefault(); createMutation.mutate(form) }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
            <input type="text" value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })} className="input w-full" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
            <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} className="input w-full" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
            <input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} className="input w-full" required minLength={8} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
            <select value={form.role} onChange={e => setForm({ ...form, role: e.target.value })} className="input w-full">
              {ROLES.map(r => <option key={r.value} value={r.value}>{r.label}</option>)}
            </select>
          </div>
          <button type="submit" disabled={createMutation.isPending} className="btn-primary w-full">
            {createMutation.isPending ? 'Creating...' : 'Create User'}
          </button>
        </form>
      </Modal>
    </div>
  )
}
