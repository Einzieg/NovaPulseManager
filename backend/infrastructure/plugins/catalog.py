from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from backend.application.errors import PluginNotFound


@dataclass(frozen=True)
class AppManifest:
    app_id: str
    name: str
    version: str
    runtime_entry: str
    package_name: str | None
    base_dir: Path


@dataclass(frozen=True)
class ModuleManifest:
    app_id: str
    module_id: str
    name: str
    description: str
    base_dir: Path


@dataclass(frozen=True)
class ActionManifest:
    app_id: str
    module_id: str
    action_id: str
    action_ref: str
    name: str
    description: str
    entry_point: str
    config_model: str | None
    base_dir: Path


class PluginCatalog:
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._apps: dict[str, AppManifest] = {}
        self._modules: dict[tuple[str, str], ModuleManifest] = {}
        self._actions: dict[str, ActionManifest] = {}

    def discover(self) -> None:
        self._apps.clear()
        self._modules.clear()
        self._actions.clear()

        if not self.plugins_dir.exists():
            return

        for app_dir in self.plugins_dir.iterdir():
            if not app_dir.is_dir():
                continue

            manifest_path = app_dir / "manifest.json"
            if not manifest_path.exists():
                continue

            with open(manifest_path, "r", encoding="utf-8") as f:
                app_data = json.load(f)

            if app_data.get("kind") != "application":
                continue

            app_id = app_data["id"]
            app_manifest = AppManifest(
                app_id=app_id,
                name=app_data.get("name", app_id),
                version=app_data.get("version", "0.0.0"),
                runtime_entry=app_data["runtime"],
                package_name=app_data.get("package_name"),
                base_dir=app_dir,
            )
            self._apps[app_id] = app_manifest

            for module_id in app_data.get("modules", []):
                self._load_module(app_id, str(module_id), app_dir)

    def _load_module(self, app_id: str, module_id: str, app_dir: Path) -> None:
        module_dir = app_dir / "modules" / module_id
        manifest_path = module_dir / "manifest.json"
        if not manifest_path.exists():
            return

        with open(manifest_path, "r", encoding="utf-8") as f:
            module_data = json.load(f)

        if module_data.get("kind") != "module":
            return

        module_manifest = ModuleManifest(
            app_id=app_id,
            module_id=module_data.get("id", module_id),
            name=module_data.get("name", module_id),
            description=module_data.get("description", ""),
            base_dir=module_dir,
        )
        self._modules[(app_id, module_manifest.module_id)] = module_manifest

        for action in module_data.get("actions", []):
            action_id = action["id"]
            action_ref = f"{app_id}.{module_manifest.module_id}.{action_id}"
            self._actions[action_ref] = ActionManifest(
                app_id=app_id,
                module_id=module_manifest.module_id,
                action_id=action_id,
                action_ref=action_ref,
                name=action.get("name", action_id),
                description=action.get("description", ""),
                entry_point=action["entry_point"],
                config_model=action.get("config_model"),
                base_dir=module_dir,
            )

    def list_apps(self) -> list[AppManifest]:
        return list(self._apps.values())

    def get_app(self, app_id: str) -> AppManifest:
        try:
            return self._apps[app_id]
        except KeyError:
            raise PluginNotFound(f"App not found: {app_id}")

    def list_modules(self, app_id: str) -> list[ModuleManifest]:
        return [
            manifest
            for (manifest_app_id, _), manifest in self._modules.items()
            if manifest_app_id == app_id
        ]

    def list_actions(
        self,
        app_id: str | None = None,
        module_id: str | None = None,
    ) -> list[ActionManifest]:
        actions = list(self._actions.values())
        if app_id is not None:
            actions = [action for action in actions if action.app_id == app_id]
        if module_id is not None:
            actions = [action for action in actions if action.module_id == module_id]
        return actions

    def get_action(self, action_ref: str) -> ActionManifest:
        try:
            return self._actions[action_ref]
        except KeyError:
            raise PluginNotFound(f"Action not found: {action_ref}")
