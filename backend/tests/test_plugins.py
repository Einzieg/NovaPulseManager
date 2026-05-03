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


def test_load_plugin_returns_new_instance_for_each_target(monkeypatch):
    """同一插件在不同设备目标下不能复用同一个实例"""

    class DummyPlugin:
        def __init__(self, target):
            self.target = target

    load_calls = []

    def fake_load_plugin(plugin_dir, manifest):
        load_calls.append((plugin_dir, manifest["id"]))
        return DummyPlugin

    monkeypatch.setattr(
        "backend.core.plugins.manager.PluginLoader.load_plugin",
        staticmethod(fake_load_plugin),
    )

    plugins_dir = Path("backend/plugins")
    manager = PluginManager(plugins_dir)
    manager._plugin_metadata["dummy"] = {
        "id": "dummy",
        "name": "Dummy Plugin",
        "version": "1.0.0",
    }
    manager._plugin_dirs["dummy"] = plugins_dir / "dummy"

    device_a = manager.load_plugin("dummy", "device-a")
    device_b = manager.load_plugin("dummy", "device-b")
    device_a_again = manager.load_plugin("dummy", "device-a")

    assert device_a is not device_b
    assert device_a is not device_a_again
    assert device_a.target == "device-a"
    assert device_b.target == "device-b"
    assert device_a_again.target == "device-a"
    assert manager.get_plugin("dummy") is None
    assert len(load_calls) == 1
