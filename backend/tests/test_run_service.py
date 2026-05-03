import asyncio
import json
from pathlib import Path

import pytest

from backend.application.errors import DeviceAlreadyRunning
from backend.application.services import RunService, WorkflowService
from backend.core.api.app import create_app
from backend.core.api.ws_manager import FastApiWebSocketManager
from backend.core.websocket import MessageHandlers
from backend.infrastructure.realtime import EventBus, WebSocketHub
from backend.models import Workflow
from database.db_session import init_database


class FakeScheduler:
    def __init__(self):
        self.is_running = False
        self.current_task = None
        self.last_result = None
        self.started_data = None
        self.start_kwargs = None

    def get_status(self):
        return {"is_running": self.is_running}

    async def start_workflow(self, workflow_data, **kwargs):
        self.is_running = True
        self.started_data = workflow_data
        self.start_kwargs = kwargs
        self.current_task = asyncio.create_task(asyncio.sleep(60))
        return {"status": "started"}

    async def stop_workflow(self):
        self.is_running = False
        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        return {"status": "stopped"}


async def test_run_service_starts_publishes_and_blocks_same_device(temp_db_path):
    init_database(db_path=temp_db_path)
    Workflow.create(
        workflow_id="run-workflow",
        name="Run Workflow",
        module_name="run-device",
        workflow_data=json.dumps({"id": "run-workflow", "nodes": [], "edges": []}),
    )

    scheduler = FakeScheduler()
    event_bus = EventBus()
    events = []
    event_bus.subscribe("run.status_changed", lambda data: events.append(data))
    service = RunService(
        workflow_service=WorkflowService(),
        scheduler_getter=lambda module_name: scheduler,
        scheduler_lookup=lambda module_name: scheduler,
        event_bus=event_bus,
    )

    started = await service.start_workflow(
        {"module_name": "run-device", "workflow_id": "run-workflow"}
    )

    assert started["status"] == "started"
    assert started["run_id"].startswith("run-")
    assert scheduler.start_kwargs == {
        "run_id": started["run_id"],
        "event_bus": event_bus,
    }
    assert events[-1]["status"] == "running"

    with pytest.raises(DeviceAlreadyRunning):
        await service.start_workflow(
            {"module_name": "run-device", "workflow_id": "run-workflow"}
        )

    cancelled = await service.cancel_run(started["run_id"])
    assert cancelled["status"] == "cancelled"


async def test_websocket_hub_broadcasts_run_status():
    class FakeWsManager:
        def __init__(self):
            self.messages = []

        async def broadcast(self, event, data):
            self.messages.append((event, data))

    event_bus = EventBus()
    ws_manager = FakeWsManager()
    WebSocketHub(event_bus, ws_manager)

    await event_bus.publish("run.status_changed", {"run_id": "run-1", "status": "running"})

    assert ws_manager.messages == [
        ("run.status_changed", {"run_id": "run-1", "status": "running"})
    ]


def test_run_api_routes_are_registered():
    handlers = MessageHandlers(Path("backend/plugins"), FastApiWebSocketManager())
    app = create_app(handlers, handlers.ws_server)
    paths = {route.path for route in app.routes}

    assert "/api/v1/workflows/{workflow_id}/runs" in paths
    assert "/api/v1/runs/{run_id}" in paths
    assert "/api/v1/runs/{run_id}/cancel" in paths
    assert "/api/v1/runs" in paths
