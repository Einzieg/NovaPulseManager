from pathlib import Path

from backend.core.api.app import create_app
from backend.core.api.ws_manager import FastApiWebSocketManager
from backend.core.websocket import MessageHandlers


def test_resource_and_legacy_api_routes_are_registered():
    handlers = MessageHandlers(Path("backend/plugins"), FastApiWebSocketManager())
    app = create_app(handlers, handlers.ws_server)
    routes = {(route.path, next(iter(route.methods), "")) for route in app.routes if hasattr(route, "methods")}
    paths = {path for path, _ in routes}

    assert "/api/v1/apps" in paths
    assert "/api/v1/actions" in paths
    assert "/api/v1/devices" in paths
    assert "/api/v1/devices/{device_id}" in paths
    assert "/api/v1/workflows" in paths
    assert "/api/v1/workflows/{workflow_id}" in paths
    assert "/api/v1/workflows/{workflow_id}/runs" in paths
    assert "/api/v1/runs/{run_id}" in paths

    assert "/api/v1/plugins" in paths
    assert "/api/v1/tasks/start" in paths
    assert "/api/v1/workflows/start" in paths
    assert "/api/v1/workflows/stop" in paths
