from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

from backend.api.routes.utils import call_handler


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["runs"])

    @router.post("/workflows/{workflow_id}/runs")
    async def start_workflow_run(workflow_id: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_run_start({"workflow_id": workflow_id}))

    @router.get("/runs/{run_id}")
    async def get_run(run_id: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_run_get({"run_id": run_id}))

    @router.post("/runs/{run_id}/cancel")
    async def cancel_run(run_id: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_run_cancel({"run_id": run_id}))

    @router.get("/runs")
    async def list_runs() -> Dict[str, Any]:
        return await call_handler(handlers.handle_run_list({}))

    return router
