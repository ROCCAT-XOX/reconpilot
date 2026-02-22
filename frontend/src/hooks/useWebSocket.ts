import { useEffect, useRef, useCallback, useState } from 'react'
import { WebSocketClient, WSEvent } from '../api/websocket'

export function useWebSocket(projectId: string | undefined) {
  const clientRef = useRef<WebSocketClient | null>(null)
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!projectId) return

    const client = new WebSocketClient(projectId)
    clientRef.current = client

    client.on('*', (event) => {
      setEvents(prev => [...prev.slice(-100), event])
    })

    client.connect()
    setConnected(true)

    return () => {
      client.disconnect()
      setConnected(false)
    }
  }, [projectId])

  const subscribe = useCallback((scanId: string) => {
    clientRef.current?.subscribe(scanId)
  }, [])

  const onEvent = useCallback((event: string, handler: (e: WSEvent) => void) => {
    return clientRef.current?.on(event, handler)
  }, [])

  const lastEvent = events.length > 0 ? events[events.length - 1] : null

  return { events, lastEvent, connected, subscribe, onEvent }
}
