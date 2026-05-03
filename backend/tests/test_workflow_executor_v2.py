from types import SimpleNamespace

from backend.application.services.app_runtime_manager import AppRuntimeManager
from backend.core.scheduler.workflow_executor_v2 import WorkflowExecutorV2


async def test_app_runtime_manager_switches_between_apps():
    calls = []

    class FakeCatalog:
        def get_app(self, app_id):
            return SimpleNamespace(app_id=app_id)

    class FakeLoader:
        def load_runtime_class(self, manifest):
            app_id = manifest.app_id

            class Runtime:
                async def on_enter(self, ctx):
                    calls.append((app_id, "enter"))

                async def on_leave(self, ctx):
                    calls.append((app_id, "leave"))

                async def ensure_ready(self, ctx):
                    calls.append((app_id, "ready"))

            return Runtime

    manager = AppRuntimeManager(FakeCatalog(), FakeLoader())

    await manager.ensure_app_ready(device_id=1, app_id="game_a", ctx=object())
    await manager.ensure_app_ready(device_id=1, app_id="game_a", ctx=object())
    await manager.ensure_app_ready(device_id=1, app_id="game_b", ctx=object())

    assert calls == [
        ("game_a", "enter"),
        ("game_a", "ready"),
        ("game_a", "ready"),
        ("game_a", "leave"),
        ("game_b", "enter"),
        ("game_b", "ready"),
    ]


async def test_workflow_executor_v2_runs_cross_app_actions_in_order():
    ready_calls = []
    action_calls = []

    class FakeRuntimeManager:
        async def ensure_app_ready(self, *, device_id, app_id, ctx):
            ready_calls.append((device_id, app_id, ctx.node_config))

    class FakeContextFactory:
        async def create(self, *, run_id, workflow_id, node):
            return SimpleNamespace(
                run_id=run_id,
                workflow_id=workflow_id,
                node_id=node["id"],
                device_id=node["device_id"],
                app_id=node["app_id"],
                module_id=node["module_id"],
                action_id=node["action_id"],
                action_ref=node["action_ref"],
                node_config=dict(node.get("config") or {}),
            )

    class FakeActionFactory:
        def create(self, action_ref, ctx):
            class Action:
                async def prepare(self):
                    action_calls.append(("prepare", action_ref))

                async def execute(self):
                    action_calls.append(("execute", action_ref, ctx.node_config))

                async def cleanup(self):
                    action_calls.append(("cleanup", action_ref))

            return Action()

    workflow_data = {
        "schema_version": 2,
        "id": "cross-app",
        "nodes": [
            {
                "id": "a-daily",
                "type": "action",
                "app_id": "game_a",
                "module_id": "daily",
                "action_id": "mock_action",
                "action_ref": "game_a.daily.mock_action",
                "device_id": 1,
                "position": {"x": 0, "y": 0},
                "config": {"step": "a"},
            },
            {
                "id": "b-daily",
                "type": "action",
                "app_id": "game_b",
                "module_id": "daily",
                "action_id": "mock_action",
                "action_ref": "game_b.daily.mock_action",
                "device_id": 1,
                "position": {"x": 100, "y": 0},
                "config": {"step": "b"},
            },
        ],
        "edges": [{"id": "edge-1", "source": "a-daily", "target": "b-daily"}],
    }

    executor = WorkflowExecutorV2(
        workflow_data=workflow_data,
        run_id="run-1",
        app_runtime_manager=FakeRuntimeManager(),
        action_factory=FakeActionFactory(),
        context_factory=FakeContextFactory(),
    )

    await executor.execute()

    assert ready_calls == [
        (1, "game_a", {"step": "a"}),
        (1, "game_b", {"step": "b"}),
    ]
    assert action_calls == [
        ("prepare", "game_a.daily.mock_action"),
        ("execute", "game_a.daily.mock_action", {"step": "a"}),
        ("cleanup", "game_a.daily.mock_action"),
        ("prepare", "game_b.daily.mock_action"),
        ("execute", "game_b.daily.mock_action", {"step": "b"}),
        ("cleanup", "game_b.daily.mock_action"),
    ]
