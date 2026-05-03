from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.api.routes.utils import call_handler


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["apps"])

    @router.get("/apps")
    async def list_apps() -> Dict[str, Any]:
        return await call_handler(handlers.handle_app_list({}))

    return router
