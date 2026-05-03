# NovaPulseManager 重构方案文档（Codex 执行版）

版本：v1.0  
目标读者：Codex / 后续维护者 / 项目作者  
适用仓库：`Einzieg/NovaPulseManager`  
核心目标：从“单层插件 + 设备绑定任务”重构为“多应用运行时 + 多层级模块 + 可编排 Action + 工作流 Run 模型”的架构。

---

## 0. 执行总则

本重构不建议一次性大爆炸式改完。Codex 必须按阶段执行，每个阶段都要做到：

1. 保持项目可运行。
2. 保留旧 API / 旧工作流 / 旧插件的兼容路径，直到明确进入 legacy cleanup 阶段。
3. 每个阶段必须新增或更新测试。
4. 不允许把业务逻辑继续塞进 `MessageHandlers`。
5. 不允许继续扩大 `PluginManager` 的职责。
6. 不允许让插件实例跨设备、跨运行复用。
7. 不允许在新代码中直接依赖旧的 `module_name` 作为设备主键。
8. 所有新工作流节点必须支持 `app_id / module_id / action_id / action_ref / node config`。
9. 新增接口应优先使用资源化 REST API；WebSocket 只负责实时事件推送。
10. 每阶段完成后输出：
    - 修改文件列表
    - 新增/修改测试列表
    - 本阶段兼容性说明
    - 当前仍保留的 legacy 入口
    - 后续阶段风险

---

## 1. 当前架构问题摘要

当前仓库已经完成过一轮重构，但处于“半收敛”状态。主要问题如下：

### 1.1 `MessageHandlers` 是上帝类

当前 `backend/core/websocket/handlers.py` 同时负责：

- HTTP / WebSocket handler 业务处理
- Device CRUD
- Workflow CRUD
- 插件配置读写
- 全局配置读写
- 调度器缓存
- 工作流启动停止
- 直接访问 Peewee model

这导致 API 层、应用服务层、领域层、数据库层混在一起。

### 1.2 Module / Device / CommonConfig / PluginConfig 概念不统一

当前已经引入 `DeviceConfig`、`CommonConfig`，但 legacy `Module`、legacy `PluginConfig` 仍在模型、测试和初始化逻辑中存在。  
这会导致“当前工作流到底存在 CommonConfig 还是 PluginConfig”这种契约不一致问题。

### 1.3 插件实例缓存存在跨设备污染风险

当前 `PluginManager.load_plugin(plugin_id, target)` 使用 `plugin_id` 作为实例缓存 key。  
同一个插件被不同设备运行时，可能复用同一个插件实例，导致设备配置、DeviceUtils、运行状态污染。

### 1.4 工作流节点配置没有真正参与执行

前端保存了 `nodes[].config`，但后端 `WorkflowExecutor` 执行时只读取 `plugin_id`，没有把节点配置注入插件。  
这会让“节点配置”在 UI 上存在，但执行时无效。

### 1.5 调度器缺少 Run 模型

当前 `TaskScheduler` 只有：

- `is_running`
- `current_task`
- `current_plugin`
- `last_result`

它无法表达：

- 运行 ID
- 历史运行记录
- 节点执行状态
- 取消中的状态
- 多设备并发保护
- 服务关闭时的任务 drain

### 1.6 插件体系不支持多游戏 / 多应用

当前插件是单层结构：

```text
backend/plugins/{plugin_id}/manifest.json
```

这无法自然表达：

```text
A 游戏
  ├─ 子模块 1
  ├─ 子模块 2

B 游戏
  ├─ 子模块 1
  ├─ 子模块 2
```

也无法自然表达：

```text
执行 A 游戏任务
  -> 切换到 B 游戏
  -> 执行 B 游戏任务
```

---

## 2. 目标架构总览

### 2.1 架构目标

目标是把系统从：

```text
设备 -> 插件 -> 执行
```

升级为：

```text
设备 -> 应用运行时 -> 模块 -> Action -> 工作流编排 -> Run 状态
```

新的核心概念：

| 概念 | 含义 |
|---|---|
| Device | 模拟器 / 手机 / ADB 目标设备 |
| Application / Game | 一个被自动化的游戏或应用，例如 A 游戏、B 游戏 |
| AppRuntime | 应用级运行时，负责启动、前台检测、登录检查、回首页、关闭弹窗 |
| Module | 应用下的功能域，例如 daily、combat、resource、account |
| Action | 工作流可执行的最小单元，例如 collect_reward、attack_monster |
| Workflow | Action 节点组成的 DAG |
| WorkflowRun | 一次工作流运行 |
| NodeRun | 工作流中某个节点的一次运行 |
| EventBus | 后端内部事件总线 |
| WebSocketHub | 订阅 EventBus 并向前端推送实时事件 |

---

## 3. 目标目录结构

### 3.1 后端目标结构

