"""
PluginConfig Model
插件配置模型 - 存储所有插件相关的配置
重构自 Module 模型（Phase 1: 数据库结构拆分）
"""
from peewee import *
from database.db_session import db
from backend.models.DeviceConfig import DeviceConfig


class PluginConfig(Model):
    """
    插件配置表
    存储所有从 Module 模型迁移过来的插件配置字段
    通过 device 外键关联到 DeviceConfig
    """
    id = AutoField(primary_key=True)
    device = ForeignKeyField(DeviceConfig, backref='plugin_configs', on_delete='CASCADE',
                             help_text="关联的设备配置")

    # 基础配置 ---------------------------------------------
    autostart_simulator = BooleanField(default=False, help_text="启动时自动启动模拟器")
    auto_relogin = BooleanField(default=False, help_text="自动抢登")
    relogin_time = IntegerField(null=True, help_text="抢登等待时间（秒）")
    attack_fleet = CharField(default='["all"]', help_text="攻击舰队列表（JSON格式）")
    task_type = CharField(default='["permanent"]', help_text="任务类型（JSON格式）")
    stop_time = CharField(null=True, help_text="停止时间")

    # 常驻任务 ---------------------------------------------
    normal_monster = BooleanField(default=False, help_text="普通清道夫")
    elite_monster = BooleanField(default=True, help_text="精英清道夫")
    red_monster = BooleanField(default=False, help_text="深红入侵")
    wreckage = BooleanField(default=True, help_text="采集残骸")

    # 其他任务 ---------------------------------------------
    hidden_switch = BooleanField(default=False, help_text="隐秘开关")
    hidden_policy = CharField(default="不使用能量道具",
                              help_text="隐秘策略（不使用能量道具/使用能量道具/使用GEC购买能量）")
    hidden_times = IntegerField(null=True, help_text="隐秘次数")
    hidden_wreckage = BooleanField(default=False, help_text="采集残骸")

    order_switch = BooleanField(default=False, help_text="订单开关")
    order_policy = CharField(default="使用超空间信标",
                            help_text="订单策略（使用超空间信标/不使用超空间信标/使用GEC购买信标）")
    order_hasten_policy = CharField(default="使用制造加速",
                                   help_text="加速策略（使用订单电路板/使用制造加速）")
    order_speeduo_policy = CharField(default='["15_min"]',
                                    help_text="加速使用策略（15_min/1_hour/3_hour, JSON格式）")
    order_times = IntegerField(null=True, help_text="订单次数")

    # 工作流相关 ---------------------------------------------
    current_workflow_id = CharField(null=True, help_text="当前激活的工作流ID")
    workflow_enabled = BooleanField(default=False, help_text="是否启用工作流模式")

    class Meta:
        database = db
        table_name = 'plugin_config'

    def __str__(self):
        return f"PluginConfig(id={self.id}, device={self.device.name})"
