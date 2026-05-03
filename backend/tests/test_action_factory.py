from pathlib import Path
from types import SimpleNamespace
import shutil

from backend.core.scheduler.workflow_executor import WorkflowExecutor
from backend.infrastructure.plugins import ActionFactory, PluginCatalog, PluginClassLoader
from backend.infrastructure.plugins.legacy_adapter import LegacyPluginActionAdapter


async def test_action_factory_creates_fresh_legacy_adapter(monkeypatch):
    class DummyLegacyPlugin:
        def __init__(self, target):
            self.target = target
            self.events = []

        async def prepare(self):
            self.events.append("prepare")

        async def execute(self):
            self.events.append("execute")

        async def cleanup(self):
            self.events.append("cleanup")

    monkeypatch.setattr(
        "backend.infrastructure.plugins.factory.PluginLoader.load_plugin",
        staticmethod(lambda plugin_dir, manifest: DummyLegacyPlugin),
    )

    catalog = PluginCatalog(Path("backend/plugins"))
    catalog.discover()
    factory = ActionFactory(catalog, PluginClassLoader())
    ctx = SimpleNamespace(device_name="device-a")

    action_a = factory.create("nova_iron_galaxy.permanent.run", ctx)
    action_b = factory.create("nova_iron_galaxy.permanent.run", ctx)

    assert isinstance(action_a, LegacyPluginActionAdapter)
    assert action_a is not action_b
    assert action_a.legacy_plugin is not action_b.legacy_plugin
    assert action_a.legacy_plugin.target == "device-a"

    await action_a.prepare()
    await action_a.execute()
    await action_a.cleanup()
    assert action_a.legacy_plugin.events == ["prepare", "execute", "cleanup"]


async def test_action_factory_executes_mock_action(temp_db_path):
    plugins_dir = temp_db_path.parent / f"plugins_{temp_db_path.stem}"
    app_dir = plugins_dir / "mock_app"
    module_dir = app_dir / "modules" / "daily"
    module_dir.mkdir(parents=True)

    try:
        (app_dir / "manifest.json").write_text(
            """
{
  "schema_version": 1,
  "kind": "application",
  "id": "mock_app",
  "name": "Mock App",
  "version": "1.0.0",
  "runtime": "runtime.py:MockRuntime",
  "modules": ["daily"]
}
""".strip(),
            encoding="utf-8",
        )
        (app_dir / "runtime.py").write_text(
            """
from backend.domain.app import AppRuntimeBase

class MockRuntime(AppRuntimeBase):
    async def launch(self, ctx):
        pass

    async def ensure_foreground(self, ctx):
        pass
""".strip(),
            encoding="utf-8",
        )
        (module_dir / "manifest.json").write_text(
            """
{
  "schema_version": 1,
  "kind": "module",
  "id": "daily",
  "name": "Daily",
  "description": "Mock module",
  "actions": [
    {
      "id": "mock_action",
      "name": "Mock Action",
      "description": "Mock action",
      "entry_point": "actions.py:MockAction"
    }
  ]
}
""".strip(),
            encoding="utf-8",
        )
        (module_dir / "actions.py").write_text(
            """
from backend.domain.action import ActionBase

class MockAction(ActionBase):
    async def execute(self):
        self.ctx.events.append("mock")
""".strip(),
            encoding="utf-8",
        )

        catalog = PluginCatalog(plugins_dir)
        catalog.discover()
        factory = ActionFactory(catalog, PluginClassLoader())
        ctx = SimpleNamespace(events=[])

        action = factory.create("mock_app.daily.mock_action", ctx)
        await action.execute()

        assert ctx.events == ["mock"]
    finally:
        shutil.rmtree(plugins_dir, ignore_errors=True)


async def test_legacy_workflow_executor_still_uses_old_plugin_path():
    events = []

    class DummyPlugin:
        async def prepare(self):
            events.append("prepare")

        async def execute(self):
            events.append("execute")

        async def cleanup(self):
            events.append("cleanup")

    class DummyPluginManager:
        def load_plugin(self, plugin_id, target):
            events.append((plugin_id, target))
            return DummyPlugin()

    executor = WorkflowExecutor(
        workflow_data={
            "id": "legacy-workflow",
            "nodes": [{"id": "node-1", "plugin_id": "legacy-plugin"}],
            "edges": [],
        },
        plugin_manager=DummyPluginManager(),
        module_name="legacy-device",
    )

    await executor.execute()

    assert events == [
        ("legacy-plugin", "legacy-device"),
        "prepare",
        "execute",
        "cleanup",
    ]
