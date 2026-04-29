from peewee import BooleanField
from backend.models.plugin_config_base import PluginConfigBase


class PermanentTaskConfig(PluginConfigBase):
    normal_monster = BooleanField(default=False)
    elite_monster = BooleanField(default=True)
    red_monster = BooleanField(default=False)
    wreckage = BooleanField(default=True)

    class Meta:
        table_name = 'permanent_task_config'
