import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useNotificationStore } from '../store/notificationStore'

describe('notificationStore', () => {
  beforeEach(() => {
    useNotificationStore.setState({ toasts: [] })
  })

  it('adds a toast', () => {
    useNotificationStore.getState().addToast('success', 'Test message')
    const toasts = useNotificationStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].type).toBe('success')
    expect(toasts[0].message).toBe('Test message')
  })

  it('adds a toast with title', () => {
    useNotificationStore.getState().addToastWithTitle('error', 'Error Title', 'Error body')
    const toasts = useNotificationStore.getState().toasts
    expect(toasts).toHaveLength(1)
    expect(toasts[0].title).toBe('Error Title')
    expect(toasts[0].message).toBe('Error body')
    expect(toasts[0].type).toBe('error')
  })

  it('removes a toast', () => {
    useNotificationStore.getState().addToast('info', 'To remove', 0)
    const id = useNotificationStore.getState().toasts[0].id
    useNotificationStore.getState().removeToast(id)
    expect(useNotificationStore.getState().toasts).toHaveLength(0)
  })

  it('auto-dismisses after duration', async () => {
    vi.useFakeTimers()
    useNotificationStore.getState().addToast('warning', 'Auto dismiss', 1000)
    expect(useNotificationStore.getState().toasts).toHaveLength(1)
    vi.advanceTimersByTime(1100)
    expect(useNotificationStore.getState().toasts).toHaveLength(0)
    vi.useRealTimers()
  })
})
