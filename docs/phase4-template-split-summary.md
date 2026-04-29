# Phase 4 模板系统拆分（执行摘要）

**日期**: 2026-01-04  
**重构阶段**: Phase 4 - 模板系统拆分（插件化）  
**状态**: ✅ 已完成（插件专属模板进入插件目录；共享模板迁至 `backend/shared_templates/`）  

---

## 目标

- 将“任务专属模板”从旧的共享目录拆分到对应插件目录内，降低插件对全局资源目录的耦合。
- 将“共享模板”集中到 `backend/shared_templates/`，避免继续把模板资源与 `backend/static/` 的其它静态资源（如 platform-tools、ico、脚本）混在一起。
- 修复“源码运行 vs PyInstaller 打包”下资源路径不一致的问题。

---

## 关键改动

### 1) 新增统一路径解析（兼容层）

- `backend/core/paths.py`
  - `get_static_dir()`：定位 `static/`（PyInstaller: `sys._MEIPASS/static`；源码: `backend/static`）
  - `get_shared_templates_dir()`：定位 `shared_templates/`（PyInstaller: `sys._MEIPASS/shared_templates`；源码: `backend/shared_templates`）
  - `resolve_template_path(rel, plugin_dir=...)`：
    - 优先读取插件内 `templates/`
    - 其次读取 `backend/shared_templates/`

### 2) 统一模板加载路径（去硬编码）

- `backend/core/LoadTemplates.py`：全部改用 `resolve_template_path(...)`
- `backend/models/Template.py`：统一 `Path` + `cv2.imread(str(path))` 读取，并在加载失败时抛出明确异常，避免问题被延迟暴露。

### 3) 迁移模板资源

**插件专属模板**:
- `backend/static/novaimgs/order/` → `backend/plugins/order_task/templates/order/`
- `backend/static/novaimgs/talent/` → `backend/plugins/order_task/templates/talent/`
- `backend/static/novaimgs/hidden/` → `backend/plugins/radar_task/templates/hidden/`

**共享模板**:
- `backend/static/novaimgs/*` → `backend/shared_templates/*`（保留原有子目录结构与相对路径不变）

示例：`identify_in/in_menu.png`、`button/to_home.png` 等相对路径保持一致。

### 4) 打包资源补齐

- `main.spec`：补齐以下 datas（保证 PyInstaller 环境可用）
  - `backend/static` → `static`
  - `backend/plugins` → `backend/plugins`
  - `backend/shared_templates` → `shared_templates`

---

## 兼容性策略（KISS + 渐进式）

- 代码侧只依赖 `resolve_template_path()`，不再硬编码模板所在目录。
- 已移除对 `backend/static/novaimgs/` 的 legacy fallback；如需回滚请使用 Git revert 回到 Phase 4 之前提交。

---

## 后续建议

- 如需更细粒度的共享模板归类（如 `ui_common/identify/`），可在不改变相对路径语义的前提下进行一次性目录整理。