```text
backend/
  app/
    main.py
    settings.py
    lifespan.py

  api/
    routes/
      devices.py
      apps.py
      actions.py
      workflows.py
      runs.py
      settings.py
    websocket.py
    dependencies.py
    schemas/
      device.py
      app.py
      action.py
      workflow.py
      run.py
      settings.py

  application/
    services/
      device_service.py
      app_catalog_service.py
      workflow_service.py
      run_service.py
      settings_service.py
    dto/
    errors.py

  domain/
    device.py
    app.py
    action.py
    workflow.py
    run.py
    events.py
    config.py

  infrastructure/
    db/
      models.py
      repositories/
        device_repository.py
        workflow_repository.py
        config_repository.py
        run_repository.py
      migrations/
    device/
      gateway.py
      adb_gateway.py
      mumu_gateway.py
    plugins/
      catalog.py
      loader.py
      factory.py
      legacy_adapter.py
    realtime/
      event_bus.py
      websocket_hub.py
    logging/

  plugins/
    nova_iron_galaxy/
      manifest.json
      runtime.py
      config.py
      templates/
      modules/
        startup/
          manifest.json
          actions.py
          config.py
        combat/
          manifest.json
          actions.py
          config.py
          templates/
        collect/
          manifest.json
          actions.py
          config.py
          templates/
        order/
          manifest.json
          actions.py
          config.py
          templates/

    game_b/
      manifest.json
      runtime.py
      config.py
      templates/
      modules/
        daily/
          manifest.json
          actions.py
        resource/
          manifest.json
          actions.py

  legacy/
    task_base.py
    legacy_plugin_base.py
```

### 3.2 依赖方向

必须保持：

```text
api -> application -> domain
application -> domain + infrastructure interfaces
infrastructure -> concrete implementations
plugins -> action context / runtime context
```

禁止：

```text
domain -> api
domain -> FastAPI
domain -> WebSocket
domain -> Peewee model
application -> React frontend type
plugins -> global DB query
plugins -> global singleton scheduler
```

---

## 4. 多层级插件体系设计

### 4.1 新插件层级

插件不再代表“一个任务”，而是一个“应用扩展包”。

```text
Application / Game
  └─ Module
      └─ Action
```

示例：

```text
nova_iron_galaxy
  ├─ startup
  │   └─ ensure_login
  ├─ combat
  │   ├─ attack_normal_monster
  │   ├─ attack_elite_monster
  │   └─ attack_red_monster
  ├─ collect
  │   └─ collect_wreckage
  └─ order
      └─ execute_order

game_b
  ├─ account
  │   └─ ensure_login
  ├─ daily
  │   └─ sign_in
  └─ resource
      └─ collect
```

最终全局 Action 引用格式：

```text
{app_id}.{module_id}.{action_id}
```

示例：

```text
nova_iron_galaxy.combat.attack_elite_monster
nova_iron_galaxy.collect.collect_wreckage
game_b.daily.sign_in
game_b.resource.collect
```

---

## 5. Manifest 规范

### 5.1 应用级 manifest

路径：

```text
backend/plugins/{app_id}/manifest.json
```

示例：

```json
{
  "schema_version": 1,
  "kind": "application",
  "id": "nova_iron_galaxy",
  "name": "Nova: Iron Galaxy",
  "version": "1.0.0",
  "description": "Nova: Iron Galaxy automation support",
  "author": "Einzieg",
  "platform": "android",
  "package_name": "com.stone3.ig",
  "runtime": "runtime.py:NovaIronGalaxyRuntime",
  "config_model": "config.py:NovaIronGalaxyConfig",
  "modules": [
    "startup",
    "combat",
    "collect",
    "order"
  ]
}
```

### 5.2 模块级 manifest

路径：

```text
backend/plugins/{app_id}/modules/{module_id}/manifest.json
```

示例：

```json
{
  "schema_version": 1,
  "kind": "module",
  "id": "combat",
  "name": "战斗模块",
  "description": "刷怪、战斗、扫荡相关动作",
  "actions": [
    {
      "id": "attack_normal_monster",
      "name": "攻击普通怪",
      "description": "寻找并攻击普通怪",
      "entry_point": "actions.py:AttackNormalMonsterAction",
      "config_model": "config.py:AttackMonsterConfig"
    },
    {
      "id": "attack_elite_monster",
      "name": "攻击精英怪",
      "description": "寻找并攻击精英怪",
      "entry_point": "actions.py:AttackEliteMonsterAction",
      "config_model": "config.py:AttackMonsterConfig"
    }
  ]
}
```

---

## 6. 新基类设计

### 6.1 AppRuntimeBase

新增文件：

```text
backend/domain/app.py
```

接口：

```python
from abc import ABC, abstractmethod

class AppRuntimeBase(ABC):
    app_id: str
    name: str
    package_name: str | None = None

    async def launch(self, ctx):
        """启动应用。"""
        raise NotImplementedError

    async def ensure_foreground(self, ctx):
        """确保应用处于前台。"""
        raise NotImplementedError

    async def ensure_ready(self, ctx):
        """确保应用可执行 action。通常包含启动、登录检测、弹窗关闭、回首页。"""
        await self.launch(ctx)
        await self.ensure_foreground(ctx)

    async def on_enter(self, ctx):
        """从其他应用切换到本应用前后可执行的逻辑。"""
        pass

    async def on_leave(self, ctx):
        """离开本应用前可执行的逻辑。"""
        pass
```

### 6.2 ActionBase

新增文件：

```text
backend/domain/action.py
```

接口：

```python
from abc import ABC, abstractmethod

class ActionBase(ABC):
    action_ref: str

    def __init__(self, ctx):
        self.ctx = ctx

    async def prepare(self):
        pass

    @abstractmethod
    async def execute(self):
        raise NotImplementedError

    async def cleanup(self):
        pass
```

### 6.3 ActionExecutionContext

新增文件：

```text
backend/domain/action.py
```

```python
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class ActionExecutionContext:
    run_id: str
    workflow_id: str | None
    node_id: str | None

    device_id: int
    device_name: str
    device: Any

    app_id: str
    module_id: str
    action_id: str
    action_ref: str

    app_config: dict[str, Any]
    module_config: dict[str, Any]
    action_config: dict[str, Any]
    node_config: dict[str, Any]
    effective_config: dict[str, Any]

    event_bus: Any
    logger: Any
    cancellation_token: Any
```

