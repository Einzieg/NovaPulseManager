# Phase 1 重构完成总结

**日期**: 2026-01-02
**重构阶段**: Phase 1 - 数据库结构拆分
**状态**: ✅ 完成

---

## 📋 重构目标

将底层数据库 Module 模型改为设备库（DeviceConfig），只保留核心设备字段：
- `id`
- `name`
- `simulator_index`
- `port`

插件相关配置字段迁移到新的 PluginConfig 表。

---

## 🎯 完成的任务

### 1. 数据库 Schema 设计

#### DeviceConfig 模型 (`backend/models/DeviceConfig.py`)
```python
class DeviceConfig(Model):
    id = AutoField(primary_key=True)
    name = CharField(unique=True)
    simulator_index = IntegerField(default=0)
    port = IntegerField()
```

**关键改进**:
- 新增 `port` 字段：从 DeviceUtils 中的动态计算逻辑提取出来
- 提供 `calculate_port()` 方法：保留端口计算逻辑
- 提供 `create_with_auto_port()` 工厂方法：创建设备时自动计算端口

#### PluginConfig 模型 (`backend/models/PluginConfig.py`)
```python
class PluginConfig(Model):
    id = AutoField(primary_key=True)
    device = ForeignKeyField(DeviceConfig, backref='plugin_configs', on_delete='CASCADE')

    # 基础配置
    autostart_simulator, auto_relogin, relogin_time
    attack_fleet, task_type, stop_time

    # 常驻任务
    normal_monster, elite_monster, red_monster, wreckage

    # 其他任务
    hidden_switch, hidden_policy, hidden_times, hidden_wreckage
    order_switch, order_policy, order_hasten_policy
    order_speeduo_policy, order_times

    # 工作流
    current_workflow_id, workflow_enabled
```

**关键改进**:
- 通过外键关联 DeviceConfig
- 级联删除：删除设备时自动删除关联的插件配置
- 修正字段类型：将 BlobField 改为 BooleanField

### 2. 数据迁移脚本

创建了完整的数据迁移脚本 (`database/migrate_module_to_device_plugin.py`):

**功能**:
1. ✅ 备份原 Module 表数据到 JSON 文件
2. ✅ 创建新的 DeviceConfig 和 PluginConfig 表
3. ✅ 迁移数据（包括端口号计算）
4. ✅ 验证数据完整性
5. ✅ 可选：重命名旧表为 `module_deprecated`

**使用方法**:
```bash
# 迁移数据（保留旧表）
python database/migrate_module_to_device_plugin.py

# 迁移数据并重命名旧表
python database/migrate_module_to_device_plugin.py --delete-old-table
```

### 3. 代码更新

#### 更新的文件列表

| 文件 | 修改内容 |
|------|----------|
| `backend/models/__init__.py` | 导出 DeviceConfig 和 PluginConfig |
| `database/db_session.py` | 添加新表的创建逻辑 |
| `backend/core/TaskBase.py` | `self.module` → `self.device_config` + `self.plugin_config` |
| `backend/device_operation/DeviceUtils.py` | 使用 `device_config.port` 代替动态计算 |
| `backend/core/websocket/handlers.py` | `Module.select()` → `DeviceConfig.select()` |
| `backend/core/scheduler/task_scheduler.py` | `self.module` → `self.device_config` |

#### 关键代码变更

**TaskBase.py** (第37-40行):
```python
# 旧代码
self.module = Module.get(Module.name == target)

# 新代码
self.device_config = DeviceConfig.get(DeviceConfig.name == target)
self.plugin_config = PluginConfig.get(PluginConfig.device == self.device_config)
```

**DeviceUtils.py** (第55-62行):
```python
# 旧代码
self.module = Module.get_or_none(Module.name == name)
if self.module.simulator_index < 5555:
    self.port = 16384 + 32 * self.module.simulator_index
else:
    self.port = self.module.simulator_index

# 新代码
self.device_config = DeviceConfig.get_or_none(DeviceConfig.name == name)
self.port = self.device_config.port
```

**handlers.py** (第54-68行):
```python
# 旧代码
for module in Module.select():
    modules.append({
        "name": module.name,
        "simulator_index": module.simulator_index,
        ...
    })

# 新代码
for device in DeviceConfig.select():
    modules.append({
        "name": device.name,
        "simulator_index": device.simulator_index,
        "port": device.port,
        ...
    })
```

---

## 📊 重构影响范围

