import json
import asyncio
import logging
from pathlib import Path
from typing import List, Any, Optional

from backend.core.plugins import PluginBase
from backend.plugins.order_task.models import OrderTaskConfig
from backend.core.LoadTemplates import Template, Templates
from backend.core.NovaException import TaskCompleted
from backend.core.tools.OcrTools import OcrTools
from backend.core.tools.TimeTools import TimeTools
from backend.core.tools.ImageTools import ImageTools
from backend.core.paths import resolve_template_path


PLUGIN_DIR = Path(__file__).resolve().parent


# ===== 天赋切换模板 =====
TO_TALENT = Template(
    name="天赋按钮",
    threshold=0.85,
    template_path=resolve_template_path("talent/to_talent.png", plugin_dir=PLUGIN_DIR)
)
TALENT_CHOICE = Template(
    name="天赋选择",
    threshold=0.85,
    template_path=resolve_template_path("talent/special_talent.png", plugin_dir=PLUGIN_DIR)
)
TALENT_RC = Template(
    name="增加RC",
    threshold=0.85,
    template_path=resolve_template_path("talent/increase_rc.png", plugin_dir=PLUGIN_DIR)
)
TALENT_TIME = Template(
    name="减少时间",
    threshold=0.85,
    template_path=resolve_template_path("talent/reduce_time.png", plugin_dir=PLUGIN_DIR)
)
CONFIRM_TALENT = Template(
    name="天赋确认",
    threshold=0.85,
    template_path=resolve_template_path("talent/confirm_replacement_talent.png", plugin_dir=PLUGIN_DIR)
)

# ===== PCBA订单提交模板 =====
TO_ORDER = Template(
    name="订单按钮",
    threshold=0.85,
    template_path=resolve_template_path("order/to_order.png", plugin_dir=PLUGIN_DIR)
)
PCBA_DELIVERY = Template(
    name="PCBA提交",
    threshold=0.75,
    template_path=resolve_template_path("order/PCBA_delivery.png", plugin_dir=PLUGIN_DIR)
)
PCBA_INSUFFICIENT = Template(
    name="PCBA不足",
    threshold=0.75,
    template_path=resolve_template_path("order/PCBA_insufficient.png", plugin_dir=PLUGIN_DIR)
)
ORDER_DEPARTURE = Template(
    name="订单离港",
    threshold=0.75,
    template_path=resolve_template_path("order/departures.png", plugin_dir=PLUGIN_DIR)
)
DELIVERY_CONFIRM = Template(
    name="提交确认",
    threshold=0.85,
    template_path=resolve_template_path("order/confirm_delivery.png", plugin_dir=PLUGIN_DIR)
)
ORDER_CLOSE = Template(
    name="关闭订单",
    threshold=0.85,
    template_path=resolve_template_path("order/close_order.png", plugin_dir=PLUGIN_DIR)
)

# ===== 制造系统模板 =====
TO_CONTROL_PANEL_GOLD = Template(
    name="空间站管理界面金",
    threshold=0.75,
    template_path=resolve_template_path("button/button_system_gold.png")
)
TO_CONTROL_PANEL_BLUE = Template(
    name="空间站管理界面蓝",
    threshold=0.75,
    template_path=resolve_template_path("button/button_system_blue.png")
)
ORDER_IS_HERE = Template(
    name="订单已到",
    threshold=0.85,
    template_path=resolve_template_path("order/order_arrived.png", plugin_dir=PLUGIN_DIR)
)
ECONOMY = Template(
    name="经济",
    threshold=0.85,
    template_path=resolve_template_path("order/economy.png", plugin_dir=PLUGIN_DIR)
)
QUICK_DELIVER = Template(
    name="快速提交",
    threshold=0.65,
    template_path=resolve_template_path("order/submit_order.png", plugin_dir=PLUGIN_DIR)
)
PRODUCE_ORDER = Template(
    name="订单获取",
    threshold=0.85,
    template_path=resolve_template_path("order/produce_order.png", plugin_dir=PLUGIN_DIR)
)
DEVELOPMENT = Template(
    name="研发",
    threshold=0.85,
    template_path=resolve_template_path("order/development.png", plugin_dir=PLUGIN_DIR)
)
GOTO_FACTORY = Template(
    name="前往工厂",
    threshold=0.85,
    template_path=resolve_template_path("order/goto_factory.png", plugin_dir=PLUGIN_DIR)
)
BACK_TO_QUEUE = Template(
    name="返回制造",
    threshold=0.85,
    template_path=resolve_template_path("order/return_to_factorymain.png", plugin_dir=PLUGIN_DIR)
)
SMART_PRODUCTION = Template(
    name="智能制造",
    threshold=0.85,
    template_path=resolve_template_path("order/auto_produce.png", plugin_dir=PLUGIN_DIR)
)
SPEEDUP_PRODUCTION = Template(
    name="制造加速",
    threshold=0.85,
    template_path=resolve_template_path("order/speedup_production.png", plugin_dir=PLUGIN_DIR)
)
SPEEDUP_15_MIN = Template(
    name="15分钟加速",
    threshold=0.85,
    template_path=resolve_template_path("order/seppdup_15_min.png", plugin_dir=PLUGIN_DIR)
)
SPEEDUO_1_HOUR = Template(
    name="1小时加速",
    threshold=0.85,
    template_path=resolve_template_path("order/speedup_1_hour.png", plugin_dir=PLUGIN_DIR)
)
SPEEDUO_3_HOUR = Template(
    name="3小时加速",
    threshold=0.85,
    template_path=resolve_template_path("order/speedup_3_hour.png", plugin_dir=PLUGIN_DIR)
)
QUEUE_SPEEDUP = Template(
    name="批量使用加速",
    threshold=0.9,
    template_path=resolve_template_path("order/quick_speedup.png", plugin_dir=PLUGIN_DIR)
)
CLOSE_FACTORY = Template(
    name="退出工厂",
    threshold=0.85,
    template_path=resolve_template_path("button/btn_close1.png")
)

