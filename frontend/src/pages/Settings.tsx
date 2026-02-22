import { useState } from 'react'
import { useAuthStore } from '../store/authStore'
import Button from '../components/common/Button'
import apiClient from '../api/client'

export default function Settings() {
  const user = useAuthStore((s) => s.user)
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'notifications' | 'api'>('profile')
  const [profile, setProfile] = useState({ full_name: user?.full_name || '', email: user?.email || '' })
  const [passwords, setPasswords] = useState({ current: '', new: '', confirm: '' })
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState('')

  const handleProfileSave = async () => {
    setSaving(true)
    try {
      await apiClient.patch('/users/me', profile)
      setMessage('Profile updated successfully.')
    } catch {
      setMessage('Failed to update profile.')
    }
    setSaving(false)
    setTimeout(() => setMessage(''), 3000)
  }

  const handlePasswordChange = async () => {
    if (passwords.new !== passwords.confirm) {
      setMessage('Passwords do not match.')
      return
    }
    setSaving(true)
    try {
      await apiClient.post('/auth/change-password', {
        current_password: passwords.current,
        new_password: passwords.new,
      })
      setMessage('Password changed successfully.')
      setPasswords({ current: '', new: '', confirm: '' })
    } catch {
      setMessage('Failed to change password.')
    }
    setSaving(false)
    setTimeout(() => setMessage(''), 3000)
  }

  const tabs = [
    { key: 'profile', label: 'Profile', icon: '👤' },
    { key: 'security', label: 'Security', icon: '🔒' },
    { key: 'notifications', label: 'Notifications', icon: '🔔' },
    { key: 'api', label: 'API Keys', icon: '🔑' },
  ] as const

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Settings</h1>
        <p className="text-sm text-gray-500 mt-1">Manage your account and preferences</p>
      </div>

      {/* Message Toast */}
      {message && (
        <div className="bg-primary-600/20 border border-primary-500/30 text-primary-300 text-sm px-4 py-2 rounded-lg">
          {message}
        </div>
      )}

      <div className="flex gap-6">
        {/* Sidebar */}
        <div className="w-48 space-y-1">
          {tabs.map((t) => (
            <button
              key={t.key}
              onClick={() => setActiveTab(t.key)}
              className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
                activeTab === t.key
                  ? 'bg-primary-600/20 text-primary-400'
                  : 'text-gray-400 hover:bg-dark-800 hover:text-gray-200'
              }`}
            >
              <span>{t.icon}</span>
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 max-w-2xl">
          {activeTab === 'profile' && (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-200">Profile Information</h3>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
                <input
                  value={profile.full_name}
                  onChange={(e) => setProfile((p) => ({ ...p, full_name: e.target.value }))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Email</label>
                <input
                  type="email"
                  value={profile.email}
                  onChange={(e) => setProfile((p) => ({ ...p, email: e.target.value }))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
                <input
                  value={user?.role || ''}
                  disabled
                  className="w-full bg-dark-950 border border-dark-700 rounded-lg px-3 py-2 text-sm text-gray-500 capitalize cursor-not-allowed"
                />
              </div>
              <Button onClick={handleProfileSave} loading={saving}>Save Changes</Button>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-200">Change Password</h3>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Current Password</label>
                <input
                  type="password"
                  value={passwords.current}
                  onChange={(e) => setPasswords((p) => ({ ...p, current: e.target.value }))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">New Password</label>
                <input
                  type="password"
                  value={passwords.new}
                  onChange={(e) => setPasswords((p) => ({ ...p, new: e.target.value }))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Confirm Password</label>
                <input
                  type="password"
                  value={passwords.confirm}
                  onChange={(e) => setPasswords((p) => ({ ...p, confirm: e.target.value }))}
                  className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
                />
              </div>
              <Button onClick={handlePasswordChange} loading={saving}>Update Password</Button>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-200">Notification Preferences</h3>
              {[
                { label: 'Scan completed', desc: 'Get notified when a scan finishes', key: 'scan_complete' },
                { label: 'Critical findings', desc: 'Immediate alerts for critical vulnerabilities', key: 'critical_finding' },
                { label: 'Report ready', desc: 'Notification when report generation completes', key: 'report_ready' },
                { label: 'Team activity', desc: 'Updates about team member actions', key: 'team_activity' },
              ].map((item) => (
                <div key={item.key} className="flex items-center justify-between py-3 border-b border-dark-700 last:border-0">
                  <div>
                    <p className="text-sm font-medium text-gray-200">{item.label}</p>
                    <p className="text-xs text-gray-500">{item.desc}</p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input type="checkbox" defaultChecked className="sr-only peer" />
                    <div className="w-9 h-5 bg-dark-700 rounded-full peer peer-checked:bg-primary-600 after:content-[''] after:absolute after:top-0.5 after:left-0.5 after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:after:translate-x-4" />
                  </label>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'api' && (
            <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-4">
              <h3 className="text-lg font-semibold text-gray-200">API Keys</h3>
              <p className="text-sm text-gray-500">
                API keys allow programmatic access to ReconForge. Keep them secret.
              </p>
              <div className="bg-dark-950 border border-dark-700 rounded-lg p-4">
                <p className="text-xs text-gray-500 mb-2">Your API Token (JWT)</p>
                <code className="text-xs text-green-400 font-mono break-all">
                  {localStorage.getItem('token')?.slice(0, 40) || 'No token'}...
                </code>
              </div>
              <Button variant="secondary" size="sm">Regenerate Token</Button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
