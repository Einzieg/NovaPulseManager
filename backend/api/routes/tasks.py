from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.api.routes.utils import call_handler
from backend.core.api.schemas import StartTaskRequest, StopTaskRequest


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["tasks"])

    @router.post("/tasks/start", deprecated=True)
    async def start_task(req: StartTaskRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_task_start(req.model_dump()))

    @router.post("/tasks/stop", deprecated=True)
    async def stop_task(req: StopTaskRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_task_stop(req.model_dump()))

    return router
