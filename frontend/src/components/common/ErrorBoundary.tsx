import { Component, ErrorInfo, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

const isDev = import.meta.env.DEV

export default class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo)
    this.setState({ errorInfo })
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback

      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4 px-4">
          <div className="text-red-400 text-6xl">⚠</div>
          <h2 className="text-xl font-semibold text-white text-center">Something went wrong</h2>
          <p className="text-gray-400 text-sm max-w-md text-center">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          {isDev && this.state.error && (
            <details className="w-full max-w-2xl text-xs">
              <summary className="text-gray-500 cursor-pointer hover:text-gray-300 mb-2">
                Error Details (dev mode)
              </summary>
              <pre className="bg-dark-950 border border-dark-700 rounded-lg p-3 overflow-x-auto text-red-400 whitespace-pre-wrap break-words">
                {this.state.error.stack}
              </pre>
              {this.state.errorInfo?.componentStack && (
                <pre className="bg-dark-950 border border-dark-700 rounded-lg p-3 mt-2 overflow-x-auto text-gray-500 whitespace-pre-wrap break-words">
                  {this.state.errorInfo.componentStack}
                </pre>
              )}
            </details>
          )}
          <div className="flex gap-3">
            <button
              onClick={this.handleRetry}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors min-h-[44px]"
            >
              Try Again
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-dark-700 hover:bg-dark-600 text-gray-200 rounded-lg transition-colors border border-dark-600 min-h-[44px]"
            >
              Reload Page
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
