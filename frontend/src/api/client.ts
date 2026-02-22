import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useNotificationStore } from '../store/notificationStore'

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
})

// --- Request interceptor ---
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// --- Token refresh logic ---
let isRefreshing = false
let failedQueue: Array<{
  resolve: (token: string) => void
  reject: (error: unknown) => void
}> = []

function processQueue(error: unknown, token: string | null) {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token)
    } else {
      prom.reject(error)
    }
  })
  failedQueue = []
}

function forceLogout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  window.location.href = '/login'
}

// --- Response interceptor ---
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 — attempt token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refresh_token')

      if (!refreshToken) {
        forceLogout()
        return Promise.reject(error)
      }

      if (isRefreshing) {
        // Queue this request until refresh completes
        return new Promise<string>((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const { data } = await axios.post('/api/v1/auth/refresh', {
          refresh_token: refreshToken,
        })
        const newAccessToken = data.access_token
        const newRefreshToken = data.refresh_token

        localStorage.setItem('access_token', newAccessToken)
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken)
        }

        processQueue(null, newAccessToken)
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        forceLogout()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    // --- Global error notifications ---
    const addToast = useNotificationStore.getState().addToast

    if (!error.response) {
      // Network error or timeout
      if (error.code === 'ECONNABORTED') {
        addToast('error', 'Request timed out. Please try again.')
      } else {
        addToast('error', 'Network error. Please check your connection.')
      }
    } else if (error.response.status >= 500) {
      addToast('error', `Server error (${error.response.status}). Please try again later.`)
    } else if (error.response.status === 403) {
      addToast('warning', 'You do not have permission to perform this action.')
    }
    // 400/404 etc. are handled by the caller

    return Promise.reject(error)
  }
)

export default apiClient
