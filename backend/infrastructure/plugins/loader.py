from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from backend.core.plugins.exceptions import PluginLoadError
from backend.domain.action import ActionBase
from backend.domain.app import AppRuntimeBase
from backend.infrastructure.plugins.catalog import ActionManifest, AppManifest


class PluginClassLoader:
    def load_runtime_class(self, manifest: AppManifest) -> type[AppRuntimeBase]:
        runtime_cls = self._load_class(
            base_dir=manifest.base_dir,
            entry_point=manifest.runtime_entry,
            module_name=f"nova_plugins.{manifest.app_id}.runtime",
        )
        if not issubclass(runtime_cls, AppRuntimeBase):
            raise PluginLoadError(f"{runtime_cls.__name__} must inherit from AppRuntimeBase")
        return runtime_cls

    def load_action_class(self, manifest: ActionManifest) -> type[ActionBase]:
        action_cls = self._load_class(
            base_dir=manifest.base_dir,
            entry_point=manifest.entry_point,
            module_name=(
                f"nova_plugins.{manifest.app_id}.modules."
                f"{manifest.module_id}.{manifest.action_id}"
            ),
        )
        if not issubclass(action_cls, ActionBase):
            raise PluginLoadError(f"{action_cls.__name__} must inherit from ActionBase")
        return action_cls

    def load_config_class(self, base_dir: Path, entry_point: str, module_name: str) -> type:
        return self._load_class(
            base_dir=base_dir,
            entry_point=entry_point,
            module_name=module_name,
        )

    def _load_class(self, *, base_dir: Path, entry_point: str, module_name: str) -> type:
        if ":" not in entry_point:
            raise PluginLoadError(f"Invalid entry_point format: {entry_point}")

        module_file, class_name = entry_point.split(":", 1)
        module_path = base_dir / module_file
        if not module_path.exists():
            raise PluginLoadError(f"Plugin module not found: {module_path}")

        unique_name = f"{module_name}.{module_path.stem}"
        spec = importlib.util.spec_from_file_location(unique_name, module_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Failed to load module spec: {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[unique_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, class_name):
            raise PluginLoadError(f"Class {class_name} not found in {module_file}")

        return getattr(module, class_name)
