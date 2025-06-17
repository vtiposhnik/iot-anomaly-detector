from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from utils.database import get_anomalies, get_traffic
from utils.logger import get_logger

logger = get_logger()
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("WebSocket connected")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info("WebSocket disconnected")

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    last_anomaly_id = None
    try:
        while True:
            await asyncio.sleep(5)
            anomalies = get_anomalies(limit=1)
            if anomalies:
                latest = anomalies[0]
                if last_anomaly_id != latest["anomaly_id"]:
                    await websocket.send_json({"event": "anomaly_alert", "data": latest})
                    last_anomaly_id = latest["anomaly_id"]
            traffic = get_traffic(limit=1)
            if traffic:
                await websocket.send_json({"event": "data_update", "data": traffic[0]})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
