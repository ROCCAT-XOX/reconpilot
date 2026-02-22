import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import event_manager

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    event_manager.connect(project_id, websocket)
    logger.info(f"WebSocket connected for project {project_id}")

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "subscribe":
                    scan_id = message.get("scan_id")
                    if scan_id:
                        event_manager.connect(f"scan:{scan_id}", websocket)
                        await websocket.send_text(json.dumps({
                            "event": "subscribed",
                            "scan_id": scan_id,
                        }))

                elif msg_type == "unsubscribe":
                    scan_id = message.get("scan_id")
                    if scan_id:
                        event_manager.disconnect(f"scan:{scan_id}", websocket)

                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "event": "error",
                    "data": {"message": "Invalid JSON"},
                }))

    except WebSocketDisconnect:
        event_manager.disconnect(project_id, websocket)
        logger.info(f"WebSocket disconnected for project {project_id}")
