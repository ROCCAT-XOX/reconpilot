export const SEVERITY_ORDER = ['critical', 'high', 'medium', 'low', 'info'] as const

export const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
  info: '#6b7280',
} as const

export const STATUS_OPTIONS = [
  { value: 'open', label: 'Open' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'false_positive', label: 'False Positive' },
  { value: 'accepted_risk', label: 'Accepted Risk' },
  { value: 'remediated', label: 'Remediated' },
] as const

export const ROLES = [
  { value: 'admin', label: 'Admin' },
  { value: 'lead', label: 'Lead' },
  { value: 'pentester', label: 'Pentester' },
  { value: 'viewer', label: 'Viewer' },
] as const
