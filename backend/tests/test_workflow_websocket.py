"""工作流消息处理集成测试（FastAPI-only）"""

import asyncio
from pathlib import Path

import pytest

from backend.core.websocket import MessageHandlers
from backend.models import CommonConfig, DeviceConfig, Workflow
from database.db_session import init_database

MODULE_NAME = "pytest-module"


class DummyBroadcaster:
    async def broadcast(self, event: str, data):
        return


@pytest.fixture
def ws_broadcaster():
    return DummyBroadcaster()


@pytest.fixture
def handlers(ws_broadcaster):
    plugins_dir = Path("backend/plugins")
    return MessageHandlers(plugins_dir, ws_broadcaster)


@pytest.fixture(autouse=True)
def setup_database(temp_db_path):
    init_database(db_path=temp_db_path)

    device, _ = DeviceConfig.get_or_create(
        name=MODULE_NAME,
        defaults={"simulator_index": 0, "port": 16384},
    )

    CommonConfig.get_or_create(device=device)

    yield

    Workflow.delete().where(Workflow.module_name == MODULE_NAME).execute()
    CommonConfig.delete().where(CommonConfig.device == device.id).execute()
    DeviceConfig.delete().where(DeviceConfig.id == device.id).execute()


@pytest.mark.asyncio
async def test_workflow_save_and_load(handlers):
    workflow_data = {
        "id": "test-workflow-001",
        "name": "Test Workflow",
        "description": "Integration test workflow",
        "module_name": MODULE_NAME,
        "nodes": [{"id": "node-1", "position": {"x": 100, "y": 100}}],
        "edges": [],
    }

    save_result = await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )

    assert save_result["workflow_id"] == "test-workflow-001"
    assert save_result["created"] is True
    assert save_result["message"] == "Workflow saved successfully"

    load_result = await handlers.handle_workflow_load({"module_name": MODULE_NAME})

    assert load_result["workflow_id"] == "test-workflow-001"
    assert load_result["workflow_data"]["id"] == "test-workflow-001"
    assert load_result["workflow_data"]["name"] == "Test Workflow"
    assert len(load_result["workflow_data"]["nodes"]) == 1


@pytest.mark.asyncio
async def test_workflow_save_update(handlers):
    workflow_data = {
        "id": "test-workflow-002",
        "name": "Original Name",
        "module_name": MODULE_NAME,
        "nodes": [],
        "edges": [],
    }

    save_result1 = await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )
    assert save_result1["created"] is True

    workflow_data["name"] = "Updated Name"
    workflow_data["description"] = "New description"

    save_result2 = await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )
    assert save_result2["created"] is False
    assert save_result2["workflow_id"] == "test-workflow-002"

    load_result = await handlers.handle_workflow_load({"module_name": MODULE_NAME})
    assert load_result["workflow_data"]["name"] == "Updated Name"
    assert load_result["workflow_data"]["description"] == "New description"


@pytest.mark.asyncio
async def test_workflow_start_lightweight(handlers):
    """测试启动工作流（不执行真实插件，仅验证调度链路）"""

    workflow_data = {
        "id": "test-workflow-start",
        "name": "Startable Workflow",
        "module_name": MODULE_NAME,
        "nodes": [{"id": "node-1", "position": {"x": 100, "y": 100}}],
        "edges": [],
    }

    await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )

    start_result = await handlers.handle_workflow_start(
        {"module_name": MODULE_NAME, "workflow_id": "test-workflow-start"}
    )

    assert start_result["status"] == "started"
    assert start_result["module"] == MODULE_NAME
    assert start_result["workflow_id"] == "test-workflow-start"
    assert start_result["mode"] == "workflow"

    # 让后台 task 有机会完成
    await asyncio.sleep(0)

    scheduler = handlers._get_scheduler(MODULE_NAME)
    await scheduler.stop_workflow()


