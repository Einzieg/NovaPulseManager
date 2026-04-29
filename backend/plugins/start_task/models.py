from peewee import BooleanField
from backend.models.plugin_config_base import PluginConfigBase


class StartTaskConfig(PluginConfigBase):
    autostart_simulator = BooleanField(default=False)

    class Meta:
        table_name = 'start_task_config'
