from __future__ import annotations

import asyncio
import logging
from typing import Any, Set


class FastApiWebSocketManager:
    """Manages FastAPI WebSocket connections for server push."""

    def __init__(self) -> None:
        self._connections: Set[Any] = set()
        self._lock = asyncio.Lock()
        self._logger = logging.getLogger(__name__)

    async def connect(self, websocket: Any) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)

    async def disconnect(self, websocket: Any) -> None:
        async with self._lock:
            self._connections.discard(websocket)

    async def broadcast(self, event: str, data: Any) -> None:
        message = {"event": event, "data": data}
        async with self._lock:
            connections = list(self._connections)

        stale: list[Any] = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                self._logger.warning("WebSocket send failed: %s", e)
                stale.append(websocket)

        if stale:
            async with self._lock:
                for websocket in stale:
                    self._connections.discard(websocket)

