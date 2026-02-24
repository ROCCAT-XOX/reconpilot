import { useNotificationStore, Toast as ToastType } from '../../store/notificationStore'

const iconMap = {
  success: '✓',
  error: '✕',
  warning: '⚠',
  info: 'ℹ',
}

const colorMap = {
  success: 'bg-green-500/20 border-green-500/40 text-green-400',
  error: 'bg-red-500/20 border-red-500/40 text-red-400',
  warning: 'bg-yellow-500/20 border-yellow-500/40 text-yellow-400',
  info: 'bg-blue-500/20 border-blue-500/40 text-blue-400',
}

function ToastItem({ toast }: { toast: ToastType }) {
  const removeToast = useNotificationStore((s) => s.removeToast)

  return (
    <div
      className={`flex items-start gap-3 px-4 py-3 rounded-lg border ${colorMap[toast.type]} shadow-lg backdrop-blur-sm animate-slide-in min-w-[280px] max-w-[90vw] sm:max-w-sm`}
    >
      <span className="text-lg mt-0.5 shrink-0">{iconMap[toast.type]}</span>
      <div className="flex-1 min-w-0">
        {toast.title && <div className="font-semibold text-sm mb-0.5">{toast.title}</div>}
        <span className="text-sm break-words">{toast.message}</span>
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="text-gray-400 hover:text-white text-sm shrink-0 min-w-[28px] min-h-[28px] flex items-center justify-center"
      >
        ✕
      </button>
    </div>
  )
}

export function ToastContainer() {
  const toasts = useNotificationStore((s) => s.toasts)

  if (toasts.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 left-4 sm:left-auto z-50 flex flex-col gap-2 items-end">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}
