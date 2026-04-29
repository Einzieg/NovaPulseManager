"""
DeviceConfig Model
设备配置模型 - 只保留设备核心信息
重构自 Module 模型（Phase 1: 数据库结构拆分）
"""
from peewee import *
from database.db_session import db


class DeviceConfig(Model):
    """
    设备配置表
    只保留设备核心字段：id, name, simulator_index, port
    插件配置已迁移到 PluginConfig 表
    """
    id: int = AutoField(primary_key=True)  # type: ignore[assignment]
    name: str = CharField(unique=True, help_text="设备名称，唯一标识符")  # type: ignore[assignment]
    simulator_index: int = IntegerField(default=0, help_text="模拟器索引号")  # type: ignore[assignment]
    port: int = IntegerField(help_text="设备端口号")  # type: ignore[assignment]

    class Meta:
        database = db
        table_name = 'device_config'

    def calculate_port(self) -> int:
        """
        根据 simulator_index 计算端口号
        迁移自 DeviceUtils.__init__ 中的端口计算逻辑
        """
        if self.simulator_index < 5555:
            return 16384 + 32 * self.simulator_index
        else:
            return self.simulator_index

    @classmethod
    def create_with_auto_port(cls, name: str, simulator_index: int, **kwargs):
        """
        创建设备配置，自动计算端口号
        """
        device = cls(name=name, simulator_index=simulator_index, **kwargs)
        device.port = device.calculate_port()
        device.save()
        return device

    def __str__(self):
        return f"DeviceConfig(id={self.id}, name={self.name}, port={self.port})"
