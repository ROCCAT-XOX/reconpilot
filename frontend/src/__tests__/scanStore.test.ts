import { describe, it, expect, beforeEach } from 'vitest'
import { useScanStore } from '../store/scanStore'

describe('scanStore', () => {
  beforeEach(() => {
    useScanStore.setState({
      activeScanId: null,
      scanEvents: [],
      scanStatus: null,
      toolProgress: {},
      logLines: [],
      connectionStatus: 'disconnected',
    })
  })

  it('sets active scan', () => {
    useScanStore.getState().setActiveScan('scan-123')
    expect(useScanStore.getState().activeScanId).toBe('scan-123')
  })

  it('adds events with max limit', () => {
    const store = useScanStore.getState()
    for (let i = 0; i < 210; i++) {
      store.addEvent({ event: `event-${i}`, timestamp: '', data: {} })
    }
    expect(useScanStore.getState().scanEvents.length).toBeLessThanOrEqual(201)
  })

  it('updates tool progress', () => {
    useScanStore.getState().updateToolProgress('nmap', { status: 'running', progress: 50 })
    const tp = useScanStore.getState().toolProgress.nmap
    expect(tp.status).toBe('running')
    expect(tp.progress).toBe(50)
  })

  it('adds log lines with limit', () => {
    const store = useScanStore.getState()
    for (let i = 0; i < 510; i++) {
      store.addLogLine(`line ${i}`)
    }
    expect(useScanStore.getState().logLines.length).toBeLessThanOrEqual(501)
  })

  it('resets scan state', () => {
    const store = useScanStore.getState()
    store.setScanStatus('running')
    store.addLogLine('test')
    store.addEvent({ event: 'test', timestamp: '', data: {} })
    store.resetScanState()
    const state = useScanStore.getState()
    expect(state.scanStatus).toBeNull()
    expect(state.logLines).toHaveLength(0)
    expect(state.scanEvents).toHaveLength(0)
  })
})
