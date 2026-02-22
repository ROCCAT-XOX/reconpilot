import { useEffect, useRef, useCallback, useState } from 'react'
import { WebSocketClient, WSEvent, ConnectionStatus } from '../api/websocket'

export function useWebSocket(projectId: string | undefined) {
  const clientRef = useRef<WebSocketClient | null>(null)
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')

  useEffect(() => {
    if (!projectId) return

    const client = new WebSocketClient(projectId)
    clientRef.current = client

    client.on('*', (event) => {
      setEvents(prev => [...prev.slice(-100), event])
    })

    client.onStatusChange(setConnectionStatus)

    client.connect()

    return () => {
      client.disconnect()
    }
  }, [projectId])

  const subscribe = useCallback((scanId: string) => {
    clientRef.current?.subscribe(scanId)
  }, [])

  const onEvent = useCallback((event: string, handler: (e: WSEvent) => void) => {
    return clientRef.current?.on(event, handler)
  }, [])

  return {
    events,
    connected: connectionStatus === 'connected',
    connectionStatus,
    subscribe,
    onEvent,
  }
}
