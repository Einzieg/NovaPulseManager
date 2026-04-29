from peewee import BooleanField, IntegerField, CharField
from backend.models.plugin_config_base import PluginConfigBase


class RadarTaskConfig(PluginConfigBase):
    hidden_switch = BooleanField(default=False)
    hidden_policy = CharField(default="不使用能量道具")
    hidden_times = IntegerField(null=True)
    hidden_wreckage = BooleanField(default=False)

    class Meta:
        table_name = 'radar_task_config'
