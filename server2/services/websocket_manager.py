import asyncio
import json
from typing import List
from fastapi import WebSocket

class WebSocketManager:
    """Manages active WebSocket connections and allows broadcasting."""
    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []
        self.loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self.loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def _broadcast(self, message: dict) -> None:
        data = json.dumps(message)
        for connection in list(self.active_connections):
            try:
                await connection.send_text(data)
            except Exception:
                # Remove broken connections
                self.disconnect(connection)

    def broadcast(self, message: dict) -> None:
        """Broadcast a message to all clients in a thread-safe manner."""
        if self.loop is None:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast(message), self.loop)

# Singleton instance
manager = WebSocketManager()
