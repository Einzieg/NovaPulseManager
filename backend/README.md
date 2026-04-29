# Nova Pulse Manager Backend

## 概述

Nova Pulse Manager 后端采用插件化架构，基于 Python 3.12 + asyncio 实现。

通信层已统一为 **FastAPI（REST + WebSocket）**，用于替代旧的 Socket.IO 实现。

- 默认地址：`http://127.0.0.1:8765`
- Swagger UI：`http://127.0.0.1:8765/docs`
- WebSocket：`ws://127.0.0.1:8765/ws`

## 核心组件

### 1) 插件系统（`backend/core/plugins/`）

- **PluginBase**：插件基类（继承 `TaskBase`，保持向后兼容）
- **PluginManager**：插件发现/加载/实例管理
- **PluginLoader**：解析 `manifest.json` 并动态加载插件

### 2) 通信层（`backend/core/api/`）

- REST：`/api/v1/*`
- WebSocket：`/ws`（用于日志/工作流节点状态推送）

### 3) 调度与工作流（`backend/core/scheduler/`）

- `TaskScheduler`：单设备任务/工作流调度
- `WorkflowExecutor`：基于 DAG 的插件编排执行

### 4) 数据库（`backend/models/`, `database/`）

- peewee + SQLite
- 关键模型：`DeviceConfig`、`PluginConfig`、`Workflow` 等

## 运行后端

从项目根目录：

```bash
python backend/main.py
```

可用环境变量：
- `NOVA_FASTAPI_HOST`：host（默认 `127.0.0.1`）
- `NOVA_FASTAPI_PORT`：port（默认 `8765`）

## API（FastAPI）

### REST

- `GET /api/v1/health`
- `GET /api/v1/modules`
- `GET /api/v1/plugins`
- `POST /api/v1/tasks/start`
- `POST /api/v1/tasks/stop`
- `POST /api/v1/workflows/save`
- `GET /api/v1/workflows/load?module_name=...`
- `POST /api/v1/workflows/start`

### WebSocket

- `ws://127.0.0.1:8765/ws`
- 推送：
  - `{"event":"log","data":{...}}`
  - `{"event":"workflow.node_status","data":{...}}`

## 前端对接

前端通过：
- HTTP 调用 `/api/v1/*`
- WebSocket 订阅 `/ws` 事件（日志/工作流节点状态）

可选环境变量（前端）：
- `VITE_FASTAPI_URL`（默认 `http://127.0.0.1:8765`）
- `VITE_FASTAPI_WS_URL`（默认 `ws://127.0.0.1:8765/ws`）
