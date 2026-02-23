import { useState, useCallback } from 'react'
import { clsx } from 'clsx'
import type { ScopeTarget } from '../../types/project'

// ─── Types ───────────────────────────────────────────────────────────────────

interface WizardState {
  // Step 1
  profile: string
  customTools: string[]
  // Step 2
  useAllScopeTargets: boolean
  additionalTargets: string
  domainTargets: string
  subdomainEnum: boolean
  ipCidrTargets: string
  urlTargets: string
  // Step 3 — Auto-discover toggles
  autoDiscoverSubdomains: boolean
  autoDiscoverTechnologies: boolean
  autoDiscoverPorts: boolean
  knownSubdomains: string
  knownTechnologies: string[]
  knownPorts: string
  contactEmails: string
  testAccounts: string
  intelNotes: string
  // Step 4
  nmapPortRange: string
  nmapSpeed: string
  nmapOsDetection: boolean
  nucleiSeverities: string[]
  nucleiCustomTemplates: string
  ffufWordlist: string
  ffufExtensions: string
  sqlmapRisk: number
  sqlmapTechnique: string
  toolTimeout: number
  parallelExecution: boolean
  // Step 5 (review only)
  scanName: string
}

interface Props {
  scopeTargets: ScopeTarget[]
  onStart: (config: {
    name?: string
    profile: string
    targets: string[]
    config: Record<string, any>
  }) => void
  onClose: () => void
  loading?: boolean
}

const ALL_TOOLS = [
  { name: 'subfinder', label: 'Subfinder', category: 'Recon' },
  { name: 'amass', label: 'Amass', category: 'Recon' },
  { name: 'httpx', label: 'httpx', category: 'Recon' },
  { name: 'nmap', label: 'Nmap', category: 'Scanning' },
  { name: 'nuclei', label: 'Nuclei', category: 'Scanning' },
  { name: 'nikto', label: 'Nikto', category: 'Scanning' },
  { name: 'ffuf', label: 'ffuf', category: 'Scanning' },
  { name: 'gobuster', label: 'Gobuster', category: 'Scanning' },
  { name: 'sslyze', label: 'SSLyze', category: 'Web Analysis' },
  { name: 'testssl', label: 'testssl.sh', category: 'Web Analysis' },
  { name: 'whatweb', label: 'WhatWeb', category: 'Web Analysis' },
  { name: 'sqlmap', label: 'SQLMap', category: 'Exploitation' },
]

const TECHNOLOGIES = [
  'WordPress', 'React', 'Angular', 'Vue.js', 'Laravel', 'Django',
  'Spring', '.NET', 'Ruby on Rails', 'Express.js', 'Flask',
  'Next.js', 'Nuxt.js', 'PHP', 'Java', 'Node.js',
]

const WORDLISTS = [
  { value: 'common.txt', label: 'Common (4.6k words)' },
  { value: '/usr/share/wordlists/dirb/common.txt', label: 'Dirb Common (4.6k)' },
  { value: '/usr/share/wordlists/dirb/big.txt', label: 'Dirb Big (20k)' },
  { value: 'directory-list-2.3-medium.txt', label: 'DirBuster Medium (220k)' },
  { value: 'directory-list-2.3-small.txt', label: 'DirBuster Small (87k)' },
]

const STEPS = [
  { num: 1, label: 'Profile' },
  { num: 2, label: 'Targets' },
  { num: 3, label: 'Intel' },
  { num: 4, label: 'Advanced' },
  { num: 5, label: 'Review' },
]

const INITIAL_STATE: WizardState = {
  profile: 'standard',
  customTools: [],
  useAllScopeTargets: true,
  additionalTargets: '',
  domainTargets: '',
  subdomainEnum: true,
  ipCidrTargets: '',
  urlTargets: '',
  autoDiscoverSubdomains: true,
  autoDiscoverTechnologies: true,
  autoDiscoverPorts: true,
  knownSubdomains: '',
  knownTechnologies: [],
  knownPorts: '',
  contactEmails: '',
  testAccounts: '',
  intelNotes: '',
  nmapPortRange: 'top-1000',
  nmapSpeed: 'T3',
  nmapOsDetection: false,
  nucleiSeverities: ['critical', 'high', 'medium'],
  nucleiCustomTemplates: '',
  ffufWordlist: 'common.txt',
  ffufExtensions: '',
  sqlmapRisk: 1,
  sqlmapTechnique: '',
  toolTimeout: 30,
  parallelExecution: true,
  scanName: '',
}

