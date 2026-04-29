from backend.core.plugins import PluginBase
from backend.plugins.start_task.models import StartTaskConfig
from backend.core.LoadTemplates import Templates


class StartPlugin(PluginBase):
    ConfigModel = StartTaskConfig

    def __init__(self, target):
        super().__init__(target)
        self.quick_start = False

    async def prepare(self):
        await super().prepare()
        self.logging.log("启动任务开始执行 >>>", self.target)

    async def execute(self):
        await self.device.async_init()
        await self.start()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log("启动任务执行完成 <<<", self.target)

    async def start(self):
        if self.plugin_config.autostart_simulator and not self.quick_start:
            await self.device.start_simulator()
            await self.device.check_running_status()
            await self.device.check_wm_size()
            if await self.control.await_element_appear(Templates.NEBULA, time_out=120, sleep=3):
                self.logging.log("游戏启动成功", self.target)
            else:
                self.logging.log("游戏启动失败,尝试重启", self.target)
                await self.device.close_app()
                await self.start()
            await self.control.matching_one(Templates.SIGN_BACK_IN, click=True)
        else:
            self.logging.log("跳过启动模拟器", self.target)
