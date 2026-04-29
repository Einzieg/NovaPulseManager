import asyncio
import logging
from backend.core.plugins import PluginBase
from backend.core.LoadTemplates import Templates
from backend.plugins.permanent_task.models import PermanentTaskConfig

swipes = [
    None,
    [(900, 480), (900, 600), (900, 720), (900, 840), (900, 960)],
    [(900, 840), (900, 720), (900, 600), (900, 480), (900, 360), (900, 240), (900, 120)],
]


class PermanentPlugin(PluginBase):
    ConfigModel = PermanentTaskConfig

    async def prepare(self):
        await super().prepare()
        self.logging.log("常驻任务开始执行 >>>", self.target)

    async def execute(self):
        await self.device.async_init()
        while True:
            await self.device.check_running_status()
            await self.attack_monsters()
            await self.collect_wreckage()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log("常驻任务执行完成 <<<", self.target)

    async def collect_wreckage(self):
        if not self.plugin_config.wreckage:
            return

        await self.reset_process()

        for swipe in swipes:
            if swipe:
                await self.device.swipe(swipe, duration=400 if len(swipe) > 3 else 200)
                await asyncio.sleep(1)

            if await self._search_and_collect():
                return

    async def _search_and_collect(self) -> bool:
        for template in Templates.WRECKAGE_LIST:
            wreckage = await self.control.move_coordinates(template)
            if not wreckage:
                continue

            for coordinate in wreckage:
                await self.device.click(coordinate)
                await asyncio.sleep(0.5)

                if await self.control.matching_one(Templates.RECALL):
                    await self.device.click_back()

                await self.control.await_element_appear(
                    Templates.COLLECT, click=True, time_out=2, sleep=1
                )

                if await self.control.matching_one(Templates.NO_WORKSHIPS):
                    await self.device.click_back()
                    await asyncio.sleep(0.5)
                    await self.device.click_back()
                    await asyncio.sleep(30)
                    return True

            return True
        self.logging.log("未找到残骸", self.target, logging.INFO)
        return False

    async def attack_monsters(self):
        await self.reset_process()

        monster_configs = [
            (self.plugin_config.red_monster, Templates.MONSTER_RED_LIST),
            (self.plugin_config.elite_monster, Templates.MONSTER_ELITE_LIST),
            (self.plugin_config.normal_monster, Templates.MONSTER_NORMAL_LIST),
        ]

        for swipe in swipes:
            if swipe:
                await self.device.swipe(swipe, duration=400 if len(swipe) > 2 else 200)
                await asyncio.sleep(1)

            for enabled, template_list in monster_configs:
                if not enabled:
                    continue

                for template in template_list:
                    if await self.control.matching_one(template, click=True):
                        await self.attack()
                        return await self.attack_monsters()

    async def reset_process(self):
        await self.return_home()
        await self.control.await_element_appear(Templates.SPACE_STATION, click=True, time_out=5)
        await self.control.await_element_appear(Templates.STAR_SYSTEM, click=True, time_out=10)
        if await self.control.await_element_appear(Templates.SPACE_STATION, click=False, time_out=10):
            await self.device.zoom_out()
            await asyncio.sleep(5)