// ─── Component ───────────────────────────────────────────────────────────────

export default function ScanWizard({ scopeTargets, onStart, onClose, loading }: Props) {
  const [step, setStep] = useState(1)
  const [state, setState] = useState<WizardState>(INITIAL_STATE)

  const update = useCallback(<K extends keyof WizardState>(key: K, value: WizardState[K]) => {
    setState(prev => ({ ...prev, [key]: value }))
  }, [])

  const showAdvanced = state.profile !== 'quick'
  const totalSteps = showAdvanced ? 5 : 4
  const adjustedStep = !showAdvanced && step >= 4 ? step + 1 : step

  const canNext = () => {
    if (step === 1 && state.profile === 'custom' && state.customTools.length === 0) return false
    return true
  }

  const handleNext = () => {
    if (step < totalSteps) {
      let nextStep = step + 1
      if (!showAdvanced && nextStep === 4) nextStep = 5
      setStep(nextStep)
    }
  }

  const handlePrev = () => {
    if (step > 1) {
      let prevStep = step - 1
      if (!showAdvanced && prevStep === 4) prevStep = 3
      setStep(prevStep)
    }
  }

  const getTargets = (): string[] => {
    const targets: string[] = []
    if (state.useAllScopeTargets) {
      scopeTargets
        .filter(s => !s.is_excluded)
        .forEach(s => targets.push(s.target_value))
    }
    const parseLines = (text: string) =>
      text.split('\n').map(t => t.trim()).filter(Boolean)

    targets.push(...parseLines(state.additionalTargets))
    targets.push(...parseLines(state.domainTargets))
    targets.push(...parseLines(state.ipCidrTargets))
    targets.push(...parseLines(state.urlTargets))
    return [...new Set(targets)]
  }

  const buildConfig = (): Record<string, any> => {
    const config: Record<string, any> = {}

    if (state.profile === 'custom') {
      config.tools = state.customTools
    }

    // Auto-discovery settings
    config.auto_discover = {
      subdomains: state.autoDiscoverSubdomains,
      technologies: state.autoDiscoverTechnologies,
      ports: state.autoDiscoverPorts,
    }

    // Intel data
    config.intel = {
      known_subdomains: state.knownSubdomains.split('\n').filter(Boolean),
      known_technologies: state.knownTechnologies,
      known_ports: state.knownPorts,
      contact_emails: state.contactEmails,
      test_accounts: state.testAccounts,
      notes: state.intelNotes,
    }

    // Advanced settings
    if (showAdvanced) {
      config.subdomain_enum = state.subdomainEnum
      config.parallel = state.parallelExecution
      config.tool_timeout_minutes = state.toolTimeout

      config.nmap = {
        port_range: state.nmapPortRange === 'top-1000' ? undefined : state.nmapPortRange || undefined,
        all_ports: state.nmapPortRange === 'all',
        speed: state.nmapSpeed,
        os_detection: state.nmapOsDetection,
      }
      config.nuclei = {
        severities: state.nucleiSeverities,
        custom_templates: state.nucleiCustomTemplates || undefined,
      }
      config.ffuf = {
        wordlist: state.ffufWordlist,
        extensions: state.ffufExtensions ? state.ffufExtensions.split(',').map(e => e.trim()) : undefined,
      }
      config.sqlmap = {
        risk: state.sqlmapRisk,
        technique: state.sqlmapTechnique || undefined,
      }
    }

    return config
  }

  const getEstimatedDuration = (): string => {
    const durations: Record<string, number> = {
      quick: 15,
      standard: 60,
      deep: 180,
      custom: state.customTools.length * 15,
    }
    const mins = durations[state.profile] || 60
    if (mins < 60) return `~${mins} min`
    return `~${Math.round(mins / 60 * 10) / 10}h`
  }

  const handleSubmit = () => {
    const targets = getTargets()
    onStart({
      name: state.scanName || undefined,
      profile: state.profile,
      targets,
      config: buildConfig(),
    })
  }

  // Determine which step number to show in the indicator
  const displaySteps = showAdvanced
    ? STEPS
    : STEPS.filter(s => s.num !== 4)

  const currentDisplayIndex = displaySteps.findIndex(s => s.num === step)

  return (
    <div className="space-y-6">
      {/* Step Indicator */}
      <div className="flex items-center justify-center gap-2">
        {displaySteps.map((s, i) => (
          <div key={s.num} className="flex items-center">
            <div className={clsx(
              'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium border transition-colors',
              step === s.num
                ? 'bg-primary-500 border-primary-500 text-white'
                : step > s.num || (step === 5 && s.num < 5)
                  ? 'bg-primary-500/20 border-primary-500/50 text-primary-400'
                  : 'border-dark-600 text-gray-500'
            )}>
              {i + 1}
            </div>
            <span className={clsx(
              'ml-1 text-xs hidden sm:inline',
              step === s.num ? 'text-primary-400' : 'text-gray-500'
            )}>
              {s.label}
            </span>
            {i < displaySteps.length - 1 && (
              <div className={clsx(
                'w-8 h-px mx-2',
                step > s.num ? 'bg-primary-500/50' : 'bg-dark-600'
              )} />
            )}
          </div>
        ))}
      </div>

      <div className="text-xs text-gray-500 text-center">
        Step {currentDisplayIndex + 1} of {displaySteps.length}
      </div>

      {/* Step Content */}
      <div className="min-h-[320px]">
        {step === 1 && <Step1Profile state={state} update={update} />}
        {step === 2 && <Step2Targets state={state} update={update} scopeTargets={scopeTargets} />}
        {step === 3 && <Step3Intel state={state} update={update} />}
        {step === 4 && <Step4Advanced state={state} update={update} />}
        {step === 5 && <Step5Review state={state} scopeTargets={scopeTargets} getTargets={getTargets} getEstimatedDuration={getEstimatedDuration} update={update} />}
      </div>

      {/* Navigation */}
      <div className="flex justify-between pt-4 border-t border-dark-700">
        <button
          type="button"
          onClick={step === 1 ? onClose : handlePrev}
          className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
        >
          {step === 1 ? 'Cancel' : '← Previous'}
        </button>
        {step === 5 ? (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || getTargets().length === 0}
            className="btn-primary disabled:opacity-50"
          >
            {loading ? 'Starting Scan...' : '🚀 Start Scan'}
          </button>
        ) : (
          <button
            type="button"
            onClick={handleNext}
            disabled={!canNext()}
            className="btn-primary disabled:opacity-50"
          >
            Next →
          </button>
        )}
      </div>
    </div>
  )
}

