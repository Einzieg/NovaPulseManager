# 数据库迁移指南

## Phase 1 重构：Module → DeviceConfig + PluginConfig

### 快速开始

```bash
# 1. 备份数据库
cp database/nova_auto_script.db database/nova_auto_script.db.backup

# 2. 运行迁移
python database/migrate_module_to_device_plugin.py

# 3. 查看迁移日志
cat database/migration_*.log
```

### 详细说明

请查看 `docs/phase1-refactor-summary.md` 了解：
- 重构目标和范围
- 数据库 Schema 变更
- 代码修改列表
- 测试建议
- 回滚方案

### 文件清单

- ✅ `backend/models/DeviceConfig.py` - 新的设备配置模型
- ✅ `backend/models/PluginConfig.py` - 新的插件配置模型
- ✅ `database/migrate_module_to_device_plugin.py` - 数据迁移脚本
- ✅ `docs/phase1-refactor-summary.md` - 详细文档
