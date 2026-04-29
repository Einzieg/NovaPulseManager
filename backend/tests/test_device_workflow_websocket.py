"""设备CRUD + 工作流关联（WebSocket handlers）集成测试。

覆盖：
- 设备新增/编辑(含改名)/删除
- 改名同步 Workflow.module_name 与 workflow_data JSON
- 多工作流：set_current / delete 清理 PluginConfig.current_workflow_id
- 工作流 start/stop（stop 需能在运行中停止）
"""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

import pytest

from backend.core.websocket import MessageHandlers
from backend.models import DeviceConfig, PluginConfig, Workflow
from database.db_session import init_database


TEST_DEVICE_PREFIX = "pytest-device-"


def _new_device_name() -> str:
    return f"{TEST_DEVICE_PREFIX}{uuid4().hex[:10]}"


def _new_workflow_id() -> str:
    return f"pytest-workflow-{uuid4().hex[:10]}"


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
    """初始化DB，并清理 pytest 前缀的测试数据，避免污染开发库。"""

    init_database()
    yield

    # 先删 Workflow（不依赖 DeviceConfig 外键）
    Workflow.delete().where(Workflow.module_name.startswith(TEST_DEVICE_PREFIX)).execute()

    # 再删 PluginConfig + DeviceConfig
    device_ids = [
        d.id
        for d in DeviceConfig.select(DeviceConfig.id).where(
            DeviceConfig.name.startswith(TEST_DEVICE_PREFIX)
        )
    ]
    if device_ids:
        PluginConfig.delete().where(PluginConfig.device.in_(device_ids)).execute()
        DeviceConfig.delete().where(DeviceConfig.id.in_(device_ids)).execute()


@pytest.mark.asyncio
async def test_device_create_and_plugin_config_one_to_one(handlers):
    name = _new_device_name()

    result = await handlers.handle_device_create(
        {"name": name, "simulator_index": 7, "port": 17000}
    )
    device = result["device"]

    assert device["name"] == name
    assert device["simulator_index"] == 7
    assert device["port"] == 17000
    assert device["current_workflow_id"] is None
    assert device["workflow_enabled"] is False

    db_device = DeviceConfig.get(DeviceConfig.id == device["id"])
    assert db_device.name == name

    cfgs = list(PluginConfig.select().where(PluginConfig.device == db_device.id))
    assert len(cfgs) == 1


@pytest.mark.asyncio
async def test_device_update_rename_syncs_workflows_and_clears_scheduler_cache(handlers):
    old_name = _new_device_name()
    new_name = _new_device_name()

    created = await handlers.handle_device_create(
        {"name": old_name, "simulator_index": 1, "port": 18001}
    )
    device_id = created["device"]["id"]

    # 创建 scheduler 缓存，验证改名后会清理旧 key
    handlers._get_scheduler(old_name)
    assert old_name in handlers.schedulers

    wf1_id = _new_workflow_id()
    wf2_id = _new_workflow_id()

    await handlers.handle_workflow_save(
        {
            "module_name": old_name,
            "workflow_data": {
                "id": wf1_id,
                "name": "WF 1",
                "module_name": old_name,
                "nodes": [],
                "edges": [],
            },
        }
    )
    await handlers.handle_workflow_save(
        {
            "module_name": old_name,
            "workflow_data": {
                "id": wf2_id,
                "name": "WF 2",
                "module_name": old_name,
                "nodes": [],
                "edges": [],
            },
        }
    )

    # 选择 wf1 为 current
    await handlers.handle_workflow_set_current({"device_id": device_id, "workflow_id": wf1_id})

    # 改名 + 改配置
    updated = await handlers.handle_device_update(
        {
            "device_id": device_id,
            "name": new_name,
            "simulator_index": 2,
            "port": 18002,
        }
    )
    assert updated["device"]["name"] == new_name
    assert updated["device"]["simulator_index"] == 2
    assert updated["device"]["port"] == 18002

    # 1) 工作流 module_name & workflow_data JSON 同步
    for wf_id in (wf1_id, wf2_id):
        wf = Workflow.get(Workflow.workflow_id == wf_id)
        assert wf.module_name == new_name
        data = json.loads(wf.workflow_data)
        assert data["module_name"] == new_name

    # 2) current_workflow_id 保持不变（workflow_id 不变）
    plugin_cfg = PluginConfig.get(PluginConfig.device == device_id)
    assert plugin_cfg.current_workflow_id == wf1_id
    assert plugin_cfg.workflow_enabled is True

    # 3) scheduler 缓存清理旧 key
    assert old_name not in handlers.schedulers


@pytest.mark.asyncio
async def test_device_update_blocked_when_running(handlers):
    name = _new_device_name()
    created = await handlers.handle_device_create(
        {"name": name, "simulator_index": 3, "port": 19003}
    )
    device_id = created["device"]["id"]

    scheduler = handlers._get_scheduler(name)
    scheduler.is_running = True
    scheduler.execution_mode = "workflow"

    with pytest.raises(ValueError, match="Device is running, cannot update"):
        await handlers.handle_device_update(
            {"device_id": device_id, "name": name, "simulator_index": 4, "port": 19004}
        )


