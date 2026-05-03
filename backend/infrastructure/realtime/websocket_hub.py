from __future__ import annotations

from backend.infrastructure.realtime.event_bus import EventBus


class WebSocketHub:
    def __init__(self, event_bus: EventBus, ws_manager):
        self.event_bus = event_bus
        self.ws_manager = ws_manager
        self.event_bus.subscribe("run.status_changed", self._broadcast_run_status)
        self.event_bus.subscribe("workflow.node_status", self._broadcast_node_status)
        self.event_bus.subscribe("log", self._broadcast_log)

    async def _broadcast_run_status(self, data: dict) -> None:
        if self.ws_manager is None:
            return
        await self.ws_manager.broadcast("run.status_changed", data)

    async def _broadcast_node_status(self, data: dict) -> None:
        if self.ws_manager is None:
            return
        await self.ws_manager.broadcast("workflow.node_status", data)

    async def _broadcast_log(self, data: dict) -> None:
        if self.ws_manager is None:
            return
        await self.ws_manager.broadcast("log", data)
