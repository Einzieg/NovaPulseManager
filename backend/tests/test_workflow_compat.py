import json

from backend.application.services.workflow_compat import normalize_workflow_graph
from backend.application.services.workflow_service import WorkflowService
from backend.models import Workflow
from database.db_session import init_database


def test_normalize_legacy_workflow_to_schema_v2_preserves_node_config():
    normalized = normalize_workflow_graph(
        {
            "id": "legacy",
            "nodes": [
                {
                    "id": "node-1",
                    "plugin_id": "permanent_task",
                    "position": {"x": 1, "y": 2},
                    "config": {"monster_type": "elite"},
                }
            ],
            "edges": [],
        }
    )

    node = normalized["nodes"][0]
    assert normalized["schema_version"] == 2
    assert node["type"] == "action"
    assert node["app_id"] == "nova_iron_galaxy"
    assert node["module_id"] == "permanent"
    assert node["action_id"] == "run"
    assert node["action_ref"] == "nova_iron_galaxy.permanent.run"
    assert node["config"] == {"monster_type": "elite"}


def test_workflow_service_loads_old_workflow_as_v2(temp_db_path):
    init_database(db_path=temp_db_path)
    Workflow.create(
        workflow_id="legacy-load",
        name="Legacy Load",
        module_name="device-a",
        workflow_data=json.dumps(
            {
                "id": "legacy-load",
                "nodes": [{"id": "node-1", "plugin_id": "order-task"}],
                "edges": [],
            }
        ),
    )

    loaded = WorkflowService().load_workflow({"module_name": "device-a"})

    assert loaded["workflow_data"]["schema_version"] == 2
    assert loaded["workflow_data"]["nodes"][0]["action_ref"] == "nova_iron_galaxy.order.run"


def test_workflow_service_saves_loads_and_resaves_schema_v2(temp_db_path):
    init_database(db_path=temp_db_path)
    service = WorkflowService()
    graph = {
        "schema_version": 2,
        "id": "v2-workflow",
        "name": "V2 Workflow",
        "nodes": [
            {
                "id": "node-1",
                "type": "action",
                "app_id": "nova_iron_galaxy",
                "module_id": "radar",
                "action_id": "run",
                "action_ref": "nova_iron_galaxy.radar.run",
                "device_id": 1,
                "position": {"x": 10, "y": 20},
                "config": {"scan": True},
            }
        ],
        "edges": [],
    }

    created = service.save_workflow({"module_name": "device-a", "workflow_data": graph})
    loaded = service.load_workflow({"module_name": "device-a"})
    saved_again = service.save_workflow(
        {"module_name": "device-a", "workflow_data": loaded["workflow_data"]}
    )

    assert created["created"] is True
    assert saved_again["created"] is False
    assert loaded["workflow_data"]["schema_version"] == 2
    assert loaded["workflow_data"]["nodes"][0]["config"] == {"scan": True}