配置合并优先级：

```text
GlobalConfig
  < DeviceConfig
  < DeviceAppConfig
  < DeviceModuleConfig
  < DeviceActionConfig
  < WorkflowNodeConfig
```

---

## 7. 插件 Catalog / Loader / Factory

### 7.1 Catalog 只负责发现和元数据

新增：

```text
backend/infrastructure/plugins/catalog.py
```

核心数据结构：

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class AppManifest:
    app_id: str
    name: str
    version: str
    runtime_entry: str
    package_name: str | None
    base_dir: Path

@dataclass(frozen=True)
class ModuleManifest:
    app_id: str
    module_id: str
    name: str
    description: str
    base_dir: Path

@dataclass(frozen=True)
class ActionManifest:
    app_id: str
    module_id: str
    action_id: str
    action_ref: str
    name: str
    description: str
    entry_point: str
    config_model: str | None
    base_dir: Path
```

接口：

```python
class PluginCatalog:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir

    def discover(self) -> None:
        ...

    def list_apps(self) -> list[AppManifest]:
        ...

    def list_modules(self, app_id: str) -> list[ModuleManifest]:
        ...

    def list_actions(
        self,
        app_id: str | None = None,
        module_id: str | None = None,
    ) -> list[ActionManifest]:
        ...

    def get_action(self, action_ref: str) -> ActionManifest:
        ...
```

### 7.2 Loader 只负责加载类

新增：

```text
backend/infrastructure/plugins/loader.py
```

要求：

- 支持从 app runtime entry 加载 `AppRuntimeBase`
- 支持从 action entry 加载 `ActionBase`
- 支持 config_model 加载
- 模块名必须包含 app_id/module_id/action_id，避免 `sys.modules` 冲突

模块名建议：

```text
nova_plugins.{app_id}.runtime
nova_plugins.{app_id}.modules.{module_id}.actions
```

### 7.3 Factory 每次执行都创建新实例

新增：

```text
backend/infrastructure/plugins/factory.py
```

```python
class ActionFactory:
    def __init__(self, catalog, loader):
        self.catalog = catalog
        self.loader = loader

    def create(self, action_ref: str, ctx) -> ActionBase:
        manifest = self.catalog.get_action(action_ref)
        action_cls = self.loader.load_action_class(manifest)
        return action_cls(ctx)
```

禁止缓存 Action 实例。

---

## 8. AppRuntimeManager：跨游戏执行核心

新增：

```text
backend/application/services/app_runtime_service.py
```

或：

```text
backend/infrastructure/plugins/runtime_manager.py
```

职责：

```text
1. 知道每个 app_id 对应哪个 AppRuntime。
2. 知道每个设备当前可能处于哪个 app。
3. 在执行节点前确保目标 app 已启动、在前台、可执行。
4. 当工作流从 A 游戏节点切换到 B 游戏节点时自动切换应用。
```

接口：

```python
class AppRuntimeManager:
    def __init__(self, catalog, loader):
        self.catalog = catalog
        self.loader = loader
        self._runtime_instances: dict[str, AppRuntimeBase] = {}
        self._current_app_by_device: dict[int, str] = {}

    async def ensure_app_ready(self, *, device_id: int, app_id: str, ctx):
        current_app = self._current_app_by_device.get(device_id)

        if current_app == app_id:
            runtime = self.get_runtime(app_id)
            await runtime.ensure_ready(ctx)
            return

        if current_app:
            old_runtime = self.get_runtime(current_app)
            await old_runtime.on_leave(ctx)

        new_runtime = self.get_runtime(app_id)
        await new_runtime.on_enter(ctx)
        await new_runtime.ensure_ready(ctx)

        self._current_app_by_device[device_id] = app_id
```

注意：Runtime 实例可以缓存，因为它应当无运行状态；Action 实例不允许缓存。

---

## 9. 工作流 Schema v2

### 9.1 节点结构

旧节点：

```json
{
  "id": "node-1",
  "plugin_id": "permanent_task",
  "position": { "x": 100, "y": 100 },
  "config": {}
}
```

新节点：

```json
{
  "id": "node-1",
  "type": "action",
  "app_id": "nova_iron_galaxy",
  "module_id": "combat",
  "action_id": "attack_elite_monster",
  "action_ref": "nova_iron_galaxy.combat.attack_elite_monster",
  "device_id": 1,
  "position": { "x": 100, "y": 100 },
  "config": {
    "retry_count": 3
  }
}
```

### 9.2 工作流结构

```json
{
  "schema_version": 2,
  "id": "workflow-cross-app-demo",
  "name": "A 游戏结束后执行 B 游戏",
  "description": "跨应用工作流示例",
  "nodes": [
    {
      "id": "a-login",
      "type": "action",
      "app_id": "game_a",
      "module_id": "account",
      "action_id": "ensure_login",
      "action_ref": "game_a.account.ensure_login",
      "device_id": 1,
      "position": { "x": 120, "y": 120 },
      "config": {}
    },
    {
      "id": "a-daily",
      "type": "action",
      "app_id": "game_a",
      "module_id": "daily",
      "action_id": "collect_reward",
      "action_ref": "game_a.daily.collect_reward",
      "device_id": 1,
      "position": { "x": 360, "y": 120 },
      "config": {}
    },
    {
      "id": "b-login",
      "type": "action",
      "app_id": "game_b",
      "module_id": "account",
      "action_id": "ensure_login",
      "action_ref": "game_b.account.ensure_login",
      "device_id": 1,
      "position": { "x": 600, "y": 120 },
      "config": {}
    },
    {
      "id": "b-resource",
      "type": "action",
      "app_id": "game_b",
      "module_id": "resource",
      "action_id": "collect",
      "action_ref": "game_b.resource.collect",
      "device_id": 1,
      "position": { "x": 840, "y": 120 },
      "config": {}
    }
  ],
  "edges": [
    { "id": "e1", "source": "a-login", "target": "a-daily" },
    { "id": "e2", "source": "a-daily", "target": "b-login" },
    { "id": "e3", "source": "b-login", "target": "b-resource" }
  ]
}
```

### 9.3 旧节点兼容映射

新增：

```text
backend/application/services/workflow_compat.py
```

```python
LEGACY_ACTION_REF_MAP = {
    "start_task": "nova_iron_galaxy.startup.launch",
    "permanent_task": "nova_iron_galaxy.permanent.run",
    "order_task": "nova_iron_galaxy.order.run",
    "radar_task": "nova_iron_galaxy.radar.run",
}
```

读取旧工作流时：

```python
def normalize_workflow_graph(graph: dict) -> dict:
    if graph.get("schema_version") == 2:
        return graph

    for node in graph.get("nodes", []):
        plugin_id = node.get("plugin_id")
        if plugin_id and "action_ref" not in node:
            action_ref = LEGACY_ACTION_REF_MAP.get(plugin_id)
            if action_ref:
                app_id, module_id, action_id = action_ref.split(".", 2)
                node["type"] = "action"
                node["app_id"] = app_id
                node["module_id"] = module_id
                node["action_id"] = action_id
                node["action_ref"] = action_ref

    graph["schema_version"] = 2
    return graph
