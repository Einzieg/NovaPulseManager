from __future__ import annotations

from abc import ABC


class AppRuntimeBase(ABC):
    app_id: str
    name: str
    package_name: str | None = None

    async def launch(self, ctx):
        raise NotImplementedError

    async def ensure_foreground(self, ctx):
        raise NotImplementedError

    async def ensure_ready(self, ctx):
        await self.launch(ctx)
        await self.ensure_foreground(ctx)

    async def on_enter(self, ctx):
        pass

    async def on_leave(self, ctx):
        pass
