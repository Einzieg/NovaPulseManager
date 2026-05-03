import json

from backend.application.services import DeviceService, WorkflowService
from backend.models import DeviceConfig, Workflow
from backend.models.CommonConfig import CommonConfig
from database.db_session import init_database


def test_device_service_core_crud(temp_db_path):
    init_database(db_path=temp_db_path)
    service = DeviceService()
    cleared = []

    created = service.create_device(
        {"name": "svc-device-a", "simulator_index": 1, "port": 18001}
    )
    device_id = created["device"]["id"]

    listed = service.list_devices(lambda _: None)
    assert [device["name"] for device in listed["devices"]] == ["svc-device-a"]
    assert CommonConfig.select().where(CommonConfig.device == device_id).count() == 1

    Workflow.create(
        workflow_id="svc-workflow-a",
        name="Workflow A",
        module_name="svc-device-a",
        workflow_data=json.dumps({"id": "svc-workflow-a", "module_name": "svc-device-a"}),
    )

    updated = service.update_device(
        {
            "device_id": device_id,
            "name": "svc-device-b",
            "simulator_index": 2,
            "port": 18002,
        },
        is_running=lambda _: False,
        clear_scheduler=cleared.append,
    )

    assert updated["device"]["name"] == "svc-device-b"
    assert cleared == ["svc-device-a"]
    workflow = Workflow.get(Workflow.workflow_id == "svc-workflow-a")
    assert workflow.module_name == "svc-device-b"
    assert json.loads(workflow.workflow_data)["module_name"] == "svc-device-a"

    deleted = service.delete_device(
        {"device_id": device_id},
        is_running=lambda _: False,
        clear_scheduler=cleared.append,
    )

    assert deleted == {"deleted": True}
    assert DeviceConfig.get_or_none(DeviceConfig.id == device_id) is None
    assert Workflow.get(Workflow.workflow_id == "svc-workflow-a").is_active is False


def test_workflow_service_core_crud(temp_db_path):
    init_database(db_path=temp_db_path)
    device = DeviceConfig.create(name="svc-workflow-device", simulator_index=0, port=16384)
    CommonConfig.create(device=device)
    service = WorkflowService()

    payload = {
        "module_name": device.name,
        "workflow_data": {
            "id": "svc-workflow-1",
            "name": "Original",
            "nodes": [{"id": "node-1"}],
            "edges": [],
        },
    }
    created = service.save_workflow(payload)
    assert created["created"] is True

    payload["workflow_data"]["name"] = "Updated"
    updated = service.save_workflow(payload)
    assert updated["created"] is False

    loaded = service.load_workflow({"module_name": device.name})
    assert loaded["workflow_id"] == "svc-workflow-1"
    assert loaded["workflow_data"]["name"] == "Updated"

    listed = service.list_workflows({"module_name": device.name})
    assert [workflow["workflow_id"] for workflow in listed["workflows"]] == [
        "svc-workflow-1"
    ]

    service.set_current_workflow(
        {"device_id": device.id, "workflow_id": "svc-workflow-1"}
    )
    common_cfg = CommonConfig.get(CommonConfig.device == device.id)
    assert common_cfg.current_workflow_id == "svc-workflow-1"
    assert common_cfg.workflow_enabled is True

    deleted = service.delete_workflow({"workflow_id": "svc-workflow-1"})
    assert deleted == {"deleted": True}
    common_cfg = CommonConfig.get(CommonConfig.device == device.id)
    assert common_cfg.current_workflow_id is None
    assert common_cfg.workflow_enabled is False
