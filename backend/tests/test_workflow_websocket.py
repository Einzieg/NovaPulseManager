"""工作流消息处理集成测试（FastAPI-only）"""

import asyncio
from pathlib import Path

import pytest

from backend.core.websocket import MessageHandlers
from backend.models import DeviceConfig, PluginConfig, Workflow
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
def setup_database():
    init_database()

    device, _ = DeviceConfig.get_or_create(
        name=MODULE_NAME,
        defaults={"simulator_index": 0, "port": 16384},
    )

    # 保证该设备只有一个 PluginConfig（TaskBase 使用 get()）
    PluginConfig.delete().where(PluginConfig.device == device.id).execute()
    PluginConfig.create(device=device)

    yield

    Workflow.delete().where(Workflow.module_name == MODULE_NAME).execute()
    PluginConfig.delete().where(PluginConfig.device == device.id).execute()
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
