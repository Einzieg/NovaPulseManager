import importlib.util
import inspect
import logging
import os
import sys
from pathlib import Path

from peewee import SqliteDatabase

db_path = os.path.join(Path(__file__).resolve().parent.parent, 'database', 'nova_auto_script.db')
print(db_path)
if not os.path.exists(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = SqliteDatabase(db_path)

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


def init_database():
    db.connect(reuse_if_open=True)
    from backend.models import Config, Module, Plugin, Workflow, DeviceConfig, PluginConfig
    from backend.models.CommonConfig import CommonConfig

    # Legacy tables
    db.create_tables([Module], safe=True)
    db.create_tables([Config], safe=True)
    db.create_tables([Plugin], safe=True)
    db.create_tables([Workflow], safe=True)

    # Core tables
    db.create_tables([DeviceConfig, PluginConfig, CommonConfig], safe=True)

    # Plugin-specific tables (auto-discovered)
    plugin_models = _discover_plugin_models()
    if plugin_models:
        db.create_tables(plugin_models, safe=True)
        _logger.info(f"自动生成 {len(plugin_models)} 插件配置表")
