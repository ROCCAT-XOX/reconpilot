import { useState } from 'react'
import Button from '../common/Button'

interface Props {
  projectId: string
  onGenerate: (config: ReportConfig) => void
  loading?: boolean
}

export interface ReportConfig {
  report_type: 'executive' | 'technical' | 'full'
  title: string
  include_sections: string[]
  severity_filter: string[]
}

const sectionOptions = [
  { key: 'executive_summary', label: 'Executive Summary' },
  { key: 'scope', label: 'Scope & Methodology' },
  { key: 'findings_overview', label: 'Findings Overview' },
  { key: 'findings_detail', label: 'Detailed Findings' },
  { key: 'remediation', label: 'Remediation Roadmap' },
  { key: 'appendix', label: 'Technical Appendix' },
]

const severities = ['critical', 'high', 'medium', 'low', 'info']

export default function ReportBuilder({ projectId, onGenerate, loading }: Props) {
  const [config, setConfig] = useState<ReportConfig>({
    report_type: 'full',
    title: '',
    include_sections: sectionOptions.map((s) => s.key),
    severity_filter: ['critical', 'high', 'medium', 'low'],
  })

  const toggleSection = (key: string) => {
    setConfig((prev) => ({
      ...prev,
      include_sections: prev.include_sections.includes(key)
        ? prev.include_sections.filter((s) => s !== key)
        : [...prev.include_sections, key],
    }))
  }

  const toggleSeverity = (sev: string) => {
    setConfig((prev) => ({
      ...prev,
      severity_filter: prev.severity_filter.includes(sev)
        ? prev.severity_filter.filter((s) => s !== sev)
        : [...prev.severity_filter, sev],
    }))
  }

  return (
    <div className="bg-dark-900 rounded-xl border border-dark-700 p-6 space-y-6">
      <h3 className="text-lg font-bold text-gray-100">Report Builder</h3>

      {/* Report Type */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Report Type</label>
        <div className="flex gap-3">
          {(['executive', 'technical', 'full'] as const).map((t) => (
            <button
              key={t}
              onClick={() => setConfig((p) => ({ ...p, report_type: t }))}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                config.report_type === t
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-800 text-gray-400 hover:bg-dark-700'
              }`}
            >
              {t.charAt(0).toUpperCase() + t.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Title */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Report Title</label>
        <input
          type="text"
          value={config.title}
          onChange={(e) => setConfig((p) => ({ ...p, title: e.target.value }))}
          placeholder="Penetration Test Report — Q1 2026"
          className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50"
        />
      </div>

      {/* Sections */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Include Sections</label>
        <div className="grid grid-cols-2 gap-2">
          {sectionOptions.map((s) => (
            <label key={s.key} className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer">
              <input
                type="checkbox"
                checked={config.include_sections.includes(s.key)}
                onChange={() => toggleSection(s.key)}
                className="rounded border-dark-600 bg-dark-800 text-primary-600 focus:ring-primary-500/50"
              />
              {s.label}
            </label>
          ))}
        </div>
      </div>

      {/* Severity Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-400 mb-2">Minimum Severity</label>
        <div className="flex gap-2">
          {severities.map((sev) => (
            <button
              key={sev}
              onClick={() => toggleSeverity(sev)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors ${
                config.severity_filter.includes(sev)
                  ? 'bg-primary-600/20 text-primary-400 ring-1 ring-primary-500/30'
                  : 'bg-dark-800 text-gray-500 hover:text-gray-400'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Generate */}
      <div className="pt-2">
        <Button onClick={() => onGenerate(config)} loading={loading} size="lg" className="w-full">
          Generate Report
        </Button>
      </div>
    </div>
  )
}
