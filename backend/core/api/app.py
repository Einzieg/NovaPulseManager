from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import actions, apps, devices, plugins, runs, settings, tasks, workflows
from .ws_manager import FastApiWebSocketManager

_logger = logging.getLogger(__name__)


def create_app(handlers: Any, ws_manager: FastApiWebSocketManager) -> FastAPI:
    """Create FastAPI app and register REST routers + WebSocket endpoint."""

    app = FastAPI(
        title="Nova Pulse Manager API",
        version="0.1.0",
        description="FastAPI REST + WebSocket API (FastAPI-only).",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(devices.create_router(handlers))
    app.include_router(apps.create_router(handlers))
    app.include_router(actions.create_router(handlers))
    app.include_router(plugins.create_router(handlers))
    app.include_router(tasks.create_router(handlers))
    app.include_router(workflows.create_router(handlers))
    app.include_router(runs.create_router(handlers))
    app.include_router(settings.create_router(handlers))

    rpc_handlers = _build_rpc_handlers(handlers)

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket) -> None:
        await ws_manager.connect(websocket)
        try:
            while True:
                incoming = await websocket.receive_json()
                event, payload = _normalize_ws_message(incoming)
                if event != "message":
                    continue

                msg_type = payload.get("type")
                request_id = payload.get("request_id")
                msg_payload = payload.get("payload", {}) or {}

                if not msg_type:
                    await websocket.send_json(
                        {"event": "error", "data": {"request_id": request_id, "error": "Missing type"}}
                    )
                    continue

                handler = rpc_handlers.get(msg_type)
                if handler is None:
                    await websocket.send_json(
                        {
                            "event": "error",
                            "data": {"request_id": request_id, "error": f"Unknown type: {msg_type}"},
                        }
                    )
                    continue

                try:
                    result = await handler(msg_payload)
                    await websocket.send_json(
                        {"event": "response", "data": {"request_id": request_id, "success": True, "data": result}}
                    )
                except Exception as e:
                    _logger.error("WS handler error (%s): %s", msg_type, e, exc_info=True)
                    await websocket.send_json(
                        {"event": "error", "data": {"request_id": request_id, "error": str(e)}}
                    )
        except WebSocketDisconnect:
            return
        finally:
            await ws_manager.disconnect(websocket)

    return app


def _build_rpc_handlers(
    handlers: Any,
) -> Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]]:
    return {
        "task.start": handlers.handle_task_start,
        "task.stop": handlers.handle_task_stop,
        "module.list": handlers.handle_module_list,
        "device.create": handlers.handle_device_create,
        "device.update": handlers.handle_device_update,
        "device.delete": handlers.handle_device_delete,
        "plugin.list": handlers.handle_plugin_list,
        "app.list": handlers.handle_app_list,
        "action.list": handlers.handle_action_list,
        "workflow.save": handlers.handle_workflow_save,
        "workflow.load": handlers.handle_workflow_load,
        "workflow.start": handlers.handle_workflow_start,
        "workflow.stop": handlers.handle_workflow_stop,
        "workflow.list": handlers.handle_workflow_list,
        "workflow.get": handlers.handle_workflow_get,
        "workflow.delete": handlers.handle_workflow_delete,
        "workflow.set_current": handlers.handle_workflow_set_current,
        "run.get": handlers.handle_run_get,
        "run.cancel": handlers.handle_run_cancel,
        "run.list": handlers.handle_run_list,
        "plugin.config.get": handlers.handle_plugin_config_get,
        "plugin.config.update": handlers.handle_plugin_config_update,
        "config.get": handlers.handle_config_get,
        "config.update": handlers.handle_config_update,
    }


def _normalize_ws_message(incoming: Any) -> tuple[str, Dict[str, Any]]:
    if isinstance(incoming, dict) and "event" in incoming and "data" in incoming:
        event = str(incoming.get("event"))
        data = incoming.get("data")
        return event, data if isinstance(data, dict) else {}

    if isinstance(incoming, dict) and "type" in incoming:
        return "message", incoming

    return "unknown", {}
