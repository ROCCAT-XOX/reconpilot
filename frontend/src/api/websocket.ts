type WSEventHandler = (event: WSEvent) => void

export interface WSEvent {
  event: string
  scan_id?: string
  timestamp: string
  data: Record<string, any>
}

export class WebSocketClient {
  private ws: WebSocket | null = null
  private handlers: Map<string, Set<WSEventHandler>> = new Map()
  private reconnectTimer: number | null = null
  private projectId: string

  constructor(projectId: string) {
    this.projectId = projectId
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/api/v1/ws/${this.projectId}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('[WS] Connected')
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
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
      console.log('[WS] Disconnected, reconnecting...')
      this.reconnectTimer = window.setTimeout(() => this.connect(), 3000)
    }

    this.ws.onerror = (error) => {
      console.error('[WS] Error:', error)
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
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

  private send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private _dispatch(event: string, data: WSEvent) {
    this.handlers.get(event)?.forEach(handler => handler(data))
  }
}
