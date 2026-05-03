from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.api.routes.utils import call_handler
from backend.core.api.schemas import ConfigUpdateRequest


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["settings"])

    @router.get("/config")
    async def get_config() -> Dict[str, Any]:
        return await call_handler(handlers.handle_config_get({}))

    @router.post("/config/update")
    async def update_config(req: ConfigUpdateRequest) -> Dict[str, Any]:
        return await call_handler(
            handlers.handle_config_update(req.model_dump(exclude_none=True))
        )

    return router