```

---

## 10. 工作流执行器 v2

### 10.1 执行流程

`WorkflowExecutorV2` 负责：

1. 读取 workflow graph。
2. 校验 DAG。
3. 拓扑排序。
4. 对每个 action 节点：
   - 解析 `app_id / action_ref / device_id`
   - 获取 DeviceGateway
   - 调用 AppRuntimeManager.ensure_app_ready
   - 创建 ActionExecutionContext
   - ActionFactory.create
   - 执行 prepare / execute / cleanup
   - 发布 node status event
5. 记录 WorkflowRun / NodeRun 状态。

伪代码：

```python
class WorkflowExecutorV2:
    async def execute(self, workflow, run_id):
        graph = self.validate_and_build_graph(workflow.graph_json)

        for node_id in nx.topological_sort(graph):
            node = graph.nodes[node_id]

            if node["type"] != "action":
                await self.execute_system_node(node)
                continue

            await self.event_bus.publish(NodeStarted(...))

            try:
                ctx = await self.context_factory.create(
                    run_id=run_id,
                    workflow_id=workflow.id,
                    node=node,
                )

                await self.app_runtime_manager.ensure_app_ready(
                    device_id=ctx.device_id,
                    app_id=ctx.app_id,
                    ctx=ctx,
                )

                action = self.action_factory.create(ctx.action_ref, ctx)

                await action.prepare()
                await action.execute()
                await action.cleanup()

                await self.event_bus.publish(NodeSucceeded(...))

            except Exception as exc:
                await self.event_bus.publish(NodeFailed(...))
                raise
```

### 10.2 第一版不做并行

尽管 DAG 可以表达并行依赖，第一版仍然串行执行拓扑排序，确保行为稳定。  
后续可以扩展为按依赖层并发执行，但需要设备锁、应用切换锁、资源锁，不在本阶段做。

---

## 11. Run 模型

### 11.1 状态枚举

```python
RunStatus = Literal[
    "pending",
    "running",
    "cancelling",
    "succeeded",
    "failed",
    "cancelled"
]

NodeRunStatus = Literal[
    "pending",
    "running",
    "succeeded",
    "failed",
    "skipped",
    "cancelled"
]
```

### 11.2 RunService

新增：

```text
backend/application/services/run_service.py
```

职责：

```text
1. 启动 workflow run。
2. 根据 run_id 查询运行状态。
3. 取消 run。
4. 防止同一设备重复启动冲突任务。
5. 服务关闭时取消或等待正在运行的任务。
```

接口：

```python
class RunService:
    async def start_workflow(self, workflow_id: str, default_device_id: int | None = None) -> RunDTO:
        ...

    async def get_run(self, run_id: str) -> RunDTO:
        ...

    async def cancel_run(self, run_id: str) -> RunDTO:
        ...

    async def shutdown(self):
        ...
```

### 11.3 DeviceRunner

```python
class DeviceRunner:
    def __init__(self, device_id: int):
        self.device_id = device_id
        self.lock = asyncio.Lock()
        self.current_run_id: str | None = None

    async def run_exclusive(self, run_id: str, coro):
        async with self.lock:
            self.current_run_id = run_id
            try:
                return await coro
            finally:
                self.current_run_id = None
```

第一版可以限制同一设备同一时间只能运行一个 workflow run。

---

## 12. EventBus 和 WebSocketHub

### 12.1 EventBus

新增：

```text
backend/infrastructure/realtime/event_bus.py
```

```python
class EventBus:
    def __init__(self):
        self.queue = asyncio.Queue()

    async def publish(self, event):
        await self.queue.put(event)

    async def subscribe(self):
        while True:
            yield await self.queue.get()
```

### 12.2 事件类型

```python
@dataclass
class RunStatusChanged:
    event: str = "run.status_changed"
    run_id: str
    workflow_id: str
    status: str

@dataclass
class NodeStatusChanged:
    event: str = "workflow.node_status"
    run_id: str
    workflow_id: str
    node_id: str
    app_id: str
    module_id: str
    action_id: str
    status: str
    error: str | None = None

