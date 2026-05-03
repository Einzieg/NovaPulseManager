from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.core.api.schemas import DeviceCreateRequest, DeviceDeleteRequest, DeviceUpdateRequest
from backend.api.routes.utils import call_handler


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["devices"])

    @router.get("/health")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    @router.get("/modules", deprecated=True)
    async def list_modules() -> Dict[str, Any]:
        return await call_handler(handlers.handle_module_list({}))

    @router.get("/devices")
    async def list_devices() -> Dict[str, Any]:
        result = await call_handler(handlers.handle_module_list({}))
        return {"devices": result.get("modules", [])}

    @router.post("/devices")
    async def create_device_resource(req: DeviceCreateRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_device_create(req.model_dump()))

    @router.post("/devices/create", deprecated=True)
    async def create_device(req: DeviceCreateRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_device_create(req.model_dump()))

    @router.patch("/devices/{device_id}")
    async def update_device_resource(
        device_id: int,
        req: DeviceUpdateRequest,
    ) -> Dict[str, Any]:
        payload = req.model_dump()
        payload["device_id"] = device_id
        return await call_handler(handlers.handle_device_update(payload))

    @router.post("/devices/update", deprecated=True)
    async def update_device(req: DeviceUpdateRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_device_update(req.model_dump()))

    @router.delete("/devices/{device_id}")
    async def delete_device_resource(device_id: int) -> Dict[str, Any]:
        return await call_handler(handlers.handle_device_delete({"device_id": device_id}))

    @router.post("/devices/delete", deprecated=True)
    async def delete_device(req: DeviceDeleteRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_device_delete(req.model_dump()))

    return router
