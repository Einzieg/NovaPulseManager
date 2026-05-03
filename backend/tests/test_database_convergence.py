import json

from backend.models import SchemaVersion, Workflow
from database.db_session import db, init_database


def test_init_database_migrates_workflow_data_to_graph_json_without_count_change(temp_db_path):
    init_database(db_path=temp_db_path)
    Workflow.create(
        workflow_id="legacy-migrate",
        name="Legacy Migrate",
        module_name="device-a",
        workflow_data=json.dumps(
            {
                "id": "legacy-migrate",
                "nodes": [{"id": "node-1", "plugin_id": "permanent_task"}],
                "edges": [],
            }
        ),
    )
    before_count = Workflow.select().count()

    init_database(db_path=temp_db_path)

    after_count = Workflow.select().count()
    workflow = Workflow.get(Workflow.workflow_id == "legacy-migrate")
    graph = json.loads(workflow.graph_json)

    assert before_count == after_count == 1
    assert graph["schema_version"] == 2
    assert graph["nodes"][0]["action_ref"] == "nova_iron_galaxy.permanent.run"
    assert SchemaVersion.get(SchemaVersion.name == "workflow_graph").version == 2


def test_init_database_does_not_create_legacy_tables_by_default(temp_db_path):
    init_database(db_path=temp_db_path)
    tables = set(db.get_tables())

    assert "module" not in tables
    assert "plugin_config" not in tables
    assert "common_config" in tables
    assert "schema_version" in tables
