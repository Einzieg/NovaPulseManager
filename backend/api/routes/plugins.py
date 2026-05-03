from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.api.routes.utils import call_handler
from backend.core.api.schemas import PluginConfigUpdateRequest


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["plugins"])

    @router.get("/plugins", deprecated=True)
    async def list_plugins() -> Dict[str, Any]:
        return await call_handler(handlers.handle_plugin_list({}))

    @router.get("/plugins/config", deprecated=True)
    async def get_plugin_config(device_name: str, plugin_id: str) -> Dict[str, Any]:
        return await call_handler(
            handlers.handle_plugin_config_get(
                {"device_name": device_name, "plugin_id": plugin_id}
            )
        )

    @router.post("/plugins/config/update", deprecated=True)
    async def update_plugin_config(req: PluginConfigUpdateRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_plugin_config_update(req.model_dump()))

    return router