@pytest.mark.asyncio
async def test_device_delete_soft_deletes_workflows_and_clears_scheduler(handlers):
    name = _new_device_name()
    created = await handlers.handle_device_create(
        {"name": name, "simulator_index": 9, "port": 20009}
    )
    device_id = created["device"]["id"]

    wf_id = _new_workflow_id()
    await handlers.handle_workflow_save(
        {
            "module_name": name,
            "workflow_data": {
                "id": wf_id,
                "name": "To Be Disabled",
                "module_name": name,
                "nodes": [],
                "edges": [],
            },
        }
    )
    await handlers.handle_workflow_set_current({"device_id": device_id, "workflow_id": wf_id})

    handlers._get_scheduler(name)
    assert name in handlers.schedulers

    deleted = await handlers.handle_device_delete({"device_id": device_id})
    assert deleted["deleted"] is True

    assert DeviceConfig.get_or_none(DeviceConfig.id == device_id) is None
    assert PluginConfig.select().where(PluginConfig.device == device_id).count() == 0

    wf = Workflow.get(Workflow.workflow_id == wf_id)
    assert wf.is_active is False

    assert name not in handlers.schedulers


@pytest.mark.asyncio
async def test_workflow_set_current_toggle_and_validation(handlers):
    device_name = _new_device_name()
    created = await handlers.handle_device_create(
        {"name": device_name, "simulator_index": 0, "port": 21000}
    )
    device_id = created["device"]["id"]

    wf_id = _new_workflow_id()
    await handlers.handle_workflow_save(
        {
            "module_name": device_name,
            "workflow_data": {
                "id": wf_id,
                "name": "Selectable",
                "module_name": device_name,
                "nodes": [],
                "edges": [],
            },
        }
    )

    set_result = await handlers.handle_workflow_set_current(
        {"device_id": device_id, "workflow_id": wf_id}
    )
    assert set_result["current_workflow_id"] == wf_id
    assert set_result["workflow_enabled"] is True

    clear_result = await handlers.handle_workflow_set_current(
        {"device_id": device_id, "workflow_id": None}
    )
    assert clear_result["current_workflow_id"] is None
    assert clear_result["workflow_enabled"] is False

    # 校验：不能选择别的设备的工作流
    other_name = _new_device_name()
    other_created = await handlers.handle_device_create(
        {"name": other_name, "simulator_index": 1, "port": 21001}
    )
    other_wf_id = _new_workflow_id()
    await handlers.handle_workflow_save(
        {
            "module_name": other_name,
            "workflow_data": {
                "id": other_wf_id,
                "name": "Other",
                "module_name": other_name,
                "nodes": [],
                "edges": [],
            },
        }
    )

    with pytest.raises(ValueError, match="Workflow not found for device"):
        await handlers.handle_workflow_set_current(
            {"device_id": device_id, "workflow_id": other_wf_id}
        )


@pytest.mark.asyncio
async def test_workflow_delete_clears_plugin_config_reference(handlers):
    name = _new_device_name()
    created = await handlers.handle_device_create(
        {"name": name, "simulator_index": 2, "port": 22002}
    )
    device_id = created["device"]["id"]

    wf_id = _new_workflow_id()
    await handlers.handle_workflow_save(
        {
            "module_name": name,
            "workflow_data": {
                "id": wf_id,
                "name": "Deletable",
                "module_name": name,
                "nodes": [],
                "edges": [],
            },
        }
    )
    await handlers.handle_workflow_set_current({"device_id": device_id, "workflow_id": wf_id})

    deleted = await handlers.handle_workflow_delete({"workflow_id": wf_id})
    assert deleted["deleted"] is True

    wf = Workflow.get(Workflow.workflow_id == wf_id)
    assert wf.is_active is False

    plugin_cfg = PluginConfig.get(PluginConfig.device == device_id)
    assert plugin_cfg.current_workflow_id is None
    assert plugin_cfg.workflow_enabled is False


@pytest.mark.asyncio
async def test_workflow_stop_returns_not_running_when_no_scheduler(handlers):
    result = await handlers.handle_workflow_stop({"module_name": "pytest-non-existent"})
    assert result["status"] == "not_running"


@pytest.mark.asyncio
async def test_workflow_start_and_stop_running(handlers, monkeypatch):
    name = _new_device_name()
    await handlers.handle_device_create({"name": name, "simulator_index": 5, "port": 23005})

    wf_id = _new_workflow_id()
    await handlers.handle_workflow_save(
        {
            "module_name": name,
            "workflow_data": {
                "id": wf_id,
                "name": "Stoppable",
                "module_name": name,
                "nodes": [],
                "edges": [],
            },
        }
    )

    # 让工作流持续运行一段时间，确保 stop 走到 cancel 分支
    from backend.core.scheduler import workflow_executor as workflow_executor_module

    async def _fake_execute(self):
        await asyncio.sleep(10)

    monkeypatch.setattr(workflow_executor_module.WorkflowExecutor, "execute", _fake_execute)

    start = await handlers.handle_workflow_start({"module_name": name, "workflow_id": wf_id})
    assert start["status"] == "started"
    assert start["mode"] == "workflow"

    stop = await handlers.handle_workflow_stop({"module_name": name})
    assert stop["status"] == "stopped"
