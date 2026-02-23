import ScanWizard from './ScanWizard'
import type { ScopeTarget } from '../../types/project'

interface Props {
  scopeTargets?: ScopeTarget[]
  onStart: (config: { name?: string; profile: string; targets: string[]; config?: Record<string, any> }) => void
  onClose: () => void
  loading?: boolean
}

export default function ScanConfigurator({ scopeTargets = [], onStart, onClose, loading }: Props) {
  return (
    <ScanWizard
      scopeTargets={scopeTargets}
      onStart={onStart}
      onClose={onClose}
      loading={loading}
    />
  )
}
