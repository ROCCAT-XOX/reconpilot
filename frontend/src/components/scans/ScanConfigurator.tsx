import { useState } from 'react'
import ProfileSelector from './ProfileSelector'

interface Props {
  onStart: (config: { name?: string; profile: string; targets: string[] }) => void
  loading?: boolean
}

export default function ScanConfigurator({ onStart, loading }: Props) {
  const [profile, setProfile] = useState('standard')
  const [name, setName] = useState('')
  const [targets, setTargets] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onStart({
      name: name || undefined,
      profile,
      targets: targets.split('\n').map(t => t.trim()).filter(Boolean),
    })
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Scan Profile</label>
        <ProfileSelector selected={profile} onSelect={setProfile} />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Scan Name (optional)</label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          className="input w-full"
          placeholder="e.g., Q1 External Scan"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">
          Targets (one per line, leave empty to use scope)
        </label>
        <textarea
          value={targets}
          onChange={e => setTargets(e.target.value)}
          className="input w-full h-32 font-mono text-sm"
          placeholder={"example.com\n10.0.0.0/24\nhttps://app.example.com"}
        />
      </div>

      <button type="submit" disabled={loading} className="btn-primary w-full disabled:opacity-50">
        {loading ? 'Starting Scan...' : '🚀 Start Scan'}
      </button>
    </form>
  )
}
