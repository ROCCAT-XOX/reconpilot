from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import event_manager

router = APIRouter()


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: str):
    await websocket.accept()
    event_manager.connect(project_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle subscribe/unsubscribe messages
    except WebSocketDisconnect:
        event_manager.disconnect(project_id, websocket)
