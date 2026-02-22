interface Props {
  severity: string
  status: string
  tool: string
  onSeverityChange: (v: string) => void
  onStatusChange: (v: string) => void
  onToolChange: (v: string) => void
  tools?: string[]
}

export default function FindingFilters({ severity, status, tool, onSeverityChange, onStatusChange, onToolChange, tools = [] }: Props) {
  return (
    <div className="flex flex-wrap gap-3">
      <select value={severity} onChange={e => onSeverityChange(e.target.value)} className="input text-sm">
        <option value="">All Severities</option>
        <option value="critical">Critical</option>
        <option value="high">High</option>
        <option value="medium">Medium</option>
        <option value="low">Low</option>
        <option value="info">Info</option>
      </select>

      <select value={status} onChange={e => onStatusChange(e.target.value)} className="input text-sm">
        <option value="">All Statuses</option>
        <option value="open">Open</option>
        <option value="confirmed">Confirmed</option>
        <option value="false_positive">False Positive</option>
        <option value="accepted_risk">Accepted Risk</option>
        <option value="remediated">Remediated</option>
      </select>

      <select value={tool} onChange={e => onToolChange(e.target.value)} className="input text-sm">
        <option value="">All Tools</option>
        {tools.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>
    </div>
  )
}
