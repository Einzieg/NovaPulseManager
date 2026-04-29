from pathlib import Path
from backend.core.plugins import PluginBase
from backend.plugins.radar_task.models import RadarTaskConfig

from backend.core.LoadTemplates import Templates, Template
from backend.core.NovaException import TaskCompleted
from backend.core.paths import resolve_template_path

PLUGIN_DIR = Path(__file__).resolve().parent

RADAR = Template(name="雷达", threshold=0.85, template_path=resolve_template_path("hidden/radar.png", plugin_dir=PLUGIN_DIR))
SEARCH = Template(name="搜索", threshold=0.80, template_path=resolve_template_path("hidden/search.png", plugin_dir=PLUGIN_DIR))
BUTTON_USE = Template(name="使用按钮", threshold=0.85, template_path=resolve_template_path("hidden/button_use_prop.png", plugin_dir=PLUGIN_DIR))
BUTTON_BUY = Template(name="购买按钮", threshold=0.85, template_path=resolve_template_path("hidden/button_buy.png", plugin_dir=PLUGIN_DIR))
MAX = Template(name="MAX", threshold=0.85, template_path=resolve_template_path("hidden/max.png", plugin_dir=PLUGIN_DIR))
RADAR_ENERGY = Template(name="雷达能量", threshold=0.75, template_path=resolve_template_path("hidden/energy.png", plugin_dir=PLUGIN_DIR))
GEC = Template(name="GEC", threshold=0.85, template_path=resolve_template_path("hidden/GEC.png", plugin_dir=PLUGIN_DIR))


class RadarPlugin(PluginBase):
    ConfigModel = RadarTaskConfig

    async def prepare(self):
        await super().prepare()
        self.logging.log("雷达任务开始执行 >>>", self.target)

    async def execute(self):
        await self.device.async_init()
        hidden_times = self.plugin_config.hidden_times
        try:
            if hidden_times:
                for _ in range(hidden_times):
                    await self.radar_process()
            else:
                while True:
                    await self.return_home()
                    await self.radar_process()
        except TaskCompleted:
            pass

    async def cleanup(self):
        await super().cleanup()
        await self.return_home()
        self.logging.log("雷达任务执行完成 <<<", self.target)

    async def radar_process(self):
        await self.control.await_element_appear(RADAR, click=True, time_out=3)
        await self.control.await_element_appear(SEARCH, click=True, time_out=3)
        if await self.control.await_element_appear(Templates.ATTACK_BUTTON, time_out=2):
            await self.attack(sleet_all=True)
            return
        if await self.control.await_element_appear(BUTTON_USE, click=True, time_out=2) | await self.control.await_element_appear(BUTTON_BUY, click=True, time_out=2):
            if self.plugin_config.hidden_policy == "不使用能量道具":
                raise TaskCompleted("不使用道具,雷达结束")
            if self.plugin_config.hidden_policy in ["使用能量道具", "使用GEC购买能量"]:
                await self.control.await_element_appear(MAX, click=True, time_out=1.5, sleep=0.5)
                if not await self.control.await_element_appear(RADAR_ENERGY, click=True, time_out=1, sleep=0.5):
                    if self.plugin_config.hidden_policy == "使用GEC购买能量":
                        await self.control.await_element_appear(GEC, click=True, time_out=1, sleep=1)
                    else:
                        raise TaskCompleted("不使用GEC购买道具,雷达结束")
                await self.control.await_element_appear(SEARCH, click=True, time_out=1, sleep=1)
            else:
                raise TaskCompleted("道具耗尽,雷达结束")
        await self.attack(sleet_all=True)
