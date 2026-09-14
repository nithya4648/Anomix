from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
from app.core.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """Manage WebSocket connections and broadcast updates"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.metrics_subscribers: Dict[str, Set[WebSocket]] = {}

    async def broadcast_progress(self, update: dict):
        """Broadcast incident progress updates to all clients.

        The ``update`` dict should contain keys like ``event``, ``incident_id``,
        ``stage`` and ``percent``. It is wrapped in a ``type`` field so clients
        can differentiate progress messages.
        """
        message = {"type": "progress_update", **update}
        await self.broadcast(message)

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.debug(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a disconnected WebSocket"""
        self.active_connections.discard(websocket)

        # Clean up metric subscriptions
        for subscribers in self.metrics_subscribers.values():
            subscribers.discard(websocket)

        logger.debug(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")
                disconnected.add(connection)

        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_metric_update(self, metric_name: str, message: dict):
        """Broadcast to specific metric subscribers"""
        if metric_name not in self.metrics_subscribers:
            return

        disconnected = set()

        for connection in self.metrics_subscribers[metric_name]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending metric update: {e}")
                disconnected.add(connection)

        for connection in disconnected:
            self.disconnect(connection)

    def subscribe_to_metric(self, websocket: WebSocket, metric_name: str):
        """Subscribe connection to specific metric updates"""
        if metric_name not in self.metrics_subscribers:
            self.metrics_subscribers[metric_name] = set()

        self.metrics_subscribers[metric_name].add(websocket)
        logger.debug(f"Subscribed to metric: {metric_name}")

    def unsubscribe_from_metric(self, websocket: WebSocket, metric_name: str):
        """Unsubscribe connection from metric"""
        if metric_name in self.metrics_subscribers:
            self.metrics_subscribers[metric_name].discard(websocket)

    async def handle_client_message(self, websocket: WebSocket, data: dict):
        """Process incoming client messages"""
        message_type = data.get("type")

        if message_type == "subscribe":
            metric_name = data.get("metric_name")
            self.subscribe_to_metric(websocket, metric_name)
            await websocket.send_json({
                "type": "subscribed",
                "metric_name": metric_name,
            })

        elif message_type == "unsubscribe":
            metric_name = data.get("metric_name")
            self.unsubscribe_from_metric(websocket, metric_name)
            await websocket.send_json({
                "type": "unsubscribed",
                "metric_name": metric_name,
            })

        elif message_type == "ping":
            await websocket.send_json({"type": "pong"})