@dataclass
class LogEvent:
    event: str = "log"
    run_id: str | None
    device_id: int | None
    level: str
    message: str
    timestamp: float
```

### 12.3 WebSocketHub

新增：

```text
backend/infrastructure/realtime/websocket_hub.py
```

职责：

- 管理连接
- 从 EventBus 消费事件
- 广播给前端
- 支持断线清理
- 不在 logging handler 里直接 create_task

---

## 13. 数据模型建议

### 13.1 新模型

建议新增统一模型，不要继续扩大 legacy 表。

```text
Device
  id
  name
  simulator_index
  port
  created_at
  updated_at

DeviceCommonConfig
  id
  device_id
  auto_relogin
  relogin_time
  attack_fleet
  task_type
  stop_time

DeviceAppConfig
  id
  device_id
  app_id
  config_json

DeviceModuleConfig
  id
  device_id
  app_id
  module_id
  config_json

DeviceActionConfig
  id
  device_id
  app_id
  module_id
  action_id
  config_json

Workflow
  id
  workflow_id
  name
  description
  graph_json
  is_active
  created_at
  updated_at

WorkflowRun
  id
  run_id
  workflow_id
  status
  started_at
  finished_at
  error

WorkflowNodeRun
  id
  run_id
  node_id
  app_id
  module_id
  action_id
  action_ref
  device_id
  status
  started_at
  finished_at
  error
```

### 13.2 迁移策略

不要第一阶段删除旧表。

阶段策略：

1. 保留旧 `DeviceConfig` 表作为 Device source。
2. 新增 `Workflow.graph_json` 字段，旧 `workflow_data` 暂时保留。
3. 保存新工作流时写 `graph_json`。
4. 读取旧工作流时从 `workflow_data` 归一化为 v2。
5. 运行时优先使用 `graph_json`。
6. 后续 cleanup 阶段再删除 `module_name` 和 `workflow_data`。

---

## 14. API 设计

### 14.1 应用 / 模块 / Action

```http
GET /api/v1/apps
GET /api/v1/apps/{app_id}
GET /api/v1/apps/{app_id}/modules
GET /api/v1/apps/{app_id}/modules/{module_id}/actions
GET /api/v1/actions
GET /api/v1/actions/{action_ref}
GET /api/v1/actions/{action_ref}/config-schema
```

### 14.2 设备

```http
GET    /api/v1/devices
POST   /api/v1/devices
GET    /api/v1/devices/{device_id}
PATCH  /api/v1/devices/{device_id}
DELETE /api/v1/devices/{device_id}
```

### 14.3 工作流

```http
GET    /api/v1/workflows
POST   /api/v1/workflows
GET    /api/v1/workflows/{workflow_id}
PATCH  /api/v1/workflows/{workflow_id}
DELETE /api/v1/workflows/{workflow_id}
```

### 14.4 运行

```http
POST /api/v1/workflows/{workflow_id}/runs
GET  /api/v1/runs/{run_id}
POST /api/v1/runs/{run_id}/cancel
GET  /api/v1/runs
```

### 14.5 兼容旧 API

第一轮必须保留：

```http
GET  /api/v1/modules
GET  /api/v1/devices
POST /api/v1/workflows/start
POST /api/v1/workflows/stop
POST /api/v1/tasks/start
POST /api/v1/tasks/stop
```

但内部可以桥接到新服务。

---

## 15. 前端重构目标

### 15.1 拆分 websocketService

当前 `frontend/src/services/websocket.ts` 同时负责 REST、WebSocket、事件派发，应拆成：

```text
frontend/src/api/
  client.ts
  devices.ts
  apps.ts
  actions.ts
  workflows.ts
  runs.ts
  settings.ts

frontend/src/realtime/
  websocketClient.ts
  eventBus.ts

frontend/src/features/
  devices/
    useDevices.ts
    DeviceList.tsx
    DeviceEditModal.tsx
  workflows/
    useWorkflow.ts
    WorkflowEditor.tsx
    ActionPalette.tsx
    NodeConfigPanel.tsx
  runs/
    useRunStatus.ts
    RunLogPanel.tsx
```

### 15.2 工作流左侧栏改成 Action 树

UI 树结构：

```text
A 游戏
  ├─ 日常模块
  │   ├─ 领取奖励
  │   └─ 每日副本
  ├─ 战斗模块
  │   ├─ 普通怪
  │   └─ 精英怪

B 游戏
  ├─ 日常模块
  │   └─ 签到
  └─ 资源模块
      └─ 收菜
```

拖入画布后节点显示：

```text
[A游戏] 日常 / 领取奖励
[B游戏] 资源 / 收菜
```

### 15.3 节点配置面板

分为三块：

```text
Action 信息
  app_id
  module_id
  action_id
  action_ref

设备选择
  device_id

节点配置
  只对当前节点生效
