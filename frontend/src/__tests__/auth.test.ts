import { describe, it, expect, beforeEach, vi } from 'vitest'

// Mock localStorage
const storage: Record<string, string> = {}
const localStorageMock = {
  getItem: vi.fn((key: string) => storage[key] ?? null),
  setItem: vi.fn((key: string, value: string) => { storage[key] = value }),
  removeItem: vi.fn((key: string) => { delete storage[key] }),
  clear: vi.fn(() => { Object.keys(storage).forEach(k => delete storage[k]) }),
  length: 0,
  key: vi.fn(),
}
Object.defineProperty(globalThis, 'localStorage', { value: localStorageMock })

describe('Token Storage', () => {
  beforeEach(() => {
    localStorageMock.clear()
  })

  it('stores access token', () => {
    localStorage.setItem('access_token', 'test-token-123')
    expect(localStorage.getItem('access_token')).toBe('test-token-123')
  })

  it('stores refresh token', () => {
    localStorage.setItem('refresh_token', 'refresh-abc')
    expect(localStorage.getItem('refresh_token')).toBe('refresh-abc')
  })

  it('removes tokens on clear', () => {
    localStorage.setItem('access_token', 'tok')
    localStorage.setItem('refresh_token', 'ref')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })
})

describe('Auth Store', () => {
  it('imports authStore without error', async () => {
    const { useAuthStore } = await import('../store/authStore')
    expect(useAuthStore).toBeDefined()
    const state = useAuthStore.getState()
    expect(state.logout).toBeDefined()
    expect(state.setToken).toBeDefined()
  })

  it('logout clears token and user', async () => {
    const { useAuthStore } = await import('../store/authStore')
    useAuthStore.getState().setToken('test-token')
    useAuthStore.getState().setUser({ id: '1', email: 'a@b.com', full_name: 'Test', role: 'admin' })
    useAuthStore.getState().logout()
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
  })
})
