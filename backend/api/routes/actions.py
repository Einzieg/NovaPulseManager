from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter

from backend.api.routes.utils import call_handler


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["actions"])

    @router.get("/actions")
    async def list_actions(
        app_id: Optional[str] = None,
        module_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return await call_handler(
            handlers.handle_action_list({"app_id": app_id, "module_id": module_id})
        )

    return router
