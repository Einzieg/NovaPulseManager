from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Callable
from uuid import uuid4

from backend.application.errors import DeviceAlreadyRunning, WorkflowNotFound
from backend.application.services.workflow_service import WorkflowService
from backend.domain.run import WorkflowRun
from backend.infrastructure.realtime.event_bus import EventBus


class RunService:
    def __init__(
        self,
        *,
        workflow_service: WorkflowService,
        scheduler_getter: Callable[[str], object],
        scheduler_lookup: Callable[[str], object | None],
        event_bus: EventBus,
    ):
        self.workflow_service = workflow_service
        self.scheduler_getter = scheduler_getter
        self.scheduler_lookup = scheduler_lookup
        self.event_bus = event_bus
        self._runs: dict[str, WorkflowRun] = {}
        self._active_run_by_module: dict[str, str] = {}

    async def start_workflow(self, payload: dict) -> dict:
        module_name, workflow_data = self.workflow_service.get_start_workflow_data(payload)
        workflow_id = payload["workflow_id"]
        return await self._start(module_name, workflow_id, workflow_data)

    async def start_workflow_by_id(self, workflow_id: str) -> dict:
        if not workflow_id:
            raise ValueError("Missing workflow_id")
        module_name, workflow_data = self.workflow_service.get_run_target_by_workflow_id(
            workflow_id
        )
        return await self._start(module_name, workflow_id, workflow_data)

    async def _start(self, module_name: str, workflow_id: str, workflow_data: dict) -> dict:
        active_run_id = self._active_run_by_module.get(module_name)
        if active_run_id:
            active_run = self._runs.get(active_run_id)
            if active_run and active_run.status in {"pending", "running", "cancelling"}:
                raise DeviceAlreadyRunning(f"Device already running: {module_name}")

        scheduler = self.scheduler_lookup(module_name)
        if scheduler and scheduler.get_status().get("is_running"):
            raise DeviceAlreadyRunning(f"Device already running: {module_name}")

        run_id = f"run-{uuid4().hex}"
        run = WorkflowRun(
            run_id=run_id,
            workflow_id=workflow_id,
            module_name=module_name,
            status="pending",
        )
        self._runs[run_id] = run
        self._active_run_by_module[module_name] = run_id

        scheduler = self.scheduler_getter(module_name)
        try:
            await scheduler.start_workflow(
                workflow_data,
                run_id=run_id,
                event_bus=self.event_bus,
            )
        except Exception:
            self._active_run_by_module.pop(module_name, None)
            self._runs.pop(run_id, None)
            raise

        run.status = "running"
        run.started_at = datetime.now()
        await self._publish_status(run)

        task = getattr(scheduler, "current_task", None)
        if task is not None:
            asyncio.create_task(self._watch_scheduler_task(run_id, module_name, task, scheduler))

        return {
            "status": "started",
            "run_id": run_id,
            "workflow_id": workflow_id,
            "module": module_name,
            "mode": "workflow",
        }

    async def _watch_scheduler_task(
        self,
        run_id: str,
        module_name: str,
        task,
        scheduler,
    ) -> None:
        run = self._runs.get(run_id)
        if run is None:
            return

        try:
            await task
        except asyncio.CancelledError:
            run.status = "cancelled"
        except Exception as e:
            run.status = "failed"
            run.error = str(e)
        else:
            result = getattr(scheduler, "last_result", None)
            if result is not None and not getattr(result, "success", False):
                run.status = "failed"
                run.error = getattr(result, "error", None)
            elif run.status != "cancelled":
                run.status = "succeeded"
        finally:
            if run.status == "cancelling":
                run.status = "cancelled"
            run.finished_at = datetime.now()
            self._active_run_by_module.pop(module_name, None)
            await self._publish_status(run)

    async def cancel_run(self, run_id: str) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            raise WorkflowNotFound(f"Run {run_id} not found")

        if run.status not in {"pending", "running"}:
            return run.to_dict()

        run.status = "cancelling"
        await self._publish_status(run)

        scheduler = self.scheduler_lookup(run.module_name)
        if scheduler is not None:
            await scheduler.stop_workflow()

        run.status = "cancelled"
        run.finished_at = datetime.now()
        self._active_run_by_module.pop(run.module_name, None)
        await self._publish_status(run)
        return run.to_dict()

    def get_run(self, run_id: str) -> dict:
        run = self._runs.get(run_id)
        if run is None:
            raise WorkflowNotFound(f"Run {run_id} not found")
        return run.to_dict()

    def list_runs(self) -> dict[str, list[dict]]:
        return {"runs": [run.to_dict() for run in self._runs.values()]}

    async def _publish_status(self, run: WorkflowRun) -> None:
        await self.event_bus.publish("run.status_changed", run.to_dict())
