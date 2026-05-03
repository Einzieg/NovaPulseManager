from __future__ import annotations

from datetime import datetime
from typing import Any, Callable

from peewee import IntegrityError

from backend.application.errors import DeviceAlreadyRunning, DeviceNotFound
from backend.models import DeviceConfig, Workflow
from backend.models.CommonConfig import CommonConfig


class DeviceService:
    def list_devices(
        self,
        status_provider: Callable[[str], dict[str, Any] | None],
    ) -> dict[str, list[dict[str, Any]]]:
        modules = []
        for device in DeviceConfig.select().order_by(DeviceConfig.id.asc()):
            status = status_provider(device.name) or {
                "is_running": False,
                "execution_mode": "plugin",
            }
            common_cfg, _ = CommonConfig.get_or_create(device=device)

            execution_mode = status.get("execution_mode") or "plugin"
            running_workflow_id = (
                status.get("workflow_id") if execution_mode == "workflow" else None
            )

            modules.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "simulator_index": device.simulator_index,
                    "port": device.port,
                    "is_running": bool(status.get("is_running")),
                    "execution_mode": execution_mode,
                    "current_plugin": status.get("current_plugin"),
                    "running_workflow_id": running_workflow_id,
                    "current_workflow_id": common_cfg.current_workflow_id,
                    "workflow_enabled": bool(common_cfg.workflow_enabled),
                }
            )

        return {"modules": modules, "devices": modules}

    def create_device(self, payload: dict[str, Any]) -> dict[str, Any]:
        name = payload.get("name")
        simulator_index = payload.get("simulator_index")
        port = payload.get("port")

        if not name:
            raise ValueError("Missing name")
        if simulator_index is None:
            raise ValueError("Missing simulator_index")
        if port is None:
            raise ValueError("Missing port")

        try:
            device = DeviceConfig.create(
                name=str(name),
                simulator_index=int(simulator_index),
                port=int(port),
            )
        except IntegrityError as e:
            raise ValueError(f"Device name already exists: {name}") from e

        CommonConfig.get_or_create(device=device)

        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "simulator_index": device.simulator_index,
                "port": device.port,
                "is_running": False,
                "execution_mode": "plugin",
                "current_plugin": None,
                "running_workflow_id": None,
                "current_workflow_id": None,
                "workflow_enabled": False,
            }
        }

    def update_device(
        self,
        payload: dict[str, Any],
        *,
        is_running: Callable[[str], bool],
        clear_scheduler: Callable[[str], None],
    ) -> dict[str, Any]:
        device_id = payload.get("device_id")
        name = payload.get("name")
        simulator_index = payload.get("simulator_index")
        port = payload.get("port")

        if device_id is None:
            raise ValueError("Missing device_id")
        if not name:
            raise ValueError("Missing name")
        if simulator_index is None:
            raise ValueError("Missing simulator_index")
        if port is None:
            raise ValueError("Missing port")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise DeviceNotFound(f"Device not found: {device_id}")

        old_name = device.name
        new_name = str(name)

        if is_running(old_name):
            raise DeviceAlreadyRunning("Device is running, cannot update")

        device.name = new_name
        device.simulator_index = int(simulator_index)
        device.port = int(port)

        try:
            device.save()
        except IntegrityError as e:
            raise ValueError(f"Device name already exists: {new_name}") from e

        common_cfg, _ = CommonConfig.get_or_create(device=device)

        if old_name != new_name:
            for wf in Workflow.select().where(Workflow.module_name == old_name):
                wf.module_name = new_name
                wf.updated_at = datetime.now()
                wf.save()

        clear_scheduler(old_name)

        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "simulator_index": device.simulator_index,
                "port": device.port,
                "is_running": False,
                "execution_mode": "plugin",
                "current_plugin": None,
                "running_workflow_id": None,
                "current_workflow_id": common_cfg.current_workflow_id,
                "workflow_enabled": bool(common_cfg.workflow_enabled),
            }
        }

    def delete_device(
        self,
        payload: dict[str, Any],
        *,
        is_running: Callable[[str], bool],
        clear_scheduler: Callable[[str], None],
    ) -> dict[str, bool]:
        device_id = payload.get("device_id")
        if device_id is None:
            raise ValueError("Missing device_id")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise DeviceNotFound(f"Device not found: {device_id}")

        if is_running(device.name):
            raise DeviceAlreadyRunning("Device is running, cannot delete")

        now = datetime.now()
        (
            Workflow.update({Workflow.is_active: False, Workflow.updated_at: now})
            .where(Workflow.module_name == device.name)
            .execute()
        )

        (
            CommonConfig.update(
                {
                    CommonConfig.current_workflow_id: None,
                    CommonConfig.workflow_enabled: False,
                }
            )
            .where(CommonConfig.device == device.id)
            .execute()
        )

        CommonConfig.delete().where(CommonConfig.device == device.id).execute()
        old_name = device.name
        device.delete_instance()
        clear_scheduler(old_name)

        return {"deleted": True}
