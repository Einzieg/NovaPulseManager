from peewee import CharField, DateTimeField, IntegerField, Model
from datetime import datetime

from database.db_session import db


class SchemaVersion(Model):
    name = CharField(primary_key=True)
    version = IntegerField()
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = "schema_version"
