type WSEventHandler = (event: WSEvent) => void

export type ConnectionStatus = 'connected' | 'disconnected' | 'reconnecting'

export interface WSEvent {
  event: string
  scan_id?: string
  timestamp: string
  data: Record<string, any>
}

const MAX_RECONNECT_DELAY = 30000
const BASE_DELAY = 1000

export class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Map<string, Set<WSEventHandler>> = new Map()
  private statusHandlers: Set<(status: ConnectionStatus) => void> = new Set()
  private reconnectTimer: number | null = null
  private reconnectAttempts: number = 0
  private projectId: string
  private intentionalClose: boolean = false

  constructor(projectId: string) {
    this.projectId = projectId
  }

  connect() {
    this.intentionalClose = false
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const token = localStorage.getItem('access_token')
    const url = `${protocol}//${window.location.host}/api/v1/ws/${this.projectId}${token ? `?token=${token}` : ''}`

    this._setStatus('reconnecting')
    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('[WS] Connected')
      this.reconnectAttempts = 0
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
      this._setStatus('connected')
    }

    this.ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data)
        this._dispatch(data.event, data)
        this._dispatch('*', data)
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    this.ws.onclose = () => {
      if (this.intentionalClose) {
        this._setStatus('disconnected')
        return
      }
      console.log('[WS] Disconnected, scheduling reconnect...')
      this._setStatus('disconnected')
      this._scheduleReconnect()
    }

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  disconnect() {
    this.intentionalClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this._setStatus('disconnected')
  }

  subscribe(scanId: string) {
    this.send({ type: 'subscribe', scan_id: scanId })
  }

  unsubscribe(scanId: string) {
    this.send({ type: 'unsubscribe', scan_id: scanId })
  }

  on(event: string, handler: WSEventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)
    return () => this.handlers.get(event)?.delete(handler)
  }

  onStatusChange(handler: (status: ConnectionStatus) => void) {
    this.statusHandlers.add(handler)
    return () => this.statusHandlers.delete(handler)
  }

  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private _dispatch(event: string, data: WSEvent) {
    this.handlers.get(event)?.forEach(handler => handler(data))
  }

  private _setStatus(status: ConnectionStatus) {
    this.statusHandlers.forEach(handler => handler(status))
  }

  private _scheduleReconnect() {
    const delay = Math.min(BASE_DELAY * Math.pow(2, this.reconnectAttempts), MAX_RECONNECT_DELAY)
    const jitter = delay * 0.2 * Math.random()
    console.log(`[WS] Reconnecting in ${Math.round(delay + jitter)}ms (attempt ${this.reconnectAttempts + 1})`)
    this._setStatus('reconnecting')
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay + jitter)
  }
}
