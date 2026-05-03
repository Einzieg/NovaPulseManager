from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.application.errors import DeviceNotFound, PluginConfigError, PluginNotFound
from backend.core.plugins import PluginManager
from backend.core.plugins.loader import PluginLoader
from backend.models import DeviceConfig


class PluginConfigService:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._config_model_cache: dict[str, type] = {}

    def _resolve_config_model(self, plugin_id: str):
        if plugin_id in self._config_model_cache:
            return self._config_model_cache[plugin_id]

        manager = PluginManager(self.plugins_dir)
        manager.discover_plugins()

        if plugin_id not in manager._plugin_dirs:
            raise PluginNotFound(f"Plugin not found: {plugin_id}")

        plugin_dir = manager._plugin_dirs[plugin_id]
        manifest = manager._plugin_metadata[plugin_id]
        plugin_class = PluginLoader.load_plugin(plugin_dir, manifest)

        if plugin_class.ConfigModel is None:
            raise PluginConfigError(f"Plugin {plugin_id} has no ConfigModel")

        self._config_model_cache[plugin_id] = plugin_class.ConfigModel
        return plugin_class.ConfigModel

    def get_plugin_config(self, payload: dict[str, Any]) -> dict[str, Any]:
        device_name = payload.get("device_name")
        plugin_id = payload.get("plugin_id")
        if not device_name or not plugin_id:
            raise ValueError("Missing device_name or plugin_id")

        device = DeviceConfig.get_or_none(DeviceConfig.name == device_name)
        if not device:
            raise DeviceNotFound(f"Device not found: {device_name}")

        ConfigModel = self._resolve_config_model(plugin_id)
        instance, _ = ConfigModel.get_or_create(device=device)

        fields = []
        for name, field in ConfigModel._meta.fields.items():
            if name in ("id", "device"):
                continue
            default = field.default
            if callable(default):
                default = None
            fields.append(
                {
                    "name": name,
                    "type": type(field).__name__,
                    "value": getattr(instance, name),
                    "default": default,
                }
            )

        return {"fields": fields}

    def update_plugin_config(self, payload: dict[str, Any]) -> dict[str, bool]:
        device_name = payload.get("device_name")
        plugin_id = payload.get("plugin_id")
        config = payload.get("config")
        if not device_name or not plugin_id or config is None:
            raise ValueError("Missing device_name, plugin_id or config")

        device = DeviceConfig.get_or_none(DeviceConfig.name == device_name)
        if not device:
            raise DeviceNotFound(f"Device not found: {device_name}")

        ConfigModel = self._resolve_config_model(plugin_id)
        instance, _ = ConfigModel.get_or_create(device=device)

        valid_fields = {
            name for name in ConfigModel._meta.fields if name not in ("id", "device")
        }
        for key, value in config.items():
            if key in valid_fields:
                setattr(instance, key, value)

        instance.save()
        return {"updated": True}