@pytest.mark.asyncio
async def test_workflow_start_uses_v2_action_executor(handlers, monkeypatch):
    """Action workflow must not be sent to the legacy plugin loader."""

    action_calls = []
    legacy_load_calls = []
    device = DeviceConfig.get(DeviceConfig.name == MODULE_NAME)

    class FakeAction:
        async def prepare(self):
            action_calls.append("prepare")

        async def execute(self):
            action_calls.append("execute")

        async def cleanup(self):
            action_calls.append("cleanup")

    def fake_create(self, action_ref, ctx):
        action_calls.append((action_ref, ctx.run_id, ctx.device_id, ctx.device_name))
        return FakeAction()

    def fake_load_plugin(self, plugin_id, target):
        legacy_load_calls.append((plugin_id, target))
        raise AssertionError("action_ref should not use legacy plugin loader")

    monkeypatch.setattr(
        "backend.infrastructure.plugins.factory.ActionFactory.create",
        fake_create,
    )
    monkeypatch.setattr(
        "backend.core.plugins.manager.PluginManager.load_plugin",
        fake_load_plugin,
    )

    workflow_data = {
        "schema_version": 2,
        "id": "test-action-workflow-start",
        "name": "Action Workflow",
        "module_name": MODULE_NAME,
        "nodes": [
            {
                "id": "node-1",
                "type": "action",
                "app_id": "nova_iron_galaxy",
                "module_id": "order",
                "action_id": "run",
                "action_ref": "nova_iron_galaxy.order.run",
                "device_id": device.id,
                "position": {"x": 100, "y": 100},
                "config": {},
            }
        ],
        "edges": [],
    }

    await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )
    start_result = await handlers.handle_workflow_start(
        {"module_name": MODULE_NAME, "workflow_id": "test-action-workflow-start"}
    )

    scheduler = handlers.schedulers[MODULE_NAME]
    task = scheduler.current_task
    assert task is not None
    await task

    assert legacy_load_calls == []
    assert action_calls == [
        (
            "nova_iron_galaxy.order.run",
            start_result["run_id"],
            device.id,
            MODULE_NAME,
        ),
        "prepare",
        "execute",
        "cleanup",
    ]
    assert scheduler.last_result.success is True


@pytest.mark.asyncio
async def test_unmapped_legacy_workflow_still_uses_plugin_executor(handlers, monkeypatch):
    load_calls = []
    lifecycle_calls = []

    class DummyPlugin:
        async def prepare(self):
            lifecycle_calls.append("prepare")

        async def execute(self):
            lifecycle_calls.append("execute")

        async def cleanup(self):
            lifecycle_calls.append("cleanup")

    def fake_load_plugin(self, plugin_id, target):
        load_calls.append((plugin_id, target))
        return DummyPlugin()

    monkeypatch.setattr(
        "backend.core.plugins.manager.PluginManager.load_plugin",
        fake_load_plugin,
    )

    workflow_data = {
        "id": "test-legacy-plugin-workflow-start",
        "name": "Legacy Plugin Workflow",
        "module_name": MODULE_NAME,
        "nodes": [
            {
                "id": "node-1",
                "plugin_id": "custom-plugin",
                "position": {"x": 100, "y": 100},
                "config": {},
            }
        ],
        "edges": [],
    }

    await handlers.handle_workflow_save(
        {"module_name": MODULE_NAME, "workflow_data": workflow_data}
    )
    await handlers.handle_workflow_start(
        {"module_name": MODULE_NAME, "workflow_id": "test-legacy-plugin-workflow-start"}
    )

    scheduler = handlers.schedulers[MODULE_NAME]
    task = scheduler.current_task
    assert task is not None
    await task

    assert load_calls == [("custom-plugin", MODULE_NAME)]
    assert lifecycle_calls == ["prepare", "execute", "cleanup"]
    assert scheduler.last_result.success is True


@pytest.mark.asyncio
async def test_workflow_not_found(handlers):
    """测试工作流不存在时的行为"""

    load_result = await handlers.handle_workflow_load({"module_name": "NonExistentModule"})
    assert load_result["workflow_id"] is None
    assert load_result["workflow_data"]["nodes"] == []

    with pytest.raises(ValueError, match="Workflow .* not found"):
        await handlers.handle_workflow_start(
            {"module_name": MODULE_NAME, "workflow_id": "non-existent-workflow"}
        )


@pytest.mark.asyncio
async def test_workflow_missing_fields(handlers):
    with pytest.raises(ValueError, match="Missing module_name or workflow_data"):
        await handlers.handle_workflow_save({"workflow_data": {}})

    with pytest.raises(ValueError, match="Missing module_name or workflow_data"):
        await handlers.handle_workflow_save({"module_name": MODULE_NAME})

    with pytest.raises(ValueError, match="workflow_data must contain 'id' field"):
        await handlers.handle_workflow_save(
            {"module_name": MODULE_NAME, "workflow_data": {"name": "No ID"}}
        )

    with pytest.raises(ValueError, match="Missing module_name"):
        await handlers.handle_workflow_load({})

    with pytest.raises(ValueError, match="Missing module_name or workflow_id"):
        await handlers.handle_workflow_start({"module_name": MODULE_NAME})
