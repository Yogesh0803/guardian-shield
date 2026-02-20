from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections for different channels."""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {
            "network": [],
            "alerts": [],
            "predictions": [],
        }

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel] = [
                conn for conn in self.active_connections[channel] if conn != websocket
            ]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_json(message)

    async def broadcast(self, message: dict, channel: str):
        if channel not in self.active_connections:
            return
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn, channel)

    def get_connection_count(self, channel: str) -> int:
        return len(self.active_connections.get(channel, []))


manager = ConnectionManager()
