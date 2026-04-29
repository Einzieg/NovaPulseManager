"""
数据迁移脚本: Module -> DeviceConfig + PluginConfig
Phase 1: 数据库结构拆分

功能:
1. 备份原 Module 表数据
2. 创建新的 DeviceConfig 和 PluginConfig 表
3. 迁移数据到新表
4. 验证数据完整性
5. (可选) 删除旧的 Module 表

使用方法:
    python migrate_module_to_device_plugin.py [--delete-old-table]

参数:
    --delete-old-table: 迁移成功后删除旧的 Module 表（谨慎使用）
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from peewee import *

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from database.db_session import db
from backend.models.Module import Module
from backend.models.DeviceConfig import DeviceConfig
from backend.models.PluginConfig import PluginConfig


class MigrationLogger:
    """迁移日志记录器"""
    def __init__(self):
        self.log_file = Path(__file__).parent / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')


def backup_module_table(logger: MigrationLogger):
    """备份 Module 表到 JSON 文件"""
    logger.log("开始备份 Module 表...")

    backup_file = Path(__file__).parent / f"module_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    modules_data = []
    for module in Module.select():
        module_dict = {
            'id': module.id,
            'name': module.name,
            'simulator_index': module.simulator_index,
            'autostart_simulator': bool(module.autostart_simulator),
            'auto_relogin': bool(module.auto_relogin),
            'relogin_time': module.relogin_time,
            'attack_fleet': module.attack_fleet,
            'task_type': module.task_type,
            'stop_time': module.stop_time,
            'normal_monster': bool(module.normal_monster),
            'elite_monster': bool(module.elite_monster),
            'red_monster': bool(module.red_monster),
            'wreckage': bool(module.wreckage),
            'hidden_switch': bool(module.hidden_switch),
            'hidden_policy': module.hidden_policy,
            'hidden_times': module.hidden_times,
            'hidden_wreckage': bool(module.hidden_wreckage),
            'order_switch': bool(module.order_switch),
            'order_policy': module.order_policy,
            'order_hasten_policy': module.order_hasten_policy,
            'order_speeduo_policy': module.order_speeduo_policy,
            'order_times': module.order_times,
            'current_workflow_id': module.current_workflow_id,
            'workflow_enabled': bool(module.workflow_enabled),
        }
        modules_data.append(module_dict)

    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(modules_data, f, ensure_ascii=False, indent=2)

    logger.log(f"备份完成，共备份 {len(modules_data)} 条记录")
    logger.log(f"备份文件: {backup_file}")
    return backup_file, modules_data


def create_new_tables(logger: MigrationLogger):
    """创建新表"""
    logger.log("创建新表: DeviceConfig, PluginConfig...")

    db.create_tables([DeviceConfig, PluginConfig], safe=True)

    logger.log("新表创建完成")


def migrate_data(logger: MigrationLogger, modules_data: list):
    """迁移数据"""
    logger.log("开始迁移数据...")

    migrated_count = 0
    failed_count = 0

    for module_data in modules_data:
        try:
            # 计算端口号
            simulator_index = module_data['simulator_index']
            if simulator_index < 5555:
                port = 16384 + 32 * simulator_index
            else:
                port = simulator_index

            # 创建 DeviceConfig
            device = DeviceConfig.create(
                name=module_data['name'],
                simulator_index=simulator_index,
                port=port
            )
            logger.log(f"  创建设备配置: {device.name} (port={port})")

            # 创建 PluginConfig
            plugin_config = PluginConfig.create(
                device=device,
                autostart_simulator=module_data['autostart_simulator'],
                auto_relogin=module_data['auto_relogin'],
                relogin_time=module_data['relogin_time'],
                attack_fleet=module_data['attack_fleet'],
                task_type=module_data['task_type'],
                stop_time=module_data['stop_time'],
                normal_monster=module_data['normal_monster'],
                elite_monster=module_data['elite_monster'],
                red_monster=module_data['red_monster'],
                wreckage=module_data['wreckage'],
                hidden_switch=module_data['hidden_switch'],
                hidden_policy=module_data['hidden_policy'],
                hidden_times=module_data['hidden_times'],
                hidden_wreckage=module_data['hidden_wreckage'],
                order_switch=module_data['order_switch'],
                order_policy=module_data['order_policy'],
                order_hasten_policy=module_data['order_hasten_policy'],
                order_speeduo_policy=module_data['order_speeduo_policy'],
                order_times=module_data['order_times'],
                current_workflow_id=module_data['current_workflow_id'],
                workflow_enabled=module_data['workflow_enabled'],
            )
            logger.log(f"  创建插件配置: {plugin_config.id}")

            migrated_count += 1

        except Exception as e:
            logger.log(f"  迁移失败: {module_data['name']} - {str(e)}", "ERROR")
            failed_count += 1

    logger.log(f"数据迁移完成: 成功 {migrated_count} 条, 失败 {failed_count} 条")
    return migrated_count, failed_count


def verify_migration(logger: MigrationLogger, original_count: int):
    """验证迁移结果"""
    logger.log("开始验证迁移结果...")

    device_count = DeviceConfig.select().count()
    plugin_count = PluginConfig.select().count()

    logger.log(f"原 Module 记录数: {original_count}")
    logger.log(f"新 DeviceConfig 记录数: {device_count}")
    logger.log(f"新 PluginConfig 记录数: {plugin_count}")

    if device_count == original_count and plugin_count == original_count:
        logger.log("✓ 数据验证通过：记录数量一致", "SUCCESS")
        return True
    else:
        logger.log("✗ 数据验证失败：记录数量不一致", "ERROR")
        return False


def delete_old_table(logger: MigrationLogger):
    """删除旧的 Module 表"""
    logger.log("删除旧的 Module 表...", "WARNING")

    # 重命名而不是删除，以防万一
    try:
        db.execute_sql('ALTER TABLE module RENAME TO module_deprecated;')
        logger.log("Module 表已重命名为 module_deprecated", "SUCCESS")
    except Exception as e:
        logger.log(f"重命名失败: {str(e)}", "ERROR")


def main():
    parser = argparse.ArgumentParser(description='迁移 Module 表到 DeviceConfig + PluginConfig')
    parser.add_argument('--delete-old-table', action='store_true',
                       help='迁移成功后删除旧的 Module 表')
    args = parser.parse_args()

    logger = MigrationLogger()

    logger.log("=" * 60)
    logger.log("开始执行数据库迁移: Module -> DeviceConfig + PluginConfig")
    logger.log("=" * 60)

    try:
        # 1. 备份数据
        backup_file, modules_data = backup_module_table(logger)

        # 2. 创建新表
        create_new_tables(logger)

        # 3. 迁移数据
        migrated_count, failed_count = migrate_data(logger, modules_data)

        # 4. 验证迁移
        if verify_migration(logger, len(modules_data)):
            logger.log("=" * 60)
            logger.log("迁移成功完成！", "SUCCESS")
            logger.log("=" * 60)

            # 5. 可选：删除旧表
            if args.delete_old_table:
                delete_old_table(logger)
        else:
            logger.log("=" * 60)
            logger.log("迁移验证失败，请检查日志", "ERROR")
            logger.log("=" * 60)
            sys.exit(1)

    except Exception as e:
        logger.log(f"迁移过程中发生错误: {str(e)}", "ERROR")
        import traceback
        logger.log(traceback.format_exc(), "ERROR")
        sys.exit(1)

    logger.log(f"日志文件: {logger.log_file}")


if __name__ == '__main__':
    main()