```

第一版不要在节点面板直接修改设备全局配置，避免再次混淆。

---

## 16. 分阶段执行计划

## Phase 0：准备与安全修复

目标：保证后续重构有稳定基础。

### Codex 任务

1. 检查并修复 `pyproject.toml`：
   - 删除重复 `pydantic>=1.0.0`
   - 将 `pytest`、`pytest-asyncio`、`pyinstaller` 放入 dev optional dependencies
   - 若日志代码需要 structlog，则加入依赖或明确 fallback 策略

2. 修复 `main.spec`：
   - 当前入口应指向根目录 `main.py`
   - 确认 backend/static、backend/plugins、backend/shared_templates 打包路径正确

3. 修复测试数据库污染：
   - 测试不得使用固定开发数据库
   - 为测试引入临时 SQLite DB
   - 封装 `init_database(db_path=...)`

4. README 补最小开发说明：
   - 后端启动
   - 前端启动
   - 测试运行
   - 插件目录说明

### 验收标准

- `pytest` 可以运行且不污染开发数据库。
- `python main.py` 路径仍可用。
- README 包含最小可运行说明。
- 无功能行为变更。

---

## Phase 1：修复插件实例缓存问题

目标：消除跨设备复用插件实例的风险。

### Codex 任务

1. 修改当前 `backend/core/plugins/manager.py`：
   - `_loaded_plugins` 可以保留 class 缓存
   - `_plugin_instances` 不再按 `plugin_id` 缓存
   - `load_plugin(plugin_id, target)` 每次返回新实例
   - 或缓存 key 改为 `(plugin_id, target)` 作为临时过渡，但推荐每次新实例

2. 新增测试：
   - 同一个 plugin_id 在不同 target 下创建两个实例
   - 两个实例不能是同一个对象
   - 两个实例 target 不同

3. 保持旧调用签名不变。

### 验收标准

- `PluginManager.load_plugin("x", "device-a") is not PluginManager.load_plugin("x", "device-b")`
- 旧 `TaskScheduler` 仍可运行。
- 不改工作流 schema。

---

## Phase 2：抽离应用服务层

目标：把业务逻辑从 `MessageHandlers` 中迁出，暂不改 API 和前端。

### Codex 任务

新增：

```text
backend/application/services/device_service.py
backend/application/services/workflow_service.py
backend/application/services/plugin_config_service.py
backend/application/services/settings_service.py
backend/application/errors.py
```

要求：

- `MessageHandlers` 变成薄适配层。
- 设备 CRUD 迁入 `DeviceService`。
- 工作流 CRUD 迁入 `WorkflowService`。
- 插件配置读写迁入 `PluginConfigService`。
- 全局配置读写迁入 `SettingsService`。
- 定义业务错误：
  - `DeviceNotFound`
  - `WorkflowNotFound`
  - `DeviceAlreadyRunning`
  - `WorkflowValidationError`
  - `PluginNotFound`
  - `PluginConfigError`

### 验收标准

- 旧 API 行为不变。
- `MessageHandlers` 不再直接包含大量 Peewee 操作。
- 服务层单元测试覆盖核心 CRUD。
- `pytest` 通过。

---

## Phase 3：引入多层级插件 Catalog

目标：新增 App / Module / Action 元数据体系，但不立刻替换旧插件执行。

### Codex 任务

新增：

```text
backend/infrastructure/plugins/catalog.py
backend/infrastructure/plugins/loader.py
backend/infrastructure/plugins/factory.py
backend/domain/app.py
backend/domain/action.py
```

实现：

- `PluginCatalog.discover()`
- `list_apps()`
- `list_modules(app_id)`
- `list_actions(app_id=None, module_id=None)`
- `get_action(action_ref)`

创建当前旧插件的默认应用目录：

```text
backend/plugins/nova_iron_galaxy/
  manifest.json
  runtime.py
  modules/
    permanent/
      manifest.json
    order/
      manifest.json
    radar/
      manifest.json
    startup/
      manifest.json
```

暂时可以让这些 action 指向 legacy adapter。

### 验收标准

- `GET /api/v1/apps` 可返回 `nova_iron_galaxy`。
- `GET /api/v1/actions` 可返回 legacy action_ref。
- 不破坏旧 `/api/v1/plugins`。
- 新增 catalog 单元测试。

---

## Phase 4：引入 ActionBase 和 Legacy Adapter

目标：让旧插件可以通过新 Action 模型运行。

### Codex 任务

新增：

```text
backend/infrastructure/plugins/legacy_adapter.py
```

实现：

```python
class LegacyPluginActionAdapter(ActionBase):
    def __init__(self, ctx, legacy_plugin_cls):
        super().__init__(ctx)
        self.legacy_plugin = legacy_plugin_cls(ctx.device_name)

    async def prepare(self):
        await self.legacy_plugin.prepare()

    async def execute(self):
        await self.legacy_plugin.execute()

    async def cleanup(self):
        await self.legacy_plugin.cleanup()
