import asyncio
import logging
from pathlib import Path
from typing import Optional

from backend.core.NovaException import TaskAbortedError, TaskCompleted
from backend.core.logging import LogManager
from backend.core.plugins import PluginBase, PluginManager
from backend.core.task_result import TaskResult
from backend.models import DeviceConfig


class TaskScheduler:
    """任务调度器,管理单个Module的插件执行"""

    def __init__(self, module_name: str, plugins_dir: Path, ws_server=None):
        self.module_name = module_name
        self.device_config = DeviceConfig.get(DeviceConfig.name == module_name)

        self.plugin_manager = PluginManager(plugins_dir)
        self.logger = logging.getLogger(__name__)

        self.current_task: Optional[asyncio.Task] = None
        self.current_plugin: Optional[PluginBase] = None
        self.is_running = False
        self.ws_server = ws_server

        self.last_result: Optional[TaskResult] = None

        # 工作流相关
        self.workflow_executor = None
        self.execution_mode = "plugin"  # 'plugin' or 'workflow'
        self._workflow_stop_requested = False

        # 初始化LogManager,传入ws_server用于日志推送
        self.log_manager = LogManager(ws_server=ws_server)

        # 发现可用插件
        self.plugin_manager.discover_plugins()
        self.logger.info(f"Discovered plugins: {self.plugin_manager.list_loaded_plugins()}")

    async def start_plugin(self, plugin_id: str) -> dict:
        """启动插件任务"""
        if self.is_running:
            raise RuntimeError(f"Module {self.module_name} is already running")

        self.last_result = None

        try:
            self.current_plugin = self.plugin_manager.load_plugin(plugin_id, self.module_name)
            self.is_running = True

            # 创建异步任务（任务内部会消化异常，避免 'Task exception was never retrieved'）
            self.current_task = asyncio.create_task(self._run_plugin(plugin_id))

            self.logger.info(f"启动插件 {plugin_id} 对 {self.module_name}")
            return {"status": "started", "module": self.module_name, "plugin": plugin_id}
        except Exception as e:
            self.is_running = False
            self.logger.error(f"插件启动失败 {plugin_id}: {e}", exc_info=True)
            raise

    async def stop_plugin(self) -> dict:
        """停止当前插件任务"""
        if not self.is_running:
            return {"status": "not_running", "module": self.module_name}

        if self.current_task:
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        self.is_running = False
        self.current_plugin = None
        self.current_task = None

        self.logger.info(f"插件停止 {self.module_name}")
        return {"status": "stopped", "module": self.module_name}

    async def _run_plugin(self, plugin_id: str) -> None:
        """执行插件任务（后台Task）。"""

        plugin = self.current_plugin
        result: Optional[TaskResult] = None

        try:
            if plugin is None:
                result = TaskResult.fail("plugin_not_loaded", error="current_plugin is None")
                return

            await plugin.prepare()
            await plugin.execute()
            result = TaskResult.ok("completed", data={"plugin_id": plugin_id})

        except asyncio.CancelledError:
            result = TaskResult.cancelled("cancelled",)
            raise

        except TaskCompleted as e:
            result = TaskResult.ok(str(e), data={"plugin_id": plugin_id})

        except TaskAbortedError as e:
            result = TaskResult.fail(str(e), error=str(e), data={"plugin_id": plugin_id})

        except Exception as e:
            self.logger.error(f"插件执行错误: {e}", exc_info=True)
            result = TaskResult.fail("plugin_error", error=str(e), data={"plugin_id": plugin_id})

        finally:
            if plugin is not None:
                try:
                    await plugin.cleanup()
                except Exception as e:
                    self.logger.error(f"插件清理失败: {e}", exc_info=True)
                    if result and result.success:
                        result = TaskResult.fail(
                            "cleanup_failed",
                            error=str(e),
                            data={"plugin_id": plugin_id},
                        )

            self.last_result = result
            self.is_running = False

    async def start_workflow(self, workflow_data: dict) -> dict:
        """启动工作流执行"""
        if self.is_running:
            raise RuntimeError(f"模块 {self.module_name} 正在运行中")

        self.last_result = None

        try:
            # 动态导入WorkflowExecutor,避免循环依赖
            from backend.core.scheduler.workflow_executor import WorkflowExecutor

            self.workflow_executor = WorkflowExecutor(
                workflow_data=workflow_data,
                plugin_manager=self.plugin_manager,
                ws_server=self.ws_server,
                module_name=self.module_name,
            )

            self.is_running = True
            self.execution_mode = "workflow"
            self._workflow_stop_requested = False

            workflow_id = workflow_data.get("id", "unknown")

            # 创建异步任务（任务内部会消化异常）
            self.current_task = asyncio.create_task(self._run_workflow(workflow_id))

            await self._broadcast_module_status(
                reason="workflow_started", workflow_id=workflow_id
            )

            self.logger.info(f"开始工作流程 {workflow_id} 模块 {self.module_name}")
            return {
                "status": "started",
                "module": self.module_name,
                "workflow_id": workflow_id,
                "mode": "workflow",
            }
        except Exception as e:
            self.is_running = False
            self.execution_mode = "plugin"
            self.current_task = None
            self.workflow_executor = None
            self._workflow_stop_requested = False
            await self._broadcast_module_status(reason="workflow_start_failed")
            self.logger.error(f"无法启动工作流程: {e}", exc_info=True)
            raise

    async def stop_workflow(self) -> dict:
        """停止当前工作流执行"""
        if not self.is_running or self.execution_mode != "workflow":
            return {
                "status": "not_running",
                "module": self.module_name,
                "mode": self.execution_mode,
            }

        if self.current_task:
            self._workflow_stop_requested = True
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass

        # _run_workflow finally 已完成清理和广播，此处仅兜底
        self.workflow_executor = None
        self.execution_mode = "plugin"

        self.logger.info(f"模块的工作流程停止 {self.module_name}")
        return {"status": "stopped", "module": self.module_name}

    async def _run_workflow(self, workflow_id: str) -> None:
        """执行工作流任务（后台Task）。"""

        result: Optional[TaskResult] = None

        try:
            if self.workflow_executor is None:
                result = TaskResult.fail("workflow_not_loaded", error="workflow_executor is None")
                return

            await self.workflow_executor.execute()
            result = TaskResult.ok("completed", data={"workflow_id": workflow_id})
            self.logger.info(f"工作流程已完成 {self.module_name}")

        except asyncio.CancelledError:
            result = TaskResult.cancelled("cancelled")
            self.logger.info(f"工作流任务已取消 {self.module_name}")
            raise

        except Exception as e:
            self.logger.error(f"工作流执行错误: {e}", exc_info=True)
            result = TaskResult.fail("workflow_error", error=str(e), data={"workflow_id": workflow_id})

        finally:
            was_stop_requested = self._workflow_stop_requested
            self._workflow_stop_requested = False
            self.last_result = result
            self.is_running = False
            self.execution_mode = "plugin"
            self.current_task = None
            self.workflow_executor = None
            terminal_reason = (
                "workflow_stopped" if was_stop_requested else "workflow_finished"
            )
            await self._broadcast_module_status(
                reason=terminal_reason, workflow_id=workflow_id
            )

    async def _broadcast_module_status(
        self, reason: str, workflow_id: Optional[str] = None
    ) -> None:
        """广播模块级状态，供前端同步设备运行态。"""
        if not self.ws_server:
            return

        resolved_workflow_id = workflow_id
        if resolved_workflow_id is None and self.workflow_executor is not None:
            resolved_workflow_id = self.workflow_executor.workflow_data.get("id", "unknown")

        payload: dict = {
            "module_name": self.module_name,
            "is_running": self.is_running,
            "execution_mode": self.execution_mode,
            "workflow_id": resolved_workflow_id,
            "running_workflow_id": (
                resolved_workflow_id
                if self.is_running and self.execution_mode == "workflow"
                else None
            ),
            "reason": reason,
        }
        try:
            await self.ws_server.broadcast("module.status", payload)
        except Exception as e:
            self.logger.warning(f"模块状态广播失败 {self.module_name}: {e}")

    def get_status(self) -> dict:
        """获取当前状态"""
        status: dict = {
            "module": self.module_name,
            "is_running": self.is_running,
            "execution_mode": self.execution_mode,
            "last_result": self.last_result.to_dict() if self.last_result else None,
        }

        if self.execution_mode == "plugin":
            status["current_plugin"] = self.current_plugin.plugin_id if self.current_plugin else None
        elif self.execution_mode == "workflow":
            status["workflow_id"] = (
                self.workflow_executor.workflow_data.get("id", "unknown")
                if self.workflow_executor
                else None
            )

        return status
