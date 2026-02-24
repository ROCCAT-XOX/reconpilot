import { create } from 'zustand'
import type { WSEvent } from '../api/websocket'
import type { ConnectionStatus } from '../api/websocket'

export interface ToolProgress {
  tool: string
  status: 'queued' | 'running' | 'completed' | 'failed' | 'skipped'
  progress?: number
  startedAt?: string
  completedAt?: string
  error?: string
}

interface ScanState {
  activeScanId: string | null
  scanEvents: WSEvent[]
  scanStatus: string | null
  toolProgress: Record<string, ToolProgress>
  logLines: string[]
  connectionStatus: ConnectionStatus
  setActiveScan: (id: string | null) => void
  addEvent: (event: WSEvent) => void
  clearEvents: () => void
  setScanStatus: (status: string) => void
  updateToolProgress: (tool: string, update: Partial<ToolProgress>) => void
  addLogLine: (line: string) => void
  clearLogLines: () => void
  setConnectionStatus: (status: ConnectionStatus) => void
  resetScanState: () => void
}

export const useScanStore = create<ScanState>((set) => ({
  activeScanId: null,
  scanEvents: [],
  scanStatus: null,
  toolProgress: {},
  logLines: [],
  connectionStatus: 'disconnected',
  setActiveScan: (id) => set({ activeScanId: id }),
  addEvent: (event) => set((state) => ({
    scanEvents: [...state.scanEvents.slice(-200), event],
  })),
  clearEvents: () => set({ scanEvents: [] }),
  setScanStatus: (status) => set({ scanStatus: status }),
  updateToolProgress: (tool, update) => set((state) => ({
    toolProgress: {
      ...state.toolProgress,
      [tool]: { ...state.toolProgress[tool], tool, ...update } as ToolProgress,
    },
  })),
  addLogLine: (line) => set((state) => ({
    logLines: [...state.logLines.slice(-500), line],
  })),
  clearLogLines: () => set({ logLines: [] }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
  resetScanState: () => set({
    scanEvents: [],
    scanStatus: null,
    toolProgress: {},
    logLines: [],
  }),
}))
