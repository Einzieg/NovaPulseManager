from __future__ import annotations

from backend.domain.action import ActionBase
from backend.core.plugins import PluginManager
from backend.core.plugins.loader import PluginLoader
from backend.infrastructure.plugins.catalog import PluginCatalog
from backend.infrastructure.plugins.legacy_adapter import (
    ACTION_REF_LEGACY_PLUGIN_MAP,
    LegacyPluginActionAdapter,
)
from backend.infrastructure.plugins.loader import PluginClassLoader


class ActionFactory:
    def __init__(self, catalog: PluginCatalog, loader: PluginClassLoader):
        self.catalog = catalog
        self.loader = loader

    def create(self, action_ref: str, ctx) -> ActionBase:
        manifest = self.catalog.get_action(action_ref)
        legacy_plugin_id = ACTION_REF_LEGACY_PLUGIN_MAP.get(manifest.action_ref)
        if legacy_plugin_id is not None:
            legacy_plugin_cls = self._load_legacy_plugin_class(legacy_plugin_id)
            return LegacyPluginActionAdapter(ctx, legacy_plugin_cls)

        action_cls = self.loader.load_action_class(manifest)
        return action_cls(ctx)

    def _load_legacy_plugin_class(self, plugin_id: str) -> type:
        manager = PluginManager(self.catalog.plugins_dir)
        manager.discover_plugins()

        if plugin_id not in manager._plugin_dirs:
            raise ValueError(f"Plugin not found: {plugin_id}")

        plugin_dir = manager._plugin_dirs[plugin_id]
        manifest = manager._plugin_metadata[plugin_id]
        return PluginLoader.load_plugin(plugin_dir, manifest)
