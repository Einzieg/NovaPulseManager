from __future__ import annotations

from backend.domain.app import AppRuntimeBase
from backend.infrastructure.plugins.catalog import PluginCatalog
from backend.infrastructure.plugins.loader import PluginClassLoader


class AppRuntimeManager:
    def __init__(self, catalog: PluginCatalog, loader: PluginClassLoader):
        self.catalog = catalog
        self.loader = loader
        self._runtime_instances: dict[str, AppRuntimeBase] = {}
        self._current_app_by_device: dict[int, str] = {}

    def get_runtime(self, app_id: str) -> AppRuntimeBase:
        runtime = self._runtime_instances.get(app_id)
        if runtime is not None:
            return runtime

        manifest = self.catalog.get_app(app_id)
        runtime_cls = self.loader.load_runtime_class(manifest)
        runtime = runtime_cls()
        self._runtime_instances[app_id] = runtime
        return runtime

    async def ensure_app_ready(self, *, device_id: int, app_id: str, ctx) -> None:
        current_app = self._current_app_by_device.get(device_id)

        if current_app == app_id:
            runtime = self.get_runtime(app_id)
            await runtime.ensure_ready(ctx)
            return

        if current_app:
            old_runtime = self.get_runtime(current_app)
            await old_runtime.on_leave(ctx)

        new_runtime = self.get_runtime(app_id)
        await new_runtime.on_enter(ctx)
        await new_runtime.ensure_ready(ctx)

        self._current_app_by_device[device_id] = app_id
