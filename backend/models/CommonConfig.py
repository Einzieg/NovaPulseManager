from peewee import BooleanField, IntegerField, CharField
from backend.models.plugin_config_base import PluginConfigBase


class CommonConfig(PluginConfigBase):
    auto_relogin = BooleanField(default=False)
    relogin_time = IntegerField(null=True)
    attack_fleet = CharField(default='["all"]')
    task_type = CharField(default='["permanent"]')
    stop_time = CharField(null=True)
    current_workflow_id = CharField(null=True)
    workflow_enabled = BooleanField(default=False)

    class Meta:
        table_name = 'common_config'
