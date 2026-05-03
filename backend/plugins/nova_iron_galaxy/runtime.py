from backend.domain.app import AppRuntimeBase


class NovaIronGalaxyRuntime(AppRuntimeBase):
    app_id = "nova_iron_galaxy"
    name = "Nova: Iron Galaxy"
    package_name = "com.stone3.ig"

    async def launch(self, ctx):
        pass

    async def ensure_foreground(self, ctx):
        pass
