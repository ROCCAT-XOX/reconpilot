export interface Scan {
  id: string
  project_id: string
  name: string | null
  profile: 'quick' | 'standard' | 'deep' | 'custom'
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled'
  config: Record<string, any>
  started_at: string | null
  completed_at: string | null
  started_by: string | null
  created_at: string
}

export interface ScanJob {
  id: string
  scan_id: string
  tool_name: string
  phase: string
  status: string
  target: string | null
  duration_seconds: number | null
  error_message: string | null
  started_at: string | null
  completed_at: string | null
}

export interface ScanProfile {
  name: string
  key: string
  description: string
  estimated_duration_minutes: number
  phases: number
  tools: string[]
}
