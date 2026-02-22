import json
import logging
from datetime import UTC, datetime
from uuid import UUID

logger = logging.getLogger(__name__)


class WebSocketEventManager:
    """Manages WebSocket connections and event broadcasting."""

    def __init__(self):
        self._connections: dict[str, set] = {}  # project_id -> set of websockets

    def connect(self, project_id: str, websocket):
        if project_id not in self._connections:
            self._connections[project_id] = set()
        self._connections[project_id].add(websocket)

    def disconnect(self, project_id: str, websocket):
        if project_id in self._connections:
            self._connections[project_id].discard(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]

    async def emit(self, scan_id: UUID | str, event: str, data: dict):
        message = json.dumps({
            "event": event,
            "scan_id": str(scan_id),
            "timestamp": datetime.now(UTC).isoformat(),
            "data": data,
        })
        # Broadcast to all connected clients for now
        for project_id, connections in self._connections.items():
            for ws in connections.copy():
                try:
                    await ws.send_text(message)
                except Exception:
                    connections.discard(ws)

    @property
    def active_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


event_manager = WebSocketEventManager()
