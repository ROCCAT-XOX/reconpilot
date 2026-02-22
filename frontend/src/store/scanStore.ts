import { create } from 'zustand'
import type { WSEvent } from '../api/websocket'

interface ScanState {
  activeScanId: string | null
  scanEvents: WSEvent[]
  setActiveScan: (id: string | null) => void
  addEvent: (event: WSEvent) => void
  clearEvents: () => void
}

export const useScanStore = create<ScanState>((set) => ({
  activeScanId: null,
  scanEvents: [],
  setActiveScan: (id) => set({ activeScanId: id }),
  addEvent: (event) => set((state) => ({
    scanEvents: [...state.scanEvents.slice(-200), event],
  })),
  clearEvents: () => set({ scanEvents: [] }),
}))
