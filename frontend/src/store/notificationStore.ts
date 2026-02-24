import { create } from 'zustand'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title?: string
  message: string
  duration?: number
}

interface NotificationState {
  toasts: Toast[]
  browserPermission: NotificationPermission | 'default'
  addToast: (type: ToastType, message: string, duration?: number) => void
  addToastWithTitle: (type: ToastType, title: string, message: string, duration?: number) => void
  removeToast: (id: string) => void
  requestBrowserPermission: () => Promise<void>
  sendBrowserNotification: (title: string, body: string) => void
}

let toastId = 0

export const useNotificationStore = create<NotificationState>((set, get) => ({
  toasts: [],
  browserPermission: typeof Notification !== 'undefined' ? Notification.permission : 'default',
  addToast: (type, message, duration = 5000) => {
    const id = String(++toastId)
    set((s) => ({ toasts: [...s.toasts, { id, type, message, duration }] }))
    if (duration > 0) {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
      }, duration)
    }
  },
  addToastWithTitle: (type, title, message, duration = 5000) => {
    const id = String(++toastId)
    set((s) => ({ toasts: [...s.toasts, { id, type, title, message, duration }] }))
    if (duration > 0) {
      setTimeout(() => {
        set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }))
      }, duration)
    }
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
  requestBrowserPermission: async () => {
    if (typeof Notification === 'undefined') return
    const permission = await Notification.requestPermission()
    set({ browserPermission: permission })
  },
  sendBrowserNotification: (title, body) => {
    const { browserPermission } = get()
    if (browserPermission === 'granted' && typeof Notification !== 'undefined') {
      new Notification(title, {
        body,
        icon: '/logo.png',
        badge: '/logo.png',
      })
    }
  },
}))
