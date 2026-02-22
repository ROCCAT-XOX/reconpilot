export interface User {
  id: string
  email: string
  full_name: string
  role: 'admin' | 'lead' | 'pentester' | 'viewer'
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}
