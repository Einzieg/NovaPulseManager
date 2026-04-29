from peewee import BooleanField, IntegerField, CharField
from backend.models.plugin_config_base import PluginConfigBase


class OrderTaskConfig(PluginConfigBase):
    order_switch = BooleanField(default=False)
    order_policy = CharField(default="使用超空间信标")
    order_hasten_policy = CharField(default="使用制造加速")
    order_speeduo_policy = CharField(default='["15_min"]')
    order_times = IntegerField(null=True)

    class Meta:
        table_name = 'order_task_config'
