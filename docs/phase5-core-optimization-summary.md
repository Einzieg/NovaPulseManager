# Phase 5 核心系统优化（执行摘要）

**日期**: 2026-01-04  
**重构阶段**: Phase 5 - 核心系统优化  
**状态**: ✅ 已完成（渐进式）

---

## 目标

- **统一任务结果语义**：减少“异常做控制流/隐式约定”带来的维护成本。
- **统一日志格式**：日志输出结构化（JSON），便于检索与前端推送。
- **前后端类型同步**：以 Pydantic schemas 为单一来源，生成前端 TypeScript 类型。

---

## 关键改动

### 1) TaskResult：统一结果类型

- 新增 `backend/core/task_result.py`
  - `TaskStatus`: `success|failed|cancelled`
  - `TaskResult`: `status/message/data/error` + `to_dict()`

### 2) 调度器接入 TaskResult（消化异常）

- `backend/core/scheduler/task_scheduler.py`
  - `TaskScheduler.last_result`：记录最近一次插件/工作流执行结果
  - 后台 task 内部捕获并转换异常，避免出现 "Task exception was never retrieved"

- `backend/core/scheduler/workflow_executor.py`
  - `TaskCompleted` 视为节点正常完成
  - `TaskAbortedError` 视为节点失败并终止工作流

> 说明：插件内部仍保留 `TaskCompleted/TaskAbortedError`（legacy 兼容），但调度层统一转换为 `TaskResult`。

### 3) structlog：日志 JSON 化（兼容回退）

- 新增 `backend/core/logging/config.py`
  - `configure_logging()`：优先启用 structlog JSON 输出；未安装 structlog 时回退到 `logging.basicConfig`。
  - `get_json_formatter()`：供 `LogManager` 文件日志使用。

- `backend/main.py`：入口改为调用 `configure_logging()`。
- `backend/core/logging/log_manager.py`：文件日志 formatter 改为 JSON formatter（structlog 可选）。

### 4) 类型同步：Pydantic schemas + 生成前端 types

- 新增 `backend/core/api/schemas.py`：集中定义 API/WS 相关 Pydantic schemas。
- 新增 `scripts/generate_frontend_types.py`
  - 优先尝试 `pydantic2ts` CLI
  - 若不可用则使用内置 fallback generator
- 生成产物：`frontend/src/types/api.generated.ts`（前端开始引用）

---

## 依赖变更

- `pyproject.toml`：新增 `structlog`、`pydantic2ts`（需同步依赖后生效）。

---

## 验证建议

- 同步依赖后运行：
  - `python -m compileall backend -q`
  - `cd frontend && npm run build`
  - `python scripts/generate_frontend_types.py`（检查生成文件是否更新）