# ===== 订单获取模板 =====
MORE_ORDER = Template(
    name="更多订单",
    threshold=0.85,
    template_path=resolve_template_path("order/more_order.png", plugin_dir=PLUGIN_DIR)
)
BEACON_ORDER = Template(
    name="信标订单",
    threshold=0.85,
    template_path=resolve_template_path("order/fast_forward.png", plugin_dir=PLUGIN_DIR)
)
GEC_ORDER = Template(
    name="GEC订单",
    threshold=0.85,
    template_path=resolve_template_path("order/gec_speedup.png", plugin_dir=PLUGIN_DIR)
)
BEACON_CONFIRM = Template(
    name="信标确认",
    threshold=0.85,
    template_path=resolve_template_path("order/confirm_delivery.png", plugin_dir=PLUGIN_DIR)
)
COLLECT_ALL = Template(
    name="全部领取",
    threshold=0.85,
    template_path=resolve_template_path("order/collect_all.png", plugin_dir=PLUGIN_DIR)
)
ORDER_FINISH = Template(
    name="订单完成",
    threshold=0.95,
    template_path=resolve_template_path("order/order_finish.png", plugin_dir=PLUGIN_DIR)
)

# ===== 常量配置 =====
QHOUR_SPEEDUP_OFFSET_X = 410
QHOUR_SPEEDUP_OFFSET_Y = 10
SPEEDUP_MASK = {
    "retain": [(1300, 130, 1870, 870)],
    "remove": [(1560, 240, 1840, 870), (1300, 130, 1625, 200)]
}
SPEEDUP_SECOND = {
    "15_min": 15 * 60,
    "1_hour": 60 * 60,
    "3_hour": 3 * 60 * 60
}

TASK_NAME = "订单"


