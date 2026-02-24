import { useEffect, useRef, useCallback, useState } from 'react'
import { WebSocketClient, WSEvent, ConnectionStatus } from '../api/websocket'
import { useScanStore } from '../store/scanStore'
import { useNotificationStore } from '../store/notificationStore'

export function useWebSocket(projectId: string | undefined) {
  const clientRef = useRef<WebSocketClient | null>(null)
  const [events, setEvents] = useState<WSEvent[]>([])
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected')

  const addEvent = useScanStore((s) => s.addEvent)
  const setScanStatus = useScanStore((s) => s.setScanStatus)
  const updateToolProgress = useScanStore((s) => s.updateToolProgress)
  const addLogLine = useScanStore((s) => s.addLogLine)
  const setStoreConnectionStatus = useScanStore((s) => s.setConnectionStatus)
  const addToast = useNotificationStore((s) => s.addToast)
  const addToastWithTitle = useNotificationStore((s) => s.addToastWithTitle)
  const sendBrowserNotification = useNotificationStore((s) => s.sendBrowserNotification)

  useEffect(() => {
    if (!projectId) return

    const client = new WebSocketClient(projectId)
    clientRef.current = client

    client.on('*', (event) => {
      setEvents(prev => [...prev.slice(-100), event])
      addEvent(event)
    })

    // Handle scan status changes
    client.on('scan_status', (event) => {
      const { status, scan_id } = event.data || {}
      if (status) {
        setScanStatus(status)
        if (status === 'running') {
          addToast('info', 'Scan started')
        } else if (status === 'completed') {
          const findings = event.data.total_findings ?? 0
          const critical = event.data.critical_findings ?? 0
          const msg = `Scan completed — ${findings} findings${critical > 0 ? `, ${critical} critical` : ''}`
          addToastWithTitle('success', 'Scan Complete', msg)
          sendBrowserNotification('Scan Complete', msg)
        } else if (status === 'failed') {
          const error = event.data.error || 'Unknown error'
          addToastWithTitle('error', 'Scan Failed', error, 8000)
          sendBrowserNotification('Scan Failed', error)
        }
      }
    })

    // Handle tool progress
    client.on('tool_started', (event) => {
      const { tool } = event.data || {}
      if (tool) {
        updateToolProgress(tool, { status: 'running', startedAt: event.timestamp })
      }
    })

    client.on('tool_progress', (event) => {
      const { tool, progress } = event.data || {}
      if (tool) {
        updateToolProgress(tool, { progress })
      }
    })

    client.on('tool_completed', (event) => {
      const { tool } = event.data || {}
      if (tool) {
        updateToolProgress(tool, { status: 'completed', completedAt: event.timestamp })
      }
    })

    client.on('tool_failed', (event) => {
      const { tool, error } = event.data || {}
      if (tool) {
        updateToolProgress(tool, { status: 'failed', error, completedAt: event.timestamp })
        addToast('warning', `Tool ${tool} failed: ${error || 'unknown error'}`)
      }
    })

    // Handle log lines
    client.on('log', (event) => {
      const { line } = event.data || {}
      if (line) {
        addLogLine(line)
      }
    })

    client.onStatusChange((status) => {
      setConnectionStatus(status)
      setStoreConnectionStatus(status)
    })

    client.connect()

    return () => {
      client.disconnect()
    }
  }, [projectId, addEvent, setScanStatus, updateToolProgress, addLogLine, setStoreConnectionStatus, addToast, addToastWithTitle, sendBrowserNotification])

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
