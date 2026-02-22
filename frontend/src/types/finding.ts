export interface Finding {
  id: string
  scan_id: string
  project_id: string
  title: string
  description: string | null
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info'
  cvss_score: number | null
  cve_id: string | null
  cwe_id: string | null
  target_host: string | null
  target_port: number | null
  target_protocol: string | null
  target_url: string | null
  target_service: string | null
  source_tool: string
  raw_evidence: Record<string, any> | null
  status: 'open' | 'confirmed' | 'false_positive' | 'accepted_risk' | 'remediated'
  assigned_to: string | null
  verified_by: string | null
  verified_at: string | null
  fingerprint: string | null
  is_duplicate: boolean
  created_at: string
  updated_at: string
}

export interface FindingComment {
  id: string
  finding_id: string
  user_id: string | null
  user_name: string | null
  content: string
  created_at: string
}

export interface FindingStats {
  total: number
  by_severity: Record<string, number>
  by_status: Record<string, number>
  by_tool: Record<string, number>
}
