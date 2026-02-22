import { clsx } from 'clsx'

const profiles = [
  {
    key: 'quick',
    name: 'Quick Recon',
    icon: '⚡',
    duration: '~15 min',
    description: 'Subdomains + Top ports + Tech stack',
  },
  {
    key: 'standard',
    name: 'Standard',
    icon: '🔍',
    duration: '~60 min',
    description: 'Full OSINT + Port scan + Web vulns',
  },
  {
    key: 'deep',
    name: 'Deep Dive',
    icon: '🔬',
    duration: '~180 min',
    description: 'Everything + SQLi + Auth testing',
  },
]

interface Props {
  selected: string
  onSelect: (key: string) => void
}

export default function ProfileSelector({ selected, onSelect }: Props) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {profiles.map(p => (
        <button
          key={p.key}
          onClick={() => onSelect(p.key)}
          className={clsx(
            'p-4 rounded-lg border text-left transition-all',
            selected === p.key
              ? 'border-primary-500 bg-primary-500/10'
              : 'border-dark-700 hover:border-dark-500'
          )}
        >
          <div className="text-2xl mb-2">{p.icon}</div>
          <div className="font-semibold">{p.name}</div>
          <div className="text-xs text-gray-500 mt-1">{p.duration}</div>
          <div className="text-sm text-gray-400 mt-2">{p.description}</div>
        </button>
      ))}
    </div>
  )
}
