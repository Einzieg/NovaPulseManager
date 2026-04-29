from peewee import Model, ForeignKeyField, AutoField
from backend.models.DeviceConfig import DeviceConfig
from database.db_session import db


class PluginConfigBase(Model):
    id = AutoField()
    device = ForeignKeyField(DeviceConfig, on_delete='CASCADE', unique=True)

    class Meta:
        database = db
