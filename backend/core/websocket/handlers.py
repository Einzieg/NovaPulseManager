"""WebSocket消息处理器"""
import logging
from functools import wraps
from pathlib import Path
from typing import Any, Dict

from backend.application.services import (
    AppCatalogService,
    DeviceService,
    PluginConfigService,
    RunService,
    SettingsService,
    WorkflowService,
)
from backend.core.scheduler import TaskScheduler
from backend.infrastructure.realtime import EventBus, WebSocketHub


def handle_errors(func):
    """错误处理装饰器,统一处理handler异常"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            return result
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Handler error in {func.__name__}: {e}", exc_info=True)
            raise

    return wrapper


class MessageHandlers:
    """WebSocket消息处理器集合"""

    def __init__(self, plugins_dir: Path, ws_server):
        self.plugins_dir = plugins_dir
        self.ws_server = ws_server
        self.schedulers: Dict[str, TaskScheduler] = {}
        self.logger = logging.getLogger(__name__)
        self.app_catalog_service = AppCatalogService(plugins_dir)
        self.device_service = DeviceService()
        self.workflow_service = WorkflowService()
        self.plugin_config_service = PluginConfigService(plugins_dir)
        self.settings_service = SettingsService()
        self.event_bus = EventBus()
        self.websocket_hub = WebSocketHub(self.event_bus, ws_server)
        self.run_service = RunService(
            workflow_service=self.workflow_service,
            scheduler_getter=self._get_scheduler,
            scheduler_lookup=lambda module_name: self.schedulers.get(module_name),
            event_bus=self.event_bus,
        )

    def _get_scheduler(self, module_name: str) -> TaskScheduler:
        """获取或创建调度器"""
        if module_name not in self.schedulers:
            self.schedulers[module_name] = TaskScheduler(
                module_name, self.plugins_dir, self.ws_server
            )
        return self.schedulers[module_name]

    def _scheduler_status(self, module_name: str) -> dict[str, Any] | None:
        scheduler = self.schedulers.get(module_name)
        return scheduler.get_status() if scheduler else None

    def _scheduler_is_running(self, module_name: str) -> bool:
        status = self._scheduler_status(module_name)
        return bool(status and status.get("is_running"))

    def _clear_scheduler(self, module_name: str) -> None:
        self.schedulers.pop(module_name, None)

    @handle_errors
    async def handle_task_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务启动请求"""
        module_name = payload.get("module_name")
        plugin_id = payload.get("plugin_id")

        if not module_name or not plugin_id:
            raise ValueError("Missing module_name or plugin_id")

        scheduler = self._get_scheduler(module_name)
        return await scheduler.start_plugin(plugin_id)

    @handle_errors
    async def handle_task_stop(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务停止请求"""
        module_name = payload.get("module_name")

        if not module_name:
            raise ValueError("Missing module_name")

        scheduler = self._get_scheduler(module_name)
        return await scheduler.stop_plugin()

    @handle_errors
    async def handle_module_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取设备列表（历史命名：module）。"""
        return self.device_service.list_devices(self._scheduler_status)

    @handle_errors
    async def handle_device_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """新增设备（DeviceConfig + CommonConfig）。"""
        return self.device_service.create_device(payload)

    @handle_errors
    async def handle_device_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """编辑设备信息。"""
        return self.device_service.update_device(
            payload,
            is_running=self._scheduler_is_running,
            clear_scheduler=self._clear_scheduler,
        )

    @handle_errors
    async def handle_device_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """删除设备。"""
        return self.device_service.delete_device(
            payload,
            is_running=self._scheduler_is_running,
            clear_scheduler=self._clear_scheduler,
        )

    @handle_errors
    async def handle_plugin_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取插件列表"""
        from backend.core.plugins import PluginManager

        manager = PluginManager(self.plugins_dir)
        plugins = manager.discover_plugins()

        plugin_list = []
        for manifest in plugins:
            plugin_list.append(
                {
                    "id": manifest.get("id"),
                    "name": manifest.get("name", manifest.get("id", "Unknown")),
                    "description": manifest.get("description", ""),
                    "version": manifest.get("version", "1.0.0"),
                    "author": manifest.get("author", "Unknown"),
                }
            )
        return {"plugins": plugin_list}

    @handle_errors
    async def handle_app_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取应用扩展包列表。"""
        return self.app_catalog_service.list_apps()

    @handle_errors
    async def handle_action_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取多层级 action 列表。"""
        return self.app_catalog_service.list_actions(
            app_id=payload.get("app_id"),
            module_id=payload.get("module_id"),
        )

    @handle_errors
    async def handle_plugin_config_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取指定插件的配置字段和当前值"""
        return self.plugin_config_service.get_plugin_config(payload)

    @handle_errors
    async def handle_plugin_config_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """更新指定插件的配置"""
        return self.plugin_config_service.update_plugin_config(payload)

    @handle_errors
    async def handle_workflow_save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """保存工作流到数据库"""
        return self.workflow_service.save_workflow(payload)

    @handle_errors
    async def handle_workflow_load(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """从数据库加载工作流。"""
        return self.workflow_service.load_workflow(payload)

    @handle_errors
    async def handle_workflow_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """启动工作流执行"""
        return await self.run_service.start_workflow(payload)

    @handle_errors
    async def handle_workflow_stop(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """停止工作流执行（仅当 scheduler 已存在时才尝试停止）。"""
        module_name = payload.get("module_name")
        if not module_name:
            raise ValueError("Missing module_name")

        scheduler = self.schedulers.get(module_name)
        if not scheduler:
            return {"status": "not_running", "module": module_name}

        return await scheduler.stop_workflow()

    @handle_errors
    async def handle_workflow_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """列出某设备的全部工作流（active 为主）。"""
        return self.workflow_service.list_workflows(payload)

    @handle_errors
    async def handle_workflow_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """按 workflow_id 获取工作流详情。"""
        return self.workflow_service.get_workflow(payload)

    @handle_errors
    async def handle_workflow_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """软删除（停用）工作流。"""
        return self.workflow_service.delete_workflow(payload)

    @handle_errors
    async def handle_workflow_set_current(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """设置设备当前工作流（current_workflow_id）。"""
        return self.workflow_service.set_current_workflow(payload)

    @handle_errors
    async def handle_run_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.run_service.start_workflow_by_id(payload.get("workflow_id"))

    @handle_errors
    async def handle_run_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        run_id = payload.get("run_id")
        if not run_id:
            raise ValueError("Missing run_id")
        return self.run_service.get_run(run_id)

    @handle_errors
    async def handle_run_cancel(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        run_id = payload.get("run_id")
        if not run_id:
            raise ValueError("Missing run_id")
        return await self.run_service.cancel_run(run_id)

    @handle_errors
    async def handle_run_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.run_service.list_runs()

    @handle_errors
    async def handle_config_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.settings_service.get_config()

    @handle_errors
    async def handle_config_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.settings_service.update_config(payload)