```

注意：如果旧插件内部已经在 execute 外由调度器调用 prepare/cleanup，则 adapter 不能重复调用。Codex 应检查当前调用链后选择一种实现，避免 double prepare / double cleanup。

新增 legacy map：

```python
LEGACY_ACTION_REF_MAP = {
    "start_task": "nova_iron_galaxy.startup.launch",
    "permanent_task": "nova_iron_galaxy.permanent.run",
    "order_task": "nova_iron_galaxy.order.run",
    "radar_task": "nova_iron_galaxy.radar.run",
}
```

### 验收标准

- 新 ActionFactory 可以创建 legacy action。
- legacy action 每次执行创建新实例。
- 旧插件仍可通过旧工作流执行。
- 新 action_ref 可以被测试直接执行 mock action。

---

## Phase 5：工作流 Schema v2 和兼容读取

目标：工作流节点支持 app/module/action/action_ref/device_id/node config。

### Codex 任务

1. 修改 Pydantic schema：
   - 新增 `WorkflowNodeV2`
   - 新增 `WorkflowDataV2`
   - 保留旧 schema 兼容

2. 新增 `workflow_compat.py`：
   - 读取旧 `plugin_id`
   - 映射为新 `action_ref`
   - 自动补齐 `app_id/module_id/action_id`
   - 设置 `schema_version = 2`

3. 修改 `WorkflowService`：
   - 保存新工作流时使用 v2 schema
   - 读取旧工作流时自动 normalize
   - 不立即删除旧字段

4. 前端类型生成脚本同步更新。

### 验收标准

- 旧工作流可加载为 v2。
- 新工作流可保存、加载、再次保存。
- `nodes[].config` 保留并参与后续上下文构造。
- 生成的 TypeScript 类型更新。

---

## Phase 6：WorkflowExecutorV2 和 AppRuntimeManager

目标：支持 A 游戏节点执行后自动切换到 B 游戏节点。

### Codex 任务

新增：

```text
backend/application/services/app_runtime_manager.py
backend/core/scheduler/workflow_executor_v2.py
```

实现：

- `AppRuntimeManager.ensure_app_ready`
- `WorkflowExecutorV2`
- `ActionExecutionContextFactory`
- action 节点执行前根据 `app_id` 自动确保应用 ready
- 节点执行时传入 `node.config`

暂时保持串行拓扑执行。

### 验收标准

- 构造一个测试 workflow：
  - node1: `game_a.daily.mock_action`
  - node2: `game_b.daily.mock_action`
- 测试确认：
  - game_a runtime 被调用
  - game_b runtime 被调用
  - action 顺序正确
  - node config 传入 action context
- 旧工作流仍可运行。

---

## Phase 7：RunService、Run 状态和 WebSocket 事件

目标：从“启动返回 started”升级为“启动返回 run_id”。

### Codex 任务

新增：

```text
backend/application/services/run_service.py
backend/domain/run.py
backend/infrastructure/realtime/event_bus.py
backend/infrastructure/realtime/websocket_hub.py
```

实现：

- `RunService.start_workflow`
- `RunService.get_run`
- `RunService.cancel_run`
- `DeviceRunner` 同设备互斥
- EventBus 推送：
  - `run.status_changed`
  - `workflow.node_status`
  - `log`

兼容旧接口：

```http
POST /api/v1/workflows/start
```

可以内部调用 `RunService.start_workflow`，但返回中加入：

```json
{
  "status": "started",
  "run_id": "...",
  "workflow_id": "..."
}
```

### 验收标准

- 新 API `POST /api/v1/workflows/{workflow_id}/runs` 可返回 run_id。
- WebSocket 可以收到 run status 和 node status。
- 同设备重复启动返回 409 或业务错误。
- 旧前端不崩。

---

## Phase 8：资源化 API

目标：将新能力暴露为资源 API，旧 RPC API 继续兼容。

### Codex 任务

新增 routes：

```text
backend/api/routes/apps.py
backend/api/routes/actions.py
backend/api/routes/workflows.py
backend/api/routes/runs.py
backend/api/routes/devices.py
```

接口：

```http
GET    /api/v1/apps
GET    /api/v1/apps/{app_id}/modules
GET    /api/v1/actions
GET    /api/v1/actions/{action_ref}

GET    /api/v1/workflows
POST   /api/v1/workflows
GET    /api/v1/workflows/{workflow_id}
PATCH  /api/v1/workflows/{workflow_id}
DELETE /api/v1/workflows/{workflow_id}

POST   /api/v1/workflows/{workflow_id}/runs
GET    /api/v1/runs/{run_id}
POST   /api/v1/runs/{run_id}/cancel
```

要求：

- `backend/core/api/app.py` 不再内联所有 route。
- `create_app()` 只注册 routers 和 websocket endpoint。
- 错误处理集中化。

### 验收标准

- Swagger UI 能看到新接口。
- 旧接口仍存在。
- API 测试覆盖核心路径。

---

## Phase 9：前端工作流支持多应用 Action

目标：前端可选择 A 游戏 / B 游戏下的 Action，并保存 v2 workflow graph。

### Codex 任务

1. 拆分 API：
   - `api/client.ts`
   - `api/apps.ts`
   - `api/actions.ts`
   - `api/workflows.ts`
   - `api/runs.ts`

2. 改造工作流侧边栏：
   - 从 `GET /api/v1/apps` 和 `GET /api/v1/actions` 构建树
   - 支持按 app/module/action 展示

3. 改造节点数据：
   - 保存 `app_id/module_id/action_id/action_ref/device_id/config`
   - 不再只保存 `plugin_id`

4. 改造 NodeConfigPanel：
   - 显示 action metadata
   - 编辑 node config
   - 不直接写设备级插件配置

5. 运行按钮：
   - 调用新 run API
   - 根据 WebSocket run/node events 更新状态

### 验收标准

- 可以在画布中放置 A 游戏 Action 和 B 游戏 Action。
- 保存后后端 graph 为 schema v2。
- 启动后能收到节点状态。
- 旧设备页面基本可用。

---

## Phase 10：数据库模型收敛

目标：清理 Module / PluginConfig / module_name 等 legacy 混乱点。

### Codex 任务

谨慎执行。必须先有备份和迁移测试。

1. 新增迁移：
   - Workflow 增加 `graph_json`
   - 将旧 `workflow_data` 迁移为 v2 graph_json
   - 将 `module_name` 关联替换为节点级 `device_id` 或 workflow default device

2. 明确 CommonConfig 是设备通用配置：
   - 保留并改名为 DeviceCommonConfig，或至少从代码语义中改为 DeviceCommonConfig
   - 停止使用 legacy PluginConfig 存 current_workflow_id

3. 停止在 `init_database()` 中创建 legacy `Module` 和 legacy `PluginConfig`，除非 legacy migration 模式需要。

4. 增加 schema version 记录表。

### 验收标准

- 迁移前后工作流数量一致。
- 旧工作流可运行。
- 设备改名不需要再同步 workflow JSON 中的 module_name。
- 测试不再引用 legacy PluginConfig current_workflow_id。

---

## Phase 11：Legacy Cleanup

目标：删除或冻结旧实现。

只有在前面阶段稳定后执行。

### Codex 任务

- 删除或隔离 `backend/core/websocket/handlers.py` 中的业务逻辑。
- 删除旧 `PluginManager` 实例缓存逻辑。
- 删除手写前端 `types/workflow.ts`，统一从后端 schema 生成。
- 删除废弃 API，或标记 deprecated。
- 删除 legacy Module / PluginConfig 的业务引用。
- 将旧 `TaskBase` 限制在 legacy adapter 内部。

### 验收标准

- 全部测试通过。
- README / docs 更新完成。
- 新插件开发文档完成。
- 旧功能有迁移说明。

---

## 17. Codex 主提示词

将下面内容作为 Codex 的总提示词使用：

```text
你正在重构 NovaPulseManager。不要一次性完成全部阶段。请严格按 Phase 执行，每次只完成一个 Phase。

