from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from backend.application.errors import DeviceNotFound, WorkflowNotFound
from backend.application.services.workflow_compat import normalize_workflow_graph
from backend.models import DeviceConfig, Workflow
from backend.models.CommonConfig import CommonConfig


class WorkflowService:
    def _stored_graph(self, workflow: Workflow) -> dict[str, Any]:
        raw_graph = workflow.graph_json or workflow.workflow_data
        return normalize_workflow_graph(json.loads(raw_graph))

    def save_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        module_name = payload.get("module_name")
        workflow_data = payload.get("workflow_data")

        if not module_name or not workflow_data:
            raise ValueError("Missing module_name or workflow_data")

        if hasattr(workflow_data, "model_dump"):
            workflow_data = workflow_data.model_dump()
        workflow_data = normalize_workflow_graph(workflow_data)

        workflow_id = workflow_data.get("id")
        if not workflow_id:
            raise ValueError("workflow_data must contain 'id' field")

        workflow_data["module_name"] = module_name

        workflow, created = Workflow.get_or_create(
            workflow_id=workflow_id,
            defaults={
                "name": workflow_data.get("name", "Untitled"),
                "description": workflow_data.get("description", ""),
                "module_name": module_name,
                "workflow_data": json.dumps(workflow_data, ensure_ascii=False),
                "graph_json": json.dumps(workflow_data, ensure_ascii=False),
                "is_active": True,
            },
        )

        if not created:
            workflow.name = workflow_data.get("name", workflow.name)
            workflow.description = workflow_data.get("description", workflow.description)
            workflow.module_name = module_name
            workflow.workflow_data = json.dumps(workflow_data, ensure_ascii=False)
            workflow.graph_json = json.dumps(workflow_data, ensure_ascii=False)
            workflow.updated_at = datetime.now()
            workflow.is_active = True
            workflow.save()

        return {
            "workflow_id": workflow_id,
            "created": created,
            "message": "Workflow saved successfully",
        }

    def load_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        module_name = payload.get("module_name")
        if not module_name:
            raise ValueError("Missing module_name")

        try:
            device = DeviceConfig.get_or_none(DeviceConfig.name == module_name)
            if device is not None:
                common_cfg, _ = CommonConfig.get_or_create(device=device)
                preferred_id = common_cfg.current_workflow_id
                if preferred_id:
                    preferred = (
                        Workflow.select()
                        .where(
                            Workflow.workflow_id == preferred_id,
                            Workflow.module_name == module_name,
                            Workflow.is_active == True,
                        )
                        .get()
                    )
                    return {
                        "workflow_id": preferred.workflow_id,
                        "workflow_data": self._stored_graph(preferred),
                    }
        except Workflow.DoesNotExist:
            pass
        except Exception:
            pass

        try:
            workflow = (
                Workflow.select()
                .where(Workflow.module_name == module_name, Workflow.is_active == True)
                .order_by(Workflow.updated_at.desc())
                .get()
            )

            return {
                "workflow_id": workflow.workflow_id,
                "workflow_data": self._stored_graph(workflow),
            }
        except Workflow.DoesNotExist:
            return {
                "workflow_id": None,
                "workflow_data": {
                    "nodes": [],
                    "edges": [],
                },
            }

    def get_start_workflow_data(self, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        module_name = payload.get("module_name")
        workflow_id = payload.get("workflow_id")

        if not module_name or not workflow_id:
            raise ValueError("Missing module_name or workflow_id")

        try:
            workflow = Workflow.get(
                Workflow.workflow_id == workflow_id,
                Workflow.module_name == module_name,
                Workflow.is_active == True,
            )
        except Workflow.DoesNotExist:
            raise WorkflowNotFound(f"Workflow {workflow_id} not found")

        return module_name, self._stored_graph(workflow)

    def get_run_target_by_workflow_id(self, workflow_id: str) -> tuple[str, dict[str, Any]]:
        workflow = Workflow.get_or_none(
            Workflow.workflow_id == workflow_id,
            Workflow.is_active == True,
        )
        if workflow is None:
            raise WorkflowNotFound(f"Workflow {workflow_id} not found")

        return workflow.module_name, self._stored_graph(workflow)

    def list_workflows(self, payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        module_name = payload.get("module_name")
        if not module_name:
            raise ValueError("Missing module_name")

        workflows = []
        for wf in (
            Workflow.select()
            .where(Workflow.module_name == module_name)
            .order_by(Workflow.updated_at.desc())
        ):
            workflows.append(
                {
                    "workflow_id": wf.workflow_id,
                    "name": wf.name,
                    "description": wf.description,
                    "module_name": wf.module_name,
                    "is_active": bool(wf.is_active),
                    "created_at": wf.created_at.isoformat() if wf.created_at else None,
                    "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
                }
            )

        return {"workflows": workflows}

    def get_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            raise ValueError("Missing workflow_id")

        wf = Workflow.get_or_none(
            Workflow.workflow_id == workflow_id,
            Workflow.is_active == True,
        )
        if wf is None:
            raise WorkflowNotFound(f"Workflow {workflow_id} not found")

        return {
            "workflow_id": wf.workflow_id,
            "workflow_data": self._stored_graph(wf),
        }

    def delete_workflow(self, payload: dict[str, Any]) -> dict[str, bool]:
        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            raise ValueError("Missing workflow_id")

        wf = Workflow.get_or_none(Workflow.workflow_id == workflow_id)
        if wf is None:
            return {"deleted": False}

        wf.is_active = False
        wf.updated_at = datetime.now()
        wf.save()

        (
            CommonConfig.update(
                {
                    CommonConfig.current_workflow_id: None,
                    CommonConfig.workflow_enabled: False,
                }
            )
            .where(CommonConfig.current_workflow_id == workflow_id)
            .execute()
        )

        return {"deleted": True}

    def set_current_workflow(self, payload: dict[str, Any]) -> dict[str, Any]:
        device_id = payload.get("device_id")
        workflow_id = payload.get("workflow_id")

        if device_id is None:
            raise ValueError("Missing device_id")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise DeviceNotFound(f"Device not found: {device_id}")

        common_cfg, _ = CommonConfig.get_or_create(device=device)

        if workflow_id:
            wf = Workflow.get_or_none(
                Workflow.workflow_id == workflow_id,
                Workflow.module_name == device.name,
                Workflow.is_active == True,
            )
            if wf is None:
                raise WorkflowNotFound(f"Workflow not found for device: {workflow_id}")

            common_cfg.current_workflow_id = str(workflow_id)
            common_cfg.workflow_enabled = True
        else:
            common_cfg.current_workflow_id = None
            common_cfg.workflow_enabled = False

        common_cfg.save()

        return {
            "device_id": device.id,
            "module_name": device.name,
            "current_workflow_id": common_cfg.current_workflow_id,
            "workflow_enabled": bool(common_cfg.workflow_enabled),
        }
