import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import apiClient from '../api/client'

export default function Settings() {
  const { user } = useAuthStore()
  const [passwordForm, setPasswordForm] = useState({ current: '', new_password: '', confirm: '' })
  const [message, setMessage] = useState('')

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    if (passwordForm.new_password !== passwordForm.confirm) {
      setMessage('Passwords do not match')
      return
    }
    try {
      await apiClient.put('/auth/password', {
        current_password: passwordForm.current,
        new_password: passwordForm.new_password,
      })
      setMessage('Password updated successfully')
      setPasswordForm({ current: '', new_password: '', confirm: '' })
    } catch {
      setMessage('Failed to update password')
    }
  }

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold">Settings</h1>
        <p className="text-gray-500 mt-1">Account and application settings</p>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Profile</h3>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Name</dt>
            <dd>{user?.full_name || '—'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Email</dt>
            <dd>{user?.email || '—'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Role</dt>
            <dd className="capitalize">{user?.role || '—'}</dd>
          </div>
        </dl>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">Change Password</h3>
        {message && (
          <div className={`mb-4 p-3 rounded text-sm ${message.includes('success') ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
            {message}
          </div>
        )}
        <form onSubmit={handlePasswordChange} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Current Password</label>
            <input type="password" value={passwordForm.current} onChange={e => setPasswordForm({ ...passwordForm, current: e.target.value })} className="input w-full" required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">New Password</label>
            <input type="password" value={passwordForm.new_password} onChange={e => setPasswordForm({ ...passwordForm, new_password: e.target.value })} className="input w-full" required minLength={8} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-400 mb-1">Confirm Password</label>
            <input type="password" value={passwordForm.confirm} onChange={e => setPasswordForm({ ...passwordForm, confirm: e.target.value })} className="input w-full" required />
          </div>
          <button type="submit" className="btn-primary">Update Password</button>
        </form>
      </div>

      <div className="card">
        <h3 className="font-semibold mb-4">About</h3>
        <dl className="space-y-3 text-sm">
          <div className="flex justify-between">
            <dt className="text-gray-500">Version</dt>
            <dd>ReconForge v0.3.0</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Platform</dt>
            <dd>FastAPI + React + Celery</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Logged in as</dt>
            <dd>{user?.email || '—'}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-gray-500">Role</dt>
            <dd className="capitalize">{user?.role || '—'}</dd>
          </div>
        </dl>
      </div>
    </div>
  )
}
