"""
One-time migration: split monolithic PluginConfig into per-plugin tables.

Usage:
    python -m database.migrate_plugin_config
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.db_session import db, init_database


def migrate():
    init_database()

    from backend.models.PluginConfig import PluginConfig
    from backend.models.CommonConfig import CommonConfig
    from backend.plugins.permanent_task.models import PermanentTaskConfig
    from backend.plugins.radar_task.models import RadarTaskConfig
    from backend.plugins.order_task.models import OrderTaskConfig
    from backend.plugins.start_task.models import StartTaskConfig

    migrated = 0
    for pc in PluginConfig.select():
        CommonConfig.get_or_create(
            device=pc.device,
            defaults={
                'auto_relogin': pc.auto_relogin,
                'relogin_time': pc.relogin_time,
                'attack_fleet': pc.attack_fleet,
                'task_type': pc.task_type,
                'stop_time': pc.stop_time,
                'current_workflow_id': pc.current_workflow_id,
                'workflow_enabled': pc.workflow_enabled,
            }
        )
        PermanentTaskConfig.get_or_create(
            device=pc.device,
            defaults={
                'normal_monster': pc.normal_monster,
                'elite_monster': pc.elite_monster,
                'red_monster': pc.red_monster,
                'wreckage': pc.wreckage,
            }
        )
        RadarTaskConfig.get_or_create(
            device=pc.device,
            defaults={
                'hidden_switch': pc.hidden_switch,
                'hidden_policy': pc.hidden_policy,
                'hidden_times': pc.hidden_times,
                'hidden_wreckage': pc.hidden_wreckage,
            }
        )
        OrderTaskConfig.get_or_create(
            device=pc.device,
            defaults={
                'order_switch': pc.order_switch,
                'order_policy': pc.order_policy,
                'order_hasten_policy': pc.order_hasten_policy,
                'order_speeduo_policy': pc.order_speeduo_policy,
                'order_times': pc.order_times,
            }
        )
        StartTaskConfig.get_or_create(
            device=pc.device,
            defaults={
                'autostart_simulator': pc.autostart_simulator,
            }
        )
        migrated += 1

    print(f"Migration complete: {migrated} records split into per-plugin tables.")


if __name__ == '__main__':
    migrate()
