import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import apiClient from '../api/client'

export function useAuth() {
  const { token, user, setUser, logout } = useAuthStore()
  const navigate = useNavigate()

  useEffect(() => {
    if (token && !user) {
      apiClient.get('/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          logout()
          navigate('/login')
        })
    }
  }, [token])

  return {
    isAuthenticated: !!token,
    user,
    logout: () => {
      logout()
      navigate('/login')
    },
  }
}
