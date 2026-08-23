from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import WebSocketManager
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/ws", tags=["websocket"])
ws_manager = WebSocketManager()


@router.websocket("/api/v1/updates")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time metric and anomaly updates.
    
    Client can:
    - Subscribe to specific metrics: {"type": "subscribe", "metric_name": "cpu_usage"}
    - Unsubscribe: {"type": "unsubscribe", "metric_name": "cpu_usage"}
    - Send heartbeat: {"type": "ping"}
    
    Server broadcasts:
    - Metric ingestion: {"event": "metric_ingested", "metric": {...}}
    - Anomalies: {"event": "anomaly_detected", "anomaly": {...}, "alert": {...}}
    - Incidents: {"event": "incident_created", "incident": {...}}
    """

    await ws_manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_client_message(websocket, data)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.debug("Client disconnected from WebSocket")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)
