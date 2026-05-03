from peewee import *
from datetime import datetime
from database.db_session import db


class Workflow(Model):
    """工作流模型 - 存储可视化工作流定义"""
    
    id = AutoField(primary_key=True)
    workflow_id = CharField(unique=True, index=True)
    name = CharField()
    description = TextField(null=True)
    module_name = CharField(index=True)  # 关联Module
    workflow_data = TextField()  # JSON格式: {nodes, edges}
    graph_json = TextField(null=True)  # schema v2 graph JSON
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db
        table_name = 'workflow'
        indexes = (
            (('module_name',), False),
            (('workflow_id',), True),
        )