总体目标：
把当前单层 plugin 架构升级为多应用、多模块、多 Action 的工作流系统。新的工作流节点必须支持 app_id、module_id、action_id、action_ref、device_id、config。系统必须支持一个工作流中先执行 A 游戏 Action，再自动切换并执行 B 游戏 Action。

约束：
1. 不要破坏现有旧 API，除非当前 Phase 明确要求 cleanup。
2. 不要删除旧插件，必须通过 legacy adapter 兼容。
3. 不要让插件/Action 实例跨设备或跨运行复用。
4. 不要把新业务逻辑继续塞进 MessageHandlers。
5. 新代码必须有测试。
6. 测试不能污染开发数据库。
7. 每个 Phase 完成后运行 pytest，并说明未能运行的原因。
8. 如果需要前端改动，必须同步 TypeScript 类型。
9. 工作流第一版保持串行拓扑执行，不做并行。
10. 新架构中 WebSocket 只做实时事件推送，不再作为主要 RPC 通道。

当前执行 Phase：
[在这里填 Phase 编号和 Phase 内容]
```

---

## 18. 推荐首个 Codex 执行任务

建议先给 Codex 执行 Phase 1，而不是直接做多层级插件。

首个任务：

```text
执行 Phase 1：修复 PluginManager 插件实例缓存问题。

要求：
1. 修改 backend/core/plugins/manager.py。
2. load_plugin(plugin_id, target) 每次返回新的插件实例，不能按 plugin_id 复用实例。
3. class / manifest 元数据可以缓存。
4. 保持旧调用签名不变。
5. 新增单元测试，证明同一个 plugin_id 在不同 target 下不会返回同一个实例。
6. 运行 pytest。
7. 输出修改文件列表和测试结果。
```

原因：这是当前代码中最容易引发多设备、多应用污染的点，也是后续 ActionFactory 的前置修复。

---

## 19. 最终验收场景

完整重构后，必须能通过以下场景：

### 场景 1：旧插件兼容

```text
旧 workflow 使用 plugin_id = permanent_task
系统能自动映射到 nova_iron_galaxy.permanent.run
并正常执行。
```

### 场景 2：新多应用工作流

```text
创建 workflow：
  node1 = game_a.daily.collect_reward
  node2 = game_a.combat.attack_elite
  node3 = game_b.daily.sign_in
  node4 = game_b.resource.collect

执行 workflow：
  系统启动 / 确认 game_a ready
  执行 node1
  执行 node2
  切换 / 确认 game_b ready
  执行 node3
  执行 node4
```

### 场景 3：节点级配置生效

```text
同一个 action_ref 出现两次：
  node1 config = { monster_type: "normal" }
  node2 config = { monster_type: "elite" }

执行时两个 action 的 ctx.effective_config 不同。
```

### 场景 4：同设备互斥

```text
设备 1 正在运行 workflow_run_a
再次启动 workflow_run_b
系统返回冲突错误或排队策略
不能同时操作同一设备。
```

### 场景 5：WebSocket 实时状态

前端能收到：

```json
{
  "event": "run.status_changed",
  "data": {
    "run_id": "...",
    "status": "running"
  }
}
```

以及：

```json
{
  "event": "workflow.node_status",
  "data": {
    "run_id": "...",
    "node_id": "node-1",
    "app_id": "game_a",
    "module_id": "daily",
    "action_id": "collect_reward",
    "status": "succeeded"
  }
}
```

---

## 20. 文档交付清单

Codex 完成全部阶段后，仓库应包含：

```text
README.md
docs/architecture.md
docs/plugin-development.md
docs/workflow-schema-v2.md
docs/api.md
docs/migration-guide.md
docs/adr/
  0001-layered-architecture.md
  0002-app-module-action-plugin-model.md
  0003-workflow-run-model.md
  0004-eventbus-websocket-realtime.md
```

---

## 21. 关键设计结论

最终架构结论：

```text
Plugin 不再表示一个任务。
Plugin 表示一个应用扩展包。

Application / Game 表示一个被自动化的应用。
Module 表示应用内的功能分组。
Action 表示工作流可执行的最小单元。
Workflow Node 引用 Action。
AppRuntimeManager 负责跨应用切换。
RunService 负责运行生命周期。
EventBus + WebSocketHub 负责实时状态。
```

一句话：

> NovaPulseManager 应从“插件驱动的任务系统”升级为“应用运行时驱动的多 Action 工作流编排系统”。

