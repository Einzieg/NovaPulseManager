# MVP最小可用系统 - 使用指南

## 📋 已完成的功能

### 后端
- ✅ TaskScheduler: 任务调度器,支持启动/停止插件
- ✅ FastAPI REST: modules/plugins/tasks/workflows 端点
- ✅ WebSocket推送: log / workflow.node_status
- ✅ 插件系统集成: permanent_task / order_task / radar_task / start_task

### 前端
- ✅ HTTP + WebSocket客户端: REST 调用 + 事件订阅
- ✅ DevicesPage: 设备列表页面,显示状态和控制按钮
- ✅ 实时状态更新: 每2秒自动刷新

## 🚀 启动步骤

### 1. 启动后端服务器

```bash
cd backend
python main.py
```

默认地址:
- API: `http://127.0.0.1:8765`
- Swagger UI: `http://127.0.0.1:8765/docs`
- WebSocket: `ws://127.0.0.1:8765/ws`

可选环境变量:
- `NOVA_FASTAPI_HOST` / `NOVA_FASTAPI_PORT` 用于覆盖 host/port

### 2. 启动前端应用

```bash
cd frontend
npm run dev
```

或者启动Electron应用:
```bash
npm start
```

如需覆盖后端地址（可选）:
- `VITE_FASTAPI_URL`（默认 `http://127.0.0.1:8765`）
- `VITE_FASTAPI_WS_URL`（默认 `ws://127.0.0.1:8765/ws`）

### 3. 测试功能

1. 打开前端应用,应该能看到设备列表
2. 点击绿色的Play按钮启动任务
3. 点击红色的Stop按钮停止任务

## 🔍 测试后端

运行测试脚本:
```bash
cd backend
python test_mvp.py
```

## 📝 API接口（FastAPI）

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

- 连接：`ws://127.0.0.1:8765/ws`
- 服务端推送:
  - `{"event":"log","data":{...}}`
  - `{"event":"workflow.node_status","data":{...}}`