### 修改的文件统计
- ✅ 新增模型文件: 2 (`DeviceConfig.py`, `PluginConfig.py`)
- ✅ 新增迁移脚本: 1 (`migrate_module_to_device_plugin.py`)
- ✅ 修改现有文件: 6

### 代码依赖分析

通过 `grep` 查找，发现以下文件引用了 Module:
1. ✅ `backend/core/TaskBase.py` - 已更新
2. ✅ `backend/device_operation/DeviceUtils.py` - 已更新
3. ✅ `backend/core/websocket/handlers.py` - 已更新
4. ✅ `backend/core/scheduler/task_scheduler.py` - 已更新
5. ⚠️ `backend/test_mvp.py` - 测试文件，待更新

---

## ⚠️ 注意事项

### 1. 向后兼容性

- 保留了 Module 模型的导入（标记为 Legacy）
- 数据库中保留了 Module 表（迁移后可重命名）
- 迁移脚本提供完整的备份机制

### 2. 数据迁移建议

**迁移前**:
1. 完整备份数据库文件 `database/nova_auto_script.db`
2. 停止所有正在运行的任务
3. 关闭应用程序

**迁移步骤**:
```bash
# 1. 备份数据库
cp database/nova_auto_script.db database/nova_auto_script.db.backup

# 2. 运行迁移脚本
python database/migrate_module_to_device_plugin.py

# 3. 验证迁移结果
# 检查日志文件: database/migration_YYYYMMDD_HHMMSS.log
# 检查备份文件: database/module_backup_YYYYMMDD_HHMMSS.json

# 4. (可选) 重命名旧表
python database/migrate_module_to_device_plugin.py --delete-old-table
```

**回滚方案**:
如果迁移失败：
```bash
# 1. 停止应用程序
# 2. 恢复备份
cp database/nova_auto_script.db.backup database/nova_auto_script.db
# 3. 重启应用程序
```

### 3. 测试建议

在正式环境部署前，建议进行以下测试：

1. **数据迁移测试**
   - [ ] 运行迁移脚本
   - [ ] 验证数据完整性
   - [ ] 检查端口号计算是否正确

2. **功能测试**
   - [ ] 设备列表显示正常
   - [ ] 任务启动和停止正常
   - [ ] 设备配置读取正常
   - [ ] 插件配置读取正常

3. **兼容性测试**
   - [ ] 现有工作流正常运行
   - [ ] WebSocket 通信正常
   - [ ] 日志记录正常

---

## 🔍 Port 字段说明

**问题**: 用户要求保留 `port` 字段，但原 Module 模型中没有该字段

**解决方案**:
- 在 DeviceUtils.__init__ 中发现了端口计算逻辑（第59-63行）
- 将计算逻辑提取到 DeviceConfig 模型中
- 迁移时自动计算并保存 port 值

**端口计算规则**:
```python
if simulator_index < 5555:
    port = 16384 + 32 * simulator_index
else:
    port = simulator_index
```

---

## 🎉 重构收益

1. **清晰的数据模型**: 设备配置和插件配置分离
2. **更好的可维护性**: 每个表职责单一明确
3. **更好的扩展性**: 一个设备可以有多个插件配置（未来扩展）
4. **消除冗余计算**: port 字段直接存储，无需每次计算
5. **类型安全**: 修正了 BooleanField 的使用

---

## 📝 下一步计划

根据 `docs/refactor-executive-summary.md`:

### Phase 2: 目录结构重组与变量重命名 (Week 4-6)
- [ ] `backend/installed_plugins/` → `backend/plugins/`
- [ ] `backend/core/TaskBase.py` → `backend/core/legacy/TaskBase.py`
- [ ] 全局变量重命名:
  - `Module` → `DeviceConfig` (已完成)
  - `self.module` → `self.device_config` (已完成)
  - `OrderFinishes` → `TaskCompletedSuccess`

### Phase 3: FastAPI通信框架迁移 (Week 7-10)
- [ ] 设计 RESTful API 规范
- [ ] 实现 FastAPI 路由
- [ ] 实现 WebSocket 管理器
- [ ] 前端 API 客户端改造

---

## 📞 联系方式

如有问题或需要帮助，请查阅：
- 重构总体规划: `docs/refactor-executive-summary.md`
- 迁移日志: `database/migration_*.log`
- 数据备份: `database/module_backup_*.json`

---

**重构完成日期**: 2026-01-02
**预计下一阶段开始**: Week 4
