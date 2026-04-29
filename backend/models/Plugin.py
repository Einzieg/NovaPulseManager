from peewee import *
from datetime import datetime
from database.db_session import db


class Plugin(Model):
    id = AutoField(primary_key=True)
    plugin_id = CharField(unique=True)
    name = CharField()
    version = CharField()
    enabled = BooleanField(default=True)
    config = TextField(null=True)
    manifest = TextField(null=True)
    installed_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db