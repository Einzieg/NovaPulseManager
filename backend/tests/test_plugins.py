"""插件系统测试"""
import pytest
from pathlib import Path
from backend.core.plugins import PluginManager, PluginBase


def test_plugin_manager_init():
    """测试插件管理器初始化"""
    plugins_dir = Path("backend/plugins")
    manager = PluginManager(plugins_dir)
    assert manager.plugins_dir == plugins_dir
    assert len(manager._loaded_plugins) == 0


def test_discover_plugins_empty():
    """测试空插件目录"""
    plugins_dir = Path("backend/plugins")
    manager = PluginManager(plugins_dir)
    plugins = manager.discover_plugins()
    assert isinstance(plugins, list)