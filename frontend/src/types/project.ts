export interface Project {
  id: string
  name: string
  client_name: string
  description: string | null
  status: 'active' | 'completed' | 'archived'
  start_date: string | null
  end_date: string | null
  auto_delete_at: string | null
  created_by: string
  created_at: string
  updated_at: string
  member_count?: number
  scan_count?: number
  finding_count?: number
}

export interface ProjectMember {
  id: string
  project_id: string
  user_id: string
  role: 'lead' | 'pentester' | 'viewer'
  user?: { id: string; email: string; full_name: string }
  joined_at: string
}

export interface ScopeTarget {
  id: string
  project_id: string
  target_type: 'domain' | 'ip' | 'cidr' | 'url' | 'ip_range'
  target_value: string
  is_excluded: boolean
  notes: string | null
  created_at: string
}

export interface CreateProjectPayload {
  name: string
  client_name: string
  description?: string
  start_date?: string
  end_date?: string
}