// ─── Step Components ─────────────────────────────────────────────────────────

interface StepProps {
  state: WizardState
  update: <K extends keyof WizardState>(key: K, value: WizardState[K]) => void
}

function Step1Profile({ state, update }: StepProps) {
  const profiles = [
    { key: 'quick', name: 'Quick Recon', icon: '⚡', duration: '~15 min', description: 'Subdomains + Top ports + Tech stack' },
    { key: 'standard', name: 'Standard', icon: '🔍', duration: '~60 min', description: 'Full OSINT + Port scan + Web vulns' },
    { key: 'deep', name: 'Deep Dive', icon: '🔬', duration: '~180 min', description: 'Everything + SQLi + Auth testing' },
    { key: 'custom', name: 'Custom', icon: '🛠️', duration: 'Varies', description: 'Pick individual tools' },
  ]

  const toggleTool = (toolName: string) => {
    const current = state.customTools
    if (current.includes(toolName)) {
      update('customTools', current.filter(t => t !== toolName))
    } else {
      update('customTools', [...current, toolName])
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-3">Scan Profile</label>
        <div className="grid grid-cols-2 gap-3">
          {profiles.map(p => (
            <button
              key={p.key}
              type="button"
              onClick={() => update('profile', p.key)}
              className={clsx(
                'p-3 rounded-lg border text-left transition-all',
                state.profile === p.key
                  ? 'border-primary-500 bg-primary-500/10'
                  : 'border-dark-700 hover:border-dark-500'
              )}
            >
              <div className="text-xl mb-1">{p.icon}</div>
              <div className="font-semibold text-sm">{p.name}</div>
              <div className="text-xs text-gray-500">{p.duration}</div>
              <div className="text-xs text-gray-400 mt-1">{p.description}</div>
            </button>
          ))}
        </div>
      </div>

      {state.profile === 'custom' && (
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-2">Select Tools</label>
          <div className="space-y-2">
            {['Recon', 'Scanning', 'Web Analysis', 'Exploitation'].map(category => {
              const tools = ALL_TOOLS.filter(t => t.category === category)
              return (
                <div key={category}>
                  <div className="text-xs text-gray-500 mb-1 uppercase tracking-wider">{category}</div>
                  <div className="flex flex-wrap gap-2">
                    {tools.map(tool => (
                      <button
                        key={tool.name}
                        type="button"
                        onClick={() => toggleTool(tool.name)}
                        className={clsx(
                          'px-3 py-1 rounded text-xs font-medium border transition-colors',
                          state.customTools.includes(tool.name)
                            ? 'bg-primary-500/20 border-primary-500/50 text-primary-400'
                            : 'border-dark-600 text-gray-400 hover:border-dark-400'
                        )}
                      >
                        {tool.label}
                      </button>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
          {state.customTools.length === 0 && (
            <p className="text-xs text-red-400 mt-2">Select at least one tool</p>
          )}
        </div>
      )}
    </div>
  )
}

function Step2Targets({ state, update, scopeTargets }: StepProps & { scopeTargets: ScopeTarget[] }) {
  const includedTargets = scopeTargets.filter(s => !s.is_excluded)
  const excludedTargets = scopeTargets.filter(s => s.is_excluded)

  return (
    <div className="space-y-4">
      {/* Scope targets */}
      <div>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={state.useAllScopeTargets}
            onChange={e => update('useAllScopeTargets', e.target.checked)}
          />
          <span className="text-gray-300">
            Use all scope targets ({includedTargets.length} included
            {excludedTargets.length > 0 && `, ${excludedTargets.length} excluded`})
          </span>
        </label>
        {state.useAllScopeTargets && includedTargets.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {includedTargets.map(s => (
              <span key={s.id} className="text-xs bg-green-500/10 text-green-400 px-2 py-0.5 rounded">
                {s.target_value}
              </span>
            ))}
          </div>
        )}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Additional Targets (one per line)</label>
        <textarea
          value={state.additionalTargets}
          onChange={e => update('additionalTargets', e.target.value)}
          className="input w-full h-20 font-mono text-sm"
          placeholder={"extra-target.com\n10.0.0.5"}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Domains</label>
          <textarea
            value={state.domainTargets}
            onChange={e => update('domainTargets', e.target.value)}
            className="input w-full h-20 font-mono text-sm"
            placeholder={"example.com\nsub.example.com"}
          />
          <label className="flex items-center gap-2 mt-1 text-xs">
            <input
              type="checkbox"
              checked={state.subdomainEnum}
              onChange={e => update('subdomainEnum', e.target.checked)}
            />
            <span className="text-gray-500">Enable subdomain enumeration</span>
          </label>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">IP / CIDR Ranges</label>
          <textarea
            value={state.ipCidrTargets}
            onChange={e => update('ipCidrTargets', e.target.value)}
            className="input w-full h-20 font-mono text-sm"
            placeholder={"192.168.1.0/24\n10.0.0.1"}
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">URLs</label>
        <textarea
          value={state.urlTargets}
          onChange={e => update('urlTargets', e.target.value)}
          className="input w-full h-16 font-mono text-sm"
          placeholder="https://app.example.com"
        />
      </div>
    </div>
  )
}

function AutoDiscoverToggle({ label, enabled, onToggle, children }: {
  label: string
  enabled: boolean
  onToggle: (v: boolean) => void
  children: React.ReactNode
}) {
  return (
    <div className={clsx('rounded-lg border p-3 transition-colors', enabled ? 'border-green-500/30 bg-green-500/5' : 'border-dark-700')}>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-400">{label}</label>
        <button
          type="button"
          onClick={() => onToggle(!enabled)}
          className={clsx(
            'flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-colors',
            enabled
              ? 'bg-green-500/20 text-green-400 border border-green-500/30'
              : 'bg-dark-700 text-gray-500 border border-dark-600'
          )}
        >
          {enabled ? '🔍 Auto-Discover' : '✏️ Manual'}
        </button>
      </div>
      {enabled ? (
        <p className="text-xs text-green-400/70 italic">
          Will be automatically discovered during scan. Add known values below to supplement.
        </p>
      ) : null}
      <div className={clsx('mt-2', enabled && 'opacity-60')}>{children}</div>
    </div>
  )
}

function Step3Intel({ state, update }: StepProps) {
  const toggleTech = (tech: string) => {
    const current = state.knownTechnologies
    if (current.includes(tech)) {
      update('knownTechnologies', current.filter(t => t !== tech))
    } else {
      update('knownTechnologies', [...current, tech])
    }
  }

  return (
    <div className="space-y-4">
      <p className="text-xs text-gray-500">
        Fields set to <span className="text-green-400">Auto-Discover</span> will be automatically enumerated during the scan. You can still add known values to supplement discovery.
      </p>

      <AutoDiscoverToggle
        label="Subdomains"
        enabled={state.autoDiscoverSubdomains}
        onToggle={v => update('autoDiscoverSubdomains', v)}
      >
        <textarea
          value={state.knownSubdomains}
          onChange={e => update('knownSubdomains', e.target.value)}
          className="input w-full h-16 font-mono text-sm"
          placeholder={state.autoDiscoverSubdomains ? "Optional: add known subdomains to include..." : "Enter subdomains manually (one per line)"}
        />
      </AutoDiscoverToggle>

      <AutoDiscoverToggle
        label="Technologies"
        enabled={state.autoDiscoverTechnologies}
        onToggle={v => update('autoDiscoverTechnologies', v)}
      >
        <div className="flex flex-wrap gap-2">
          {TECHNOLOGIES.map(tech => (
            <button
              key={tech}
              type="button"
              onClick={() => toggleTech(tech)}
              className={clsx(
                'px-2 py-1 rounded text-xs border transition-colors',
                state.knownTechnologies.includes(tech)
                  ? 'bg-primary-500/20 border-primary-500/50 text-primary-400'
                  : 'border-dark-600 text-gray-400 hover:border-dark-400'
              )}
            >
              {tech}
            </button>
          ))}
        </div>
      </AutoDiscoverToggle>

      <AutoDiscoverToggle
        label="Ports & Services"
        enabled={state.autoDiscoverPorts}
        onToggle={v => update('autoDiscoverPorts', v)}
      >
        <textarea
          value={state.knownPorts}
          onChange={e => update('knownPorts', e.target.value)}
          className="input w-full h-16 font-mono text-sm"
          placeholder={state.autoDiscoverPorts ? "Optional: add known ports to include..." : "Enter ports manually (e.g., 80 - HTTP)"}
        />
      </AutoDiscoverToggle>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Contact Emails / People</label>
          <textarea
            value={state.contactEmails}
            onChange={e => update('contactEmails', e.target.value)}
            className="input w-full h-16 font-mono text-sm"
            placeholder={"admin@example.com\njohn.doe@company.com"}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-400 mb-1">Test Accounts / Credentials</label>
          <textarea
            value={state.testAccounts}
            onChange={e => update('testAccounts', e.target.value)}
            className="input w-full h-16 font-mono text-sm"
            placeholder="testuser:Password123 (staging only)"
          />
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Notes</label>
        <textarea
          value={state.intelNotes}
          onChange={e => update('intelNotes', e.target.value)}
          className="input w-full h-16 text-sm"
          placeholder="Any additional context about the target environment..."
        />
      </div>
    </div>
  )
}

function Step4Advanced({ state, update }: StepProps) {
  return (
    <div className="space-y-5">
      {/* Nmap */}
      <div className="border border-dark-700 rounded-lg p-3 space-y-2">
        <h4 className="text-sm font-semibold text-gray-300">🔎 Nmap</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Port Range</label>
            <select
              value={['top-1000', 'all', 'top-100'].includes(state.nmapPortRange) ? state.nmapPortRange : 'custom'}
              onChange={e => {
                const v = e.target.value
                if (v === 'custom') update('nmapPortRange', '')
                else update('nmapPortRange', v)
              }}
              className="input w-full text-sm"
            >
              <option value="top-1000">Top 1000 (default)</option>
              <option value="top-100">Top 100 (fast)</option>
              <option value="all">All Ports (1-65535)</option>
              <option value="custom">Custom Range...</option>
            </select>
            {!['top-1000', 'all', 'top-100'].includes(state.nmapPortRange) && (
              <input
                type="text"
                value={state.nmapPortRange}
                onChange={e => update('nmapPortRange', e.target.value)}
                className="input w-full text-sm mt-1"
                placeholder="22,80,443,8080 or 1-1024"
              />
            )}
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Scan Speed</label>
            <select
              value={state.nmapSpeed}
              onChange={e => update('nmapSpeed', e.target.value)}
              className="input w-full text-sm"
            >
              {['T1', 'T2', 'T3', 'T4', 'T5'].map(t => (
                <option key={t} value={t}>{t} {t === 'T1' ? '(Sneaky)' : t === 'T3' ? '(Normal)' : t === 'T5' ? '(Insane)' : ''}</option>
              ))}
            </select>
          </div>
        </div>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={state.nmapOsDetection}
            onChange={e => update('nmapOsDetection', e.target.checked)}
          />
          <span className="text-gray-400">Enable OS detection</span>
        </label>
      </div>

      {/* Nuclei */}
      <div className="border border-dark-700 rounded-lg p-3 space-y-2">
        <h4 className="text-sm font-semibold text-gray-300">☢️ Nuclei</h4>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Severity Filter</label>
          <div className="flex gap-2">
            {['critical', 'high', 'medium', 'low', 'info'].map(sev => (
              <label key={sev} className="flex items-center gap-1 text-xs">
                <input
                  type="checkbox"
                  checked={state.nucleiSeverities.includes(sev)}
                  onChange={e => {
                    if (e.target.checked) {
                      update('nucleiSeverities', [...state.nucleiSeverities, sev])
                    } else {
                      update('nucleiSeverities', state.nucleiSeverities.filter(s => s !== sev))
                    }
                  }}
                />
                <span className="text-gray-400 capitalize">{sev}</span>
              </label>
            ))}
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Custom Templates (path)</label>
          <input
            type="text"
            value={state.nucleiCustomTemplates}
            onChange={e => update('nucleiCustomTemplates', e.target.value)}
            className="input w-full text-sm"
            placeholder="/path/to/custom-templates/"
          />
        </div>
      </div>

      {/* Ffuf */}
      <div className="border border-dark-700 rounded-lg p-3 space-y-2">
        <h4 className="text-sm font-semibold text-gray-300">📂 ffuf / Gobuster</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Wordlist</label>
            <select
              value={state.ffufWordlist}
              onChange={e => update('ffufWordlist', e.target.value)}
              className="input w-full text-sm"
            >
              {WORDLISTS.map(w => (
                <option key={w.value} value={w.value}>{w.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Extensions to fuzz</label>
            <input
              type="text"
              value={state.ffufExtensions}
              onChange={e => update('ffufExtensions', e.target.value)}
              className="input w-full text-sm"
              placeholder=".php,.html,.js,.bak"
            />
          </div>
        </div>
      </div>

      {/* SQLMap */}
      <div className="border border-dark-700 rounded-lg p-3 space-y-2">
        <h4 className="text-sm font-semibold text-gray-300">💉 SQLMap</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Risk Level (1-3)</label>
            <input
              type="range"
              min={1} max={3} step={1}
              value={state.sqlmapRisk}
              onChange={e => update('sqlmapRisk', Number(e.target.value))}
              className="w-full"
            />
            <div className="text-xs text-gray-500 text-center">{state.sqlmapRisk}</div>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Technique</label>
            <input
              type="text"
              value={state.sqlmapTechnique}
              onChange={e => update('sqlmapTechnique', e.target.value)}
              className="input w-full text-sm"
              placeholder="BEUSTQ (default: all)"
            />
          </div>
        </div>
      </div>

      {/* Global settings */}
      <div className="border border-dark-700 rounded-lg p-3 space-y-2">
        <h4 className="text-sm font-semibold text-gray-300">⚙️ General</h4>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Timeout per tool (minutes)</label>
            <input
              type="range"
              min={5} max={120} step={5}
              value={state.toolTimeout}
              onChange={e => update('toolTimeout', Number(e.target.value))}
              className="w-full"
            />
            <div className="text-xs text-gray-500 text-center">{state.toolTimeout} min</div>
          </div>
          <div className="flex items-center">
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={state.parallelExecution}
                onChange={e => update('parallelExecution', e.target.checked)}
              />
              <span className="text-gray-400">Parallel execution</span>
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}

function Step5Review({
  state,
  scopeTargets,
  getTargets,
  getEstimatedDuration,
  update,
}: StepProps & {
  scopeTargets: ScopeTarget[]
  getTargets: () => string[]
  getEstimatedDuration: () => string
}) {
  const targets = getTargets()

  const profileLabels: Record<string, string> = {
    quick: '⚡ Quick Recon',
    standard: '🔍 Standard',
    deep: '🔬 Deep Dive',
    custom: '🛠️ Custom',
  }

  return (
    <div className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-1">Scan Name (optional)</label>
        <input
          type="text"
          value={state.scanName}
          onChange={e => update('scanName', e.target.value)}
          className="input w-full"
          placeholder="e.g., Q1 External Scan"
        />
      </div>

      <div className="border border-dark-700 rounded-lg divide-y divide-dark-700">
        <div className="p-3 flex justify-between">
          <span className="text-sm text-gray-500">Profile</span>
          <span className="text-sm font-medium">{profileLabels[state.profile] || state.profile}</span>
        </div>
        {state.profile === 'custom' && (
          <div className="p-3">
            <span className="text-sm text-gray-500">Tools</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {state.customTools.map(t => (
                <span key={t} className="text-xs bg-primary-500/10 text-primary-400 px-2 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </div>
        )}
        <div className="p-3">
          <span className="text-sm text-gray-500">Targets ({targets.length})</span>
          <div className="flex flex-wrap gap-1 mt-1 max-h-20 overflow-y-auto">
            {targets.map(t => (
              <span key={t} className="text-xs bg-dark-800 text-gray-300 px-2 py-0.5 rounded font-mono">{t}</span>
            ))}
            {targets.length === 0 && (
              <span className="text-xs text-red-400">No targets selected</span>
            )}
          </div>
        </div>
        {/* Auto-Discover Summary */}
        {(state.autoDiscoverSubdomains || state.autoDiscoverTechnologies || state.autoDiscoverPorts) && (
          <div className="p-3">
            <span className="text-sm text-gray-500">Auto-Discovery</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {state.autoDiscoverSubdomains && (
                <span className="text-xs bg-green-500/10 text-green-400 px-2 py-0.5 rounded">🔍 Subdomains</span>
              )}
              {state.autoDiscoverTechnologies && (
                <span className="text-xs bg-green-500/10 text-green-400 px-2 py-0.5 rounded">🔍 Technologies</span>
              )}
              {state.autoDiscoverPorts && (
                <span className="text-xs bg-green-500/10 text-green-400 px-2 py-0.5 rounded">🔍 Ports & Services</span>
              )}
            </div>
          </div>
        )}
        {state.knownTechnologies.length > 0 && (
          <div className="p-3">
            <span className="text-sm text-gray-500">Known Technologies</span>
            <div className="flex flex-wrap gap-1 mt-1">
              {state.knownTechnologies.map(t => (
                <span key={t} className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded">{t}</span>
              ))}
            </div>
          </div>
        )}
        <div className="p-3 flex justify-between">
          <span className="text-sm text-gray-500">Estimated Duration</span>
          <span className="text-sm font-medium">{getEstimatedDuration()}</span>
        </div>
        {state.profile !== 'quick' && (
          <div className="p-3 flex justify-between">
            <span className="text-sm text-gray-500">Parallel Execution</span>
            <span className="text-sm">{state.parallelExecution ? '✅ Yes' : '❌ No'}</span>
          </div>
        )}
      </div>
    </div>
  )
}
