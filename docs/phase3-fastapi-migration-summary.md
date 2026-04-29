# Phase 3 FastAPI 通信框架迁移（FastAPI-only）- 执行摘要

**日期**: 2026-01-04  
**重构阶段**: Phase 3 - FastAPI 通信框架迁移  
**状态**: ✅ 已完成（Socket.IO 已移除）

---

## 目标

- 移除旧的 Socket.IO 通信栈，统一使用 FastAPI（REST + WebSocket）。
- 前后端协议与端口统一，降低维护成本。

---

## 关键改动

### 1) 后端入口切换为 FastAPI-only

- `backend/main.py`
  - 仅启动 FastAPI（不再启动 Socket.IO）
  - 默认端口改为 `8765`（复用原 Socket.IO 端口，减少前端改动）
  - 环境变量：`NOVA_FASTAPI_HOST` / `NOVA_FASTAPI_PORT`

### 2) FastAPI 服务

- `backend/core/api/`
  - `app.py`：REST `/api/v1/*` + WebSocket `/ws`
  - `ws_manager.py`：WebSocket 连接管理与广播
  - `server.py`：uvicorn 启动器

### 3) 移除 Socket.IO 相关代码与依赖

- 删除：`backend/core/websocket/server.py`、`backend/core/websocket/broadcast_hub.py`
- `pyproject.toml`：移除 `python-socketio`、`aiohttp`

### 4) 前端改为仅使用 FastAPI

- `frontend/src/services/websocket.ts`
  - REST 使用 `fetch` 调用 `/api/v1/*`
  - WebSocket 订阅 `ws://127.0.0.1:8765/ws` 事件（log / workflow.node_status）
- `frontend/package.json`：移除 `socket.io-client`

---

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

### WebSocket（推送）

- `ws://127.0.0.1:8765/ws`
- `{"event":"log","data":{...}}`
- `{"event":"workflow.node_status","data":{...}}`

---

## 验收要点（建议）

- Swagger UI：`http://127.0.0.1:8765/docs`
- 前端能正常获取 modules/plugins，且能接收 log / workflow.node_status 推送
