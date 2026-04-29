import asyncio
import json
import logging

# Legacy TaskBase（兼容层）：历史上使用 top-level `core.*` 路径。
# 这里统一改为 `backend.core.*`，避免在 pytest/uv 环境中出现 `ModuleNotFoundError: core`。
from backend.core.tools.ControlTools import ControlTools
from backend.core.LoadTemplates import Templates
from backend.core.LogManager import LogManager
from backend.core.NovaException import TaskAbortedError
from backend.device_operation.DeviceUtils import DeviceUtils
from backend.models import DeviceConfig
from backend.models.CommonConfig import CommonConfig
from backend.models import Config

WAITING = 0
RUNNING = 1
SUCCESS = 2
FAILED = -1

fleet_map = {
    "fleet1": (1290, 200),
    "fleet2": (1290, 325),
    "fleet3": (1290, 450),
    "fleet4": (1290, 575),
    "fleet5": (1290, 700),
    "fleet6": (1290, 825),
}


class TaskBase:
    def __init__(self, target):
        self.revenge = False
        self.target = target
        self.status = WAITING
        self.logging = LogManager()
        self.device = DeviceUtils(target)

        self.control = ControlTools(target, self.device)
        self.device_config = DeviceConfig.get(DeviceConfig.name == target)
        self.common_config = CommonConfig.get_or_create(device=self.device_config)[0]
        self.config = Config.get_or_create(id=1)[0]

    async def prepare(self):
        """任务前置操作"""
        self._update_status(WAITING)

    async def execute(self):
        """主执行逻辑（需子类实现）"""
        await self.device.async_init()
        # 可能需要增加检查游戏运行状态,防止游戏闪退
        raise NotImplementedError

    async def cleanup(self):
        """任务后置操作"""
        self._update_status(SUCCESS)

    def _update_status(self, status):
        """更新任务状态"""
        self.status = status

    async def return_home(self):
        await self.relogin_check()
        await self.close_check()
        await self.recall_check()
        await self.shortcut_check()
        await self.select_fleet_check()
        await self.none_available_check()
        await self.sign_back_check()
        await self.disconnected_check()
        await self.control.matching_one(Templates.TO_HOME, click=True)

    async def relogin_check(self):
        """检查是否需要重新登录"""
        if await self.control.matching_one(Templates.SIGN_BACK_IN):
            if self.common_config.auto_relogin:
                relogin_time = self.common_config.relogin_time
                self.logging.log(f"检测到已登出，等待 {relogin_time} 秒后重新登录...", self.target, logging.INFO)
                if relogin_time is None:
                    relogin_time = 600
                await asyncio.sleep(relogin_time)
                await self.control.matching_one(Templates.CONFIRM_RELOGIN, click=True, sleep=10)
                self.logging.log("重新登录成功！", self.target, logging.INFO)
            else:
                raise TaskAbortedError("检测到已登出, 未开启自动抢登, 执行结束")

    async def close_check(self):
        for template in Templates.CLOSE_BUTTONS:
            await self.control.matching_one(template, click=True)

    async def recall_check(self):
        if await self.control.matching_one(Templates.RECALL):
            await self.device.click_back()

    async def shortcut_check(self):
        if await self.control.matching_one(Templates.IN_SHORTCUT):
            await self.device.click_back()

    async def select_fleet_check(self):
        if await self.control.matching_one(Templates.SELECTALL):
            await self.device.click_back()

    async def none_available_check(self):
        if await self.control.matching_one(Templates.NO_WORKSHIPS):
            await self.device.click_back()

    async def sign_back_check(self):
        if await self.control.matching_one(Templates.SIGN_BACK_IN):
            await self.control.matching_one(Templates.CONFIRM_RELOGIN, click=True, sleep=10)

    async def disconnected_check(self):
        if await self.control.matching_one(Templates.DISCONNECTED):
            raise TaskAbortedError("无法连接到网络")

    async def attack(self, sleet_all=False):
        self.revenge = False
        await self.control.await_element_appear(Templates.ATTACK_BUTTON, click=True, time_out=3)
        if await self.control.await_element_appear(Templates.REVENGE, time_out=2):
            self.revenge = True
            await self.control.matching_one(Templates.REVENGE_ATTACK, click=True, sleep=1)
        await self.control.matching_one(Templates.REPAIR, click=True, sleep=1)
        fleets = json.loads(self.common_config.attack_fleet)
        if "all" in fleets or sleet_all:
            await self.control.await_element_appear(Templates.SELECTALL, click=True, time_out=3, sleep=0.5)
        else:
            for fleet in fleets:
                await self.device.click(fleet_map[fleet])

        if await self.control.await_element_appear(Templates.CONFIRM_ATTACK, click=True, time_out=0.5):
            await self.combat_checks()
            if self.revenge:
                await self.recall_fleets()
                self.logging.log("等待复仇", self.target)
                await self.combat_checks()
                self.revenge = False

    async def combat_checks(self):
        self.logging.log("检查是否进入战斗 >>>", self.target, logging.DEBUG)
        if await self.control.await_element_appear(Templates.IN_BATTLE, time_out=180):
            self.logging.log("进入战斗<<<", self.target, logging.DEBUG)
            self.logging.log("检查战斗是否结束>>>", self.target, logging.DEBUG)
            if await self.control.await_element_disappear(Templates.IN_BATTLE, time_out=120, sleep=3):
                self.logging.log("战斗结束<<<", self.target, logging.DEBUG)

    async def recall_fleets(self):
        for template in Templates.MENUS:
            await self.control.await_element_appear(template, click=True, time_out=2)
        await self.control.await_element_appear(Templates.FLEETS_MENU, click=True, time_out=3, sleep=2)
        await self.control.await_element_appear(Templates.HOVER_RECALL, click=True, time_out=2)
        await self.device.click_back()
        await asyncio.sleep(1)

