from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter

from backend.api.routes.utils import call_handler
from backend.core.api.schemas import (
    DeleteWorkflowRequest,
    SaveWorkflowRequest,
    SetCurrentWorkflowRequest,
    StartWorkflowRequest,
    StopWorkflowRequest,
)


def create_router(handlers) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["workflows"])

    @router.get("/workflows")
    async def list_workflows_resource(module_name: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_list({"module_name": module_name}))

    @router.post("/workflows")
    async def save_workflow_resource(req: SaveWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_save(req.model_dump()))

    @router.post("/workflows/save", deprecated=True)
    async def save_workflow(req: SaveWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_save(req.model_dump()))

    @router.get("/workflows/load", deprecated=True)
    async def load_workflow(module_name: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_load({"module_name": module_name}))

    @router.get("/workflows/list", deprecated=True)
    async def list_workflows(module_name: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_list({"module_name": module_name}))

    @router.get("/workflows/get", deprecated=True)
    async def get_workflow(
        workflow_id: str,
        module_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"workflow_id": workflow_id}
        if module_name:
            payload["module_name"] = module_name
        return await call_handler(handlers.handle_workflow_get(payload))

    @router.post("/workflows/delete", deprecated=True)
    async def delete_workflow(req: DeleteWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_delete(req.model_dump()))

    @router.post("/workflows/set-current", deprecated=True)
    async def set_current_workflow(req: SetCurrentWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_set_current(req.model_dump()))

    @router.post("/workflows/stop", deprecated=True)
    async def stop_workflow(req: StopWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_stop(req.model_dump()))

    @router.post("/workflows/start", deprecated=True)
    async def start_workflow(req: StartWorkflowRequest) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_start(req.model_dump()))

    @router.get("/workflows/{workflow_id}")
    async def get_workflow_resource(workflow_id: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_get({"workflow_id": workflow_id}))

    @router.patch("/workflows/{workflow_id}")
    async def update_workflow_resource(
        workflow_id: str,
        req: SaveWorkflowRequest,
    ) -> Dict[str, Any]:
        payload = req.model_dump()
        payload["workflow_data"]["id"] = workflow_id
        return await call_handler(handlers.handle_workflow_save(payload))

    @router.delete("/workflows/{workflow_id}")
    async def delete_workflow_resource(workflow_id: str) -> Dict[str, Any]:
        return await call_handler(handlers.handle_workflow_delete({"workflow_id": workflow_id}))

    return router
