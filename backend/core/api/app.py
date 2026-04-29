from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable, Dict, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .schemas import (
    ConfigUpdateRequest,
    DeleteWorkflowRequest,
    DeviceCreateRequest,
    DeviceDeleteRequest,
    DeviceUpdateRequest,
    PluginConfigGetRequest,
    PluginConfigUpdateRequest,
    SaveWorkflowRequest,
    SetCurrentWorkflowRequest,
    StartTaskRequest,
    StartWorkflowRequest,
    StopWorkflowRequest,
    StopTaskRequest,
)
from .ws_manager import FastApiWebSocketManager

_logger = logging.getLogger(__name__)


def create_app(handlers: Any, ws_manager: FastApiWebSocketManager) -> FastAPI:
    """Create FastAPI app and wire handlers."""

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

    rpc_handlers: Dict[str, Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = {
        "task.start": handlers.handle_task_start,
        "task.stop": handlers.handle_task_stop,
        "module.list": handlers.handle_module_list,
        "device.create": handlers.handle_device_create,
        "device.update": handlers.handle_device_update,
        "device.delete": handlers.handle_device_delete,
        "plugin.list": handlers.handle_plugin_list,
        "workflow.save": handlers.handle_workflow_save,
        "workflow.load": handlers.handle_workflow_load,
        "workflow.start": handlers.handle_workflow_start,
        "workflow.stop": handlers.handle_workflow_stop,
        "workflow.list": handlers.handle_workflow_list,
        "workflow.get": handlers.handle_workflow_get,
        "workflow.delete": handlers.handle_workflow_delete,
        "workflow.set_current": handlers.handle_workflow_set_current,
        "plugin.config.get": handlers.handle_plugin_config_get,
        "plugin.config.update": handlers.handle_plugin_config_update,
        "config.get": handlers.handle_config_get,
        "config.update": handlers.handle_config_update,
    }

    @app.get("/api/v1/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/v1/modules")
    async def list_modules() -> Dict[str, Any]:
        try:
            return await handlers.handle_module_list({})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/devices")
    async def list_devices() -> Dict[str, Any]:
        """设备列表（推荐使用）。"""
        try:
            result = await handlers.handle_module_list({})
            return {"devices": result.get("modules", [])}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/devices/create")
    async def create_device(req: DeviceCreateRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_device_create(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/devices/update")
    async def update_device(req: DeviceUpdateRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_device_update(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/devices/delete")
    async def delete_device(req: DeviceDeleteRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_device_delete(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/plugins")
    async def list_plugins() -> Dict[str, Any]:
        try:
            return await handlers.handle_plugin_list({})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/plugins/config")
    async def get_plugin_config(device_name: str, plugin_id: str) -> Dict[str, Any]:
        try:
            return await handlers.handle_plugin_config_get(
                {"device_name": device_name, "plugin_id": plugin_id}
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/plugins/config/update")
    async def update_plugin_config(req: PluginConfigUpdateRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_plugin_config_update(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/tasks/start")
    async def start_task(req: StartTaskRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_task_start(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/tasks/stop")
    async def stop_task(req: StopTaskRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_task_stop(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/workflows/save")
    async def save_workflow(req: SaveWorkflowRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_save(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/workflows/load")
    async def load_workflow(module_name: str) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_load({"module_name": module_name})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/workflows/list")
    async def list_workflows(module_name: str) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_list({"module_name": module_name})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/workflows/get")
    async def get_workflow(workflow_id: str, module_name: Optional[str] = None) -> Dict[str, Any]:
        try:
            payload: Dict[str, Any] = {"workflow_id": workflow_id}
            if module_name:
                payload["module_name"] = module_name
            return await handlers.handle_workflow_get(payload)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/workflows/delete")
    async def delete_workflow(req: DeleteWorkflowRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_delete(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/workflows/set-current")
    async def set_current_workflow(req: SetCurrentWorkflowRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_set_current(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/workflows/stop")
    async def stop_workflow(req: StopWorkflowRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_stop(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/workflows/start")
    async def start_workflow(req: StartWorkflowRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_workflow_start(req.model_dump())
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.get("/api/v1/config")
    async def get_config() -> Dict[str, Any]:
        try:
            return await handlers.handle_config_get({})
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/v1/config/update")
    async def update_config(req: ConfigUpdateRequest) -> Dict[str, Any]:
        try:
            return await handlers.handle_config_update(req.model_dump(exclude_none=True))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

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


def _normalize_ws_message(incoming: Any) -> tuple[str, Dict[str, Any]]:
    if isinstance(incoming, dict) and "event" in incoming and "data" in incoming:
        event = str(incoming.get("event"))
        data = incoming.get("data")
        return event, data if isinstance(data, dict) else {}

    if isinstance(incoming, dict) and "type" in incoming:
        return "message", incoming

    return "unknown", {}

