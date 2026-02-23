import { ReactNode } from 'react'
import { clsx } from 'clsx'

interface ModalProps {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl'
}

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-lg',
  lg: 'max-w-2xl',
  xl: 'max-w-4xl',
}

export default function Modal({ open, onClose, title, children, size = 'md' }: ModalProps) {
  if (!open) return null

  const isLarge = size === 'lg' || size === 'xl'

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="fixed inset-0 bg-black/60" onClick={onClose} />
      <div className={clsx(
        'relative bg-dark-900 border border-dark-700 shadow-xl w-full overflow-y-auto',
        // Mobile: full-screen for lg/xl, near-full for sm/md
        isLarge
          ? 'h-full md:h-auto md:max-h-[90vh] md:rounded-xl md:mx-4'
          : 'max-h-[95vh] mx-2 rounded-xl md:mx-4',
        'p-4 md:p-6',
        sizeClasses[size]
      )}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-300 text-xl min-h-[44px] min-w-[44px] flex items-center justify-center"
          >
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  )
}
