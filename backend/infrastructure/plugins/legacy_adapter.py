from __future__ import annotations

from backend.domain.action import ActionBase


LEGACY_ACTION_REF_MAP = {
    "start_task": "nova_iron_galaxy.startup.launch",
    "start-task": "nova_iron_galaxy.startup.launch",
    "permanent_task": "nova_iron_galaxy.permanent.run",
    "permanent-task": "nova_iron_galaxy.permanent.run",
    "order_task": "nova_iron_galaxy.order.run",
    "order-task": "nova_iron_galaxy.order.run",
    "radar_task": "nova_iron_galaxy.radar.run",
    "radar-task": "nova_iron_galaxy.radar.run",
}

ACTION_REF_LEGACY_PLUGIN_MAP = {
    "nova_iron_galaxy.startup.launch": "start-task",
    "nova_iron_galaxy.permanent.run": "permanent-task",
    "nova_iron_galaxy.order.run": "order-task",
    "nova_iron_galaxy.radar.run": "radar-task",
}


class LegacyPluginActionAdapter(ActionBase):
    def __init__(self, ctx, legacy_plugin_cls):
        super().__init__(ctx)
        self.legacy_plugin = legacy_plugin_cls(ctx.device_name)

    async def prepare(self):
        await self.legacy_plugin.prepare()

    async def execute(self):
        await self.legacy_plugin.execute()

    async def cleanup(self):
        await self.legacy_plugin.cleanup()
