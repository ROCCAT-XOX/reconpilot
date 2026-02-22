import { formatDateTime } from '../../utils/formatters'
import Button from '../common/Button'

interface Report {
  id: string
  project_id: string
  title: string
  report_type: string
  status: 'generating' | 'completed' | 'failed'
  file_path?: string
  created_at: string
}

interface Props {
  report: Report
  onDownload: (id: string) => void
  onDelete: (id: string) => void
}

export default function ReportPreview({ report, onDownload, onDelete }: Props) {
  const statusStyles = {
    generating: 'text-yellow-400 bg-yellow-400/10',
    completed: 'text-green-400 bg-green-400/10',
    failed: 'text-red-400 bg-red-400/10',
  }

  return (
    <div className="bg-dark-900 rounded-xl border border-dark-700 p-5 flex items-center justify-between">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3">
          <span className="text-2xl">📄</span>
          <div>
            <h4 className="text-sm font-semibold text-gray-100 truncate">{report.title || 'Untitled Report'}</h4>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-gray-500 capitalize">{report.report_type}</span>
              <span className="text-xs text-gray-600">•</span>
              <span className="text-xs text-gray-500">{formatDateTime(report.created_at)}</span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full capitalize ${statusStyles[report.status]}`}
              >
                {report.status}
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 ml-4">
        {report.status === 'completed' && (
          <Button variant="primary" size="sm" onClick={() => onDownload(report.id)}>
            Download PDF
          </Button>
        )}
        {report.status === 'generating' && (
          <div className="flex items-center gap-2 text-yellow-400 text-xs">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generating...
          </div>
        )}
        <Button variant="ghost" size="sm" onClick={() => onDelete(report.id)}>
          🗑️
        </Button>
      </div>
    </div>
  )
}