class OrderPlugin(PluginBase):
    """订单任务插件"""
    ConfigModel = OrderTaskConfig

    plugin_id = "order-task"
    name = "订单任务"
    version = "1.0.0"
    description = "自动完成订单提交、PCBA使用、制造加速、天赋切换等功能"
    author = "Nova Pulse Manager"

    def __init__(self, target):
        super().__init__(target)
        self.target = target
        self.order_policy = self.plugin_config.order_policy
        self.order_hasten_policy = self.plugin_config.order_hasten_policy
        self.order_speeduo_policy = json.loads(self.plugin_config.order_speeduo_policy)
        self.ocr_tool = self.config.ocr_tool
        self.ocr = OcrTools()
        self.time_tools = TimeTools()
        self.image_tool = ImageTools()

    async def prepare(self):
        await super().prepare()
        self.logging.log(f"任务 {TASK_NAME} 开始执行 >>>", self.target)

    async def execute(self):
        self._update_status("running")
        await self.start()

    async def cleanup(self):
        await super().cleanup()
        self.logging.log(f"任务 {TASK_NAME} 执行完成 <<<", self.target)

    async def start(self):
        order_times = self.plugin_config.order_times
        try:
            if order_times:
                for _ in range(order_times):
                    await self.order_process()
            else:
                while True:
                    await self.return_home()
                    await self.order_process()
        except TaskCompleted as e:
            self.logging.log(e, self.target)
            self._update_status("success")
            return

    @staticmethod
    def get_next_element(data_list: List[Any], target: Any) -> Optional[Any]:
        """在列表中查找目标元素并返回下一个元素"""
        try:
            index_of_target = data_list.index(target)
            next_index = index_of_target + 1

            if next_index < len(data_list):
                return data_list[next_index]
            else:
                return 0

        except ValueError:
            return 0

    @staticmethod
    def str2int(s: str) -> int:
        try:
            return int(s)
        except ValueError:
            return 0

    async def order_process(self):
        """订单处理主流程"""
        # 第一步：切换天赋至 +RC
        await self.change_talent(TALENT_RC)

        # 第二步：执行生产/提交
        if '订单电路板' in self.order_hasten_policy:
            await self._process_pcba()

        if '使用制造加速' in self.order_hasten_policy:
            await self._process_manufacture_speedup()

        # 第三步：切换天赋至 -Time
        await self.change_talent(TALENT_TIME)

        # 第四步：获取新订单
        await self._fetch_new_order()

    async def _process_pcba(self):
        """使用PCBA电路板提交订单"""
        self.logging.log(f"{TASK_NAME} 使用电路板 <<<", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_ORDER, click=True, time_out=3)
        await self.control.await_element_appear(PCBA_DELIVERY, click=True, time_out=3)
        if await self.control.await_element_appear(PCBA_INSUFFICIENT, time_out=2):
            await self.return_home()
            raise TaskCompleted("PCBA道具不足")
        await self.control.await_element_appear(DELIVERY_CONFIRM, click=True, time_out=3)
        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)

    async def _process_manufacture_speedup(self):
        """使用制造加速完成订单"""
        self.logging.log(f"{TASK_NAME} 使用制造加速 <<<", self.target, logging.DEBUG)

        # 打开制造界面
        has_panel = await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=1) | \
                    await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=1)
        if not has_panel:
            await self.return_home()
            return

        await self.control.await_element_appear(ECONOMY, click=True, time_out=1)
        if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
            await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
            if await self.control.await_element_appear(PRODUCE_ORDER, click=True, time_out=2):
                await self.control.await_element_appear(GOTO_FACTORY, click=True, time_out=2)
                if await self.control.await_element_appear(DEVELOPMENT, click=False, time_out=2):
                    raise TaskCompleted("无部件图纸")
                await self.control.await_element_appear(BACK_TO_QUEUE, click=True, time_out=2)

                # 加速循环
                speedup_running = True
                while speedup_running:
                    await self.control.await_element_appear(SMART_PRODUCTION, click=True, time_out=2, sleep=1.5)

                    if not await self.control.await_element_appear(SPEEDUP_PRODUCTION, click=True, time_out=2):
                        break

                    while True:
                        img = self.image_tool.apply_mask(self.device.get_screencap(), SPEEDUP_MASK)
                        fabricate_ocr = await self.ocr.async_ocr(provider=self.ocr_tool, image=img)
                        if not fabricate_ocr['success']:
                            break

                        try:
                            fabricate_time = self.time_tools.parse_duration_to_seconds(fabricate_ocr['texts'][0])
                        except IndexError:
                            break

                        props_remaining = {
                            "15_min": self.str2int(self.get_next_element(fabricate_ocr['texts'], "15分钟部件加速")),
                            "1_hour": self.str2int(self.get_next_element(fabricate_ocr['texts'], "1小时部件加速")),
                            "3_hour": self.str2int(self.get_next_element(fabricate_ocr['texts'], "3小时部件加速"))
                        }
                        self.logging.log(props_remaining, self.target, logging.DEBUG)

                        for speeduo_policy in self.order_speeduo_policy:
                            if fabricate_time >= SPEEDUP_SECOND[speeduo_policy]:
                                if speeduo_policy == "15_min" and props_remaining['15_min']:
                                    await self.control.await_element_appear(SPEEDUP_15_MIN, click=True, time_out=2,
                                                                            offset_x=QHOUR_SPEEDUP_OFFSET_X,
                                                                            offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                elif speeduo_policy == "1_hour" and props_remaining['1_hour']:
                                    await self.control.await_element_appear(SPEEDUO_1_HOUR, click=True, time_out=2,
                                                                            offset_x=QHOUR_SPEEDUP_OFFSET_X,
                                                                            offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                elif speeduo_policy == "3_hour" and props_remaining['3_hour']:
                                    await self.control.await_element_appear(SPEEDUO_3_HOUR, click=True, time_out=2,
                                                                            offset_x=QHOUR_SPEEDUP_OFFSET_X,
                                                                            offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                                    break
                                continue

                        await self.control.await_element_appear(QUEUE_SPEEDUP, click=True, time_out=2, sleep=1)

                        img = self.image_tool.apply_mask(self.device.get_screencap(), SPEEDUP_MASK)
                        fabricate_ocr = await self.ocr.async_ocr(provider=self.ocr_tool, image=img)
                        if not fabricate_ocr['success']:
                            speedup_running = False
                            break

                        try:
                            fabricate_time = self.time_tools.parse_duration_to_seconds(fabricate_ocr['texts'][0])
                        except IndexError:
                            speedup_running = False
                            break

                        if fabricate_time and fabricate_time <= SPEEDUP_SECOND['15_min']:
                            await self.control.await_element_appear(SPEEDUP_15_MIN, click=True, time_out=2,
                                                                    offset_x=QHOUR_SPEEDUP_OFFSET_X,
                                                                    offset_y=QHOUR_SPEEDUP_OFFSET_Y, sleep=1.5)
                            speedup_running = False
                            break
                        if fabricate_time == 0:
                            speedup_running = False
                            break

                if not speedup_running:
                    await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                    await self._submit_remaining_orders()
                    return

                await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                await self._submit_remaining_orders()
            else:
                await self.device.click_back()
                await self.return_home()
        else:
            if self.order_policy == "不使用超空间信标":
                await self.return_home()
                raise TaskCompleted("不使用超空间信标,订单结束 <<<")
            else:
                await self.device.click_back()

    async def _submit_remaining_orders(self):
        """提交剩余订单"""
        if await self.control.await_element_appear(TO_CONTROL_PANEL_GOLD, click=True, time_out=2) | \
                await self.control.await_element_appear(TO_CONTROL_PANEL_BLUE, click=True, time_out=2):
            if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=2)
                if not await self.control.await_element_appear(PRODUCE_ORDER, click=False, time_out=2):
                    if await self.control.await_element_appear(ORDER_IS_HERE, click=True, time_out=3):
                        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3)
                else:
                    await self.device.swipe([(1000, 950), (1000, 950), (1000, 900), (1000, 100)], 200)
                    await asyncio.sleep(2)
                    await self.control.matching_one(COLLECT_ALL, click=True, sleep=1)
                    await self.device.swipe([(1000, 100), (1000, 110), (1000, 150), (1000, 950)], 200)
                    await asyncio.sleep(2)
                    await self.control.await_element_appear(QUICK_DELIVER, click=True, time_out=3)

    async def _fetch_new_order(self):
        """获取新订单"""
        self.logging.log(f"{TASK_NAME} 获取新订单 >>>", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_ORDER, click=True, time_out=3, sleep=3)
        if await self.control.matching_one(ORDER_FINISH):
            raise TaskCompleted("今日订单已完成 <<<")
        await self.control.await_element_appear(ORDER_DEPARTURE, click=True, time_out=3)
        await self.control.await_element_appear(ORDER_CLOSE, click=True, time_out=3)

        if await self.control.await_element_appear(MORE_ORDER, click=True, time_out=3):
            await self._handle_more_order()

    async def _handle_more_order(self):
        """处理更多订单请求"""
        if self.order_policy == "不使用超空间信标":
            await self.return_home()
            raise TaskCompleted("不使用超空间信标,订单结束 <<<")

        if self.order_policy == "使用超空间信标" or self.order_policy == "使用GEC购买信标":
            await self.control.await_element_appear(BEACON_ORDER, click=True, time_out=3)

        if await self.control.await_element_appear(GEC_ORDER, click=False, time_out=3):
            if self.order_policy == "使用GEC购买信标":
                await self.control.await_element_appear(GEC_ORDER, click=True, time_out=1)
            else:
                await self.return_home()
                raise TaskCompleted("超空间信标不足,订单结束 <<<")

        await self.control.await_element_appear(BEACON_CONFIRM, click=True, time_out=3)

    async def change_talent(self, mode):
        """切换天赋"""
        self.logging.log(f"{TASK_NAME} 修改天赋至{mode.name} <<<", self.target, logging.DEBUG)
        await self.control.await_element_appear(Templates.TO_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(Templates.MORE_SYSTEM, click=True, time_out=3)
        await self.control.await_element_appear(TO_TALENT, click=True, time_out=3)
        await self.control.await_element_appear(TALENT_CHOICE, click=True, time_out=3)
        await self.control.await_element_appear(mode, click=True, time_out=3)
        await self.control.await_element_appear(CONFIRM_TALENT, click=True, time_out=3, sleep=1)
        await self.control.await_element_appear(Templates.TO_HOME, click=True, time_out=3, sleep=1)
