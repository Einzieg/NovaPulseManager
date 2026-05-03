import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path

from peewee import SqliteDatabase

DEFAULT_DB_PATH = Path(__file__).resolve().parent / 'nova_auto_script.db'

db = SqliteDatabase(str(DEFAULT_DB_PATH))

_logger = logging.getLogger(__name__)


def _discover_plugin_models() -> list:
    from backend.models.plugin_config_base import PluginConfigBase

    plugins_dir = Path(__file__).resolve().parent.parent / 'backend' / 'plugins'
    models = []

    if not plugins_dir.exists():
        return models

    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir():
            continue
        models_file = plugin_dir / 'models.py'
        if not models_file.exists():
            continue

        module_name = f"backend.plugins.{plugin_dir.name}.models"
        try:
            spec = importlib.util.spec_from_file_location(module_name, models_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, PluginConfigBase)
                        and obj is not PluginConfigBase
                        and obj.__module__ == module_name):
                    models.append(obj)
        except Exception as e:
            _logger.warning(f"未能从以下设备加载插件模型 {plugin_dir.name}: {e}")

    return models


def _ensure_column(table_name: str, column_name: str, column_sql: str) -> None:
    existing = {column.name for column in db.get_columns(table_name)}
    if column_name not in existing:
        db.execute_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")


def _migrate_workflow_graph_json() -> None:
    import json
    from datetime import datetime

    from backend.application.services.workflow_compat import normalize_workflow_graph
    from backend.models import SchemaVersion, Workflow

    migrated = 0
    for workflow in Workflow.select():
        if workflow.graph_json:
            continue

        try:
            graph = normalize_workflow_graph(json.loads(workflow.workflow_data))
        except Exception as e:
            _logger.warning(f"跳过工作流 graph_json 迁移 {workflow.workflow_id}: {e}")
            continue

        workflow.graph_json = json.dumps(graph, ensure_ascii=False)
        workflow.save()
        migrated += 1

    SchemaVersion.replace(
        name="workflow_graph",
        version=2,
        updated_at=datetime.now(),
    ).execute()

    if migrated:
        _logger.info(f"迁移 {migrated} 个工作流到 graph_json")


def init_database(
    db_path: str | os.PathLike[str] | None = None,
    *,
    include_legacy: bool = False,
):
    target_path = Path(db_path) if db_path is not None else DEFAULT_DB_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if db.database != str(target_path):
        if not db.is_closed():
            db.close()
        db.init(str(target_path))

    db.connect(reuse_if_open=True)
    from backend.models import Config, Plugin, Workflow, DeviceConfig, SchemaVersion
    from backend.models.CommonConfig import CommonConfig

    if include_legacy or os.getenv("NOVA_INIT_LEGACY_TABLES") == "1":
        from backend.models.Module import Module
        from backend.models.PluginConfig import PluginConfig

        db.create_tables([Module, PluginConfig], safe=True)

    db.create_tables([Config], safe=True)
    db.create_tables([Plugin], safe=True)
    db.create_tables([Workflow], safe=True)
    _ensure_column("workflow", "graph_json", "TEXT")

    # Core tables
    db.create_tables([DeviceConfig, CommonConfig, SchemaVersion], safe=True)

    # Plugin-specific tables (auto-discovered)
    plugin_models = _discover_plugin_models()
    if plugin_models:
        db.create_tables(plugin_models, safe=True)
        _logger.info(f"自动生成 {len(plugin_models)} 插件配置表")

    _migrate_workflow_graph_json()
