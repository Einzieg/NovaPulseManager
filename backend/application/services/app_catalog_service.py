from __future__ import annotations

from pathlib import Path

from backend.infrastructure.plugins.catalog import PluginCatalog


class AppCatalogService:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir

    def _discover_catalog(self) -> PluginCatalog:
        catalog = PluginCatalog(self.plugins_dir)
        catalog.discover()
        return catalog

    def list_apps(self) -> dict[str, list[dict]]:
        catalog = self._discover_catalog()
        apps = [
            {
                "id": app.app_id,
                "name": app.name,
                "version": app.version,
                "package_name": app.package_name,
            }
            for app in catalog.list_apps()
        ]
        return {"apps": apps}

    def list_actions(
        self,
        app_id: str | None = None,
        module_id: str | None = None,
    ) -> dict[str, list[dict]]:
        catalog = self._discover_catalog()
        actions = [
            {
                "app_id": action.app_id,
                "module_id": action.module_id,
                "action_id": action.action_id,
                "action_ref": action.action_ref,
                "name": action.name,
                "description": action.description,
            }
            for action in catalog.list_actions(app_id=app_id, module_id=module_id)
        ]
        return {"actions": actions}
