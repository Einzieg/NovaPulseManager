"""WebSocket消息处理器"""
import logging
import json
from functools import wraps
from typing import Dict, Any
from pathlib import Path
from backend.core.scheduler import TaskScheduler
from backend.models import Workflow


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

    def _get_scheduler(self, module_name: str) -> TaskScheduler:
        """获取或创建调度器"""
        if module_name not in self.schedulers:
            self.schedulers[module_name] = TaskScheduler(
                module_name, self.plugins_dir, self.ws_server
            )
        return self.schedulers[module_name]

    @handle_errors
    async def handle_task_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务启动请求"""
        module_name = payload.get("module_name")
        plugin_id = payload.get("plugin_id")

        if not module_name or not plugin_id:
            raise ValueError("Missing module_name or plugin_id")

        scheduler = self._get_scheduler(module_name)
        result = await scheduler.start_plugin(plugin_id)
        return result

    @handle_errors
    async def handle_task_stop(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务停止请求"""
        module_name = payload.get("module_name")

        if not module_name:
            raise ValueError("Missing module_name")

        scheduler = self._get_scheduler(module_name)
        result = await scheduler.stop_plugin()
        return result

    @handle_errors
    async def handle_module_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取设备列表（历史命名：module）。

        兼容：仍返回 key=modules；同时提供 devices 作为同义字段，便于前端逐步迁移。
        """

        from backend.models import DeviceConfig
        from backend.models.CommonConfig import CommonConfig

        modules = []
        for device in DeviceConfig.select().order_by(DeviceConfig.id.asc()):
            scheduler = self.schedulers.get(device.name)
            status = (
                scheduler.get_status()
                if scheduler
                else {"is_running": False, "execution_mode": "plugin"}
            )

            common_cfg, _ = CommonConfig.get_or_create(device=device)

            execution_mode = status.get("execution_mode") or "plugin"
            running_workflow_id = status.get("workflow_id") if execution_mode == "workflow" else None

            modules.append(
                {
                    "id": device.id,
                    "name": device.name,
                    "simulator_index": device.simulator_index,
                    "port": device.port,
                    "is_running": bool(status.get("is_running")),
                    "execution_mode": execution_mode,
                    "current_plugin": status.get("current_plugin"),
                    "running_workflow_id": running_workflow_id,
                    "current_workflow_id": common_cfg.current_workflow_id,
                    "workflow_enabled": bool(common_cfg.workflow_enabled),
                }
            )

        return {"modules": modules, "devices": modules}

    @handle_errors
    async def handle_device_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """新增设备（DeviceConfig + CommonConfig）。"""

        from peewee import IntegrityError
        from backend.models import DeviceConfig
        from backend.models.CommonConfig import CommonConfig

        name = payload.get("name")
        simulator_index = payload.get("simulator_index")
        port = payload.get("port")

        if not name:
            raise ValueError("Missing name")
        if simulator_index is None:
            raise ValueError("Missing simulator_index")
        if port is None:
            raise ValueError("Missing port")

        try:
            device = DeviceConfig.create(
                name=str(name),
                simulator_index=int(simulator_index),
                port=int(port),
            )
        except IntegrityError as e:
            raise ValueError(f"Device name already exists: {name}") from e

        # 保证一对一 CommonConfig
        CommonConfig.get_or_create(device=device)

        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "simulator_index": device.simulator_index,
                "port": device.port,
                "is_running": False,
                "execution_mode": "plugin",
                "current_plugin": None,
                "running_workflow_id": None,
                "current_workflow_id": None,
                "workflow_enabled": False,
            }
        }

    @handle_errors
    async def handle_device_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """编辑设备信息。

        约束：设备运行中禁止改名/改端口/改 simulator_index。
        改名时需同步更新该设备下所有工作流的 module_name 以及 workflow_data JSON 内的 module_name。
        """

        from datetime import datetime
        from peewee import IntegrityError
        from backend.models import DeviceConfig
        from backend.models.CommonConfig import CommonConfig

        device_id = payload.get("device_id")
        name = payload.get("name")
        simulator_index = payload.get("simulator_index")
        port = payload.get("port")

        if device_id is None:
            raise ValueError("Missing device_id")
        if not name:
            raise ValueError("Missing name")
        if simulator_index is None:
            raise ValueError("Missing simulator_index")
        if port is None:
            raise ValueError("Missing port")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise ValueError(f"Device not found: {device_id}")

        old_name = device.name
        new_name = str(name)

        scheduler = self.schedulers.get(old_name)
        if scheduler and scheduler.get_status().get("is_running"):
            raise ValueError("Device is running, cannot update")

        # 更新设备字段
        device.name = new_name
        device.simulator_index = int(simulator_index)
        device.port = int(port)

        try:
            device.save()
        except IntegrityError as e:
            raise ValueError(f"Device name already exists: {new_name}") from e

        # 兜底：确保 CommonConfig 一对一
        common_cfg, _ = CommonConfig.get_or_create(device=device)

        # 改名：同步工作流归属与 JSON 内 module_name
        if old_name != new_name:
            for wf in Workflow.select().where(Workflow.module_name == old_name):
                try:
                    data = json.loads(wf.workflow_data)
                except Exception:
                    data = None

                if isinstance(data, dict):
                    data["module_name"] = new_name
                    wf.workflow_data = json.dumps(data, ensure_ascii=False)

                wf.module_name = new_name
                wf.updated_at = datetime.now()
                wf.save()

            # 清理 scheduler 缓存（key 为旧 name）
            self.schedulers.pop(old_name, None)

            # current_workflow_id 仍然有效（workflow_id 不变），无需改。
        else:
            # 即使未改名，配置变化后也建议清理 scheduler，避免持有旧配置
            self.schedulers.pop(old_name, None)

        return {
            "device": {
                "id": device.id,
                "name": device.name,
                "simulator_index": device.simulator_index,
                "port": device.port,
                "is_running": False,
                "execution_mode": "plugin",
                "current_plugin": None,
                "running_workflow_id": None,
                "current_workflow_id": common_cfg.current_workflow_id,
                "workflow_enabled": bool(common_cfg.workflow_enabled),
            }
        }

    @handle_errors
    async def handle_device_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """删除设备。

        约束：设备运行中禁止删除。
        删除时：软删除（停用）该设备下所有工作流；并清理 scheduler 缓存。
        """

        from datetime import datetime
        from backend.models import DeviceConfig
        from backend.models.CommonConfig import CommonConfig

        device_id = payload.get("device_id")
        if device_id is None:
            raise ValueError("Missing device_id")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise ValueError(f"Device not found: {device_id}")

        scheduler = self.schedulers.get(device.name)
        if scheduler and scheduler.get_status().get("is_running"):
            raise ValueError("Device is running, cannot delete")

        # 停用该设备所有工作流
        now = datetime.now()
        (
            Workflow.update({Workflow.is_active: False, Workflow.updated_at: now})
            .where(Workflow.module_name == device.name)
            .execute()
        )

        # 如果某设备选中了这些工作流（理论上只有当前设备），清空选择
        (
            CommonConfig.update({CommonConfig.current_workflow_id: None, CommonConfig.workflow_enabled: False})
            .where(CommonConfig.device == device.id)
            .execute()
        )

        # 删除配置（CommonConfig 建议显式删除，避免 SQLite 外键未启用导致残留）
        CommonConfig.delete().where(CommonConfig.device == device.id).execute()
        device.delete_instance()

        # 清理 scheduler 缓存
        self.schedulers.pop(device.name, None)

        return {"deleted": True}

    @handle_errors
    async def handle_plugin_list(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取插件列表"""
        from backend.core.plugins import PluginManager
        manager = PluginManager(self.plugins_dir)
        plugins = manager.discover_plugins()

        plugin_list = []
        for manifest in plugins:
            plugin_list.append({
                "id": manifest.get("id"),
                "name": manifest.get("name", manifest.get("id", "Unknown")),
                "description": manifest.get("description", ""),
                "version": manifest.get("version", "1.0.0"),
                "author": manifest.get("author", "Unknown")
            })
        return {"plugins": plugin_list}

    _config_model_cache: dict = {}

    def _resolve_config_model(self, plugin_id: str):
        """通过 plugin_id 解析对应的 ConfigModel 类（带缓存）"""
        if plugin_id in self._config_model_cache:
            return self._config_model_cache[plugin_id]

        from backend.core.plugins import PluginManager
        from backend.core.plugins.loader import PluginLoader

        manager = PluginManager(self.plugins_dir)
        manager.discover_plugins()

        if plugin_id not in manager._plugin_dirs:
            raise ValueError(f"Plugin not found: {plugin_id}")

        plugin_dir = manager._plugin_dirs[plugin_id]
        manifest = manager._plugin_metadata[plugin_id]
        plugin_class = PluginLoader.load_plugin(plugin_dir, manifest)

        if plugin_class.ConfigModel is None:
            raise ValueError(f"Plugin {plugin_id} has no ConfigModel")

        self._config_model_cache[plugin_id] = plugin_class.ConfigModel
        return plugin_class.ConfigModel

    @handle_errors
    async def handle_plugin_config_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """获取指定插件的配置字段和当前值"""
        from backend.models import DeviceConfig
        from peewee import BooleanField, IntegerField, CharField

        device_name = payload.get("device_name")
        plugin_id = payload.get("plugin_id")
        if not device_name or not plugin_id:
            raise ValueError("Missing device_name or plugin_id")

        device = DeviceConfig.get_or_none(DeviceConfig.name == device_name)
        if not device:
            raise ValueError(f"Device not found: {device_name}")

        ConfigModel = self._resolve_config_model(plugin_id)
        instance, _ = ConfigModel.get_or_create(device=device)

        fields = []
        for name, field in ConfigModel._meta.fields.items():
            if name in ('id', 'device'):
                continue
            field_type = type(field).__name__
            default = field.default
            if callable(default):
                default = None
            fields.append({
                "name": name,
                "type": field_type,
                "value": getattr(instance, name),
                "default": default,
            })

        return {"fields": fields}

    @handle_errors
    async def handle_plugin_config_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """更新指定插件的配置"""
        from backend.models import DeviceConfig

        device_name = payload.get("device_name")
        plugin_id = payload.get("plugin_id")
        config = payload.get("config")
        if not device_name or not plugin_id or config is None:
            raise ValueError("Missing device_name, plugin_id or config")

        device = DeviceConfig.get_or_none(DeviceConfig.name == device_name)
        if not device:
            raise ValueError(f"Device not found: {device_name}")

        ConfigModel = self._resolve_config_model(plugin_id)
        instance, _ = ConfigModel.get_or_create(device=device)

        valid_fields = {
            name for name in ConfigModel._meta.fields if name not in ('id', 'device')
        }
        for key, value in config.items():
            if key in valid_fields:
                setattr(instance, key, value)

        instance.save()
        return {"updated": True}

    @handle_errors
    async def handle_workflow_save(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """保存工作流到数据库"""
        from datetime import datetime

        module_name = payload.get("module_name")
        workflow_data = payload.get("workflow_data")

        if not module_name or not workflow_data:
            raise ValueError("Missing module_name or workflow_data")

        workflow_id = workflow_data.get("id")
        if not workflow_id:
            raise ValueError("workflow_data must contain 'id' field")

        # 规范化 module_name（设备名）写入 workflow_data，确保改名/迁移后一致
        if isinstance(workflow_data, dict):
            workflow_data["module_name"] = module_name

        # 查询或创建工作流记录
        workflow, created = Workflow.get_or_create(
            workflow_id=workflow_id,
            defaults={
                "name": workflow_data.get("name", "Untitled"),
                "description": workflow_data.get("description", ""),
                "module_name": module_name,
                "workflow_data": json.dumps(workflow_data, ensure_ascii=False),
                "is_active": True,
            }
        )

        if not created:
            # 更新现有记录
            workflow.name = workflow_data.get("name", workflow.name)
            workflow.description = workflow_data.get("description", workflow.description)
            workflow.module_name = module_name
            workflow.workflow_data = json.dumps(workflow_data, ensure_ascii=False)
            workflow.updated_at = datetime.now()
            workflow.is_active = True
            workflow.save()

        return {
            "workflow_id": workflow_id,
            "created": created,
            "message": "Workflow saved successfully"
        }

    @handle_errors
    async def handle_workflow_load(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """从数据库加载工作流。

        多工作流模式：
        - 若该设备设置了 current_workflow_id，则优先加载该工作流；
        - 否则加载该设备最新更新的 active 工作流；
        - 若不存在则返回空工作流。
        """

        module_name = payload.get("module_name")
        if not module_name:
            raise ValueError("Missing module_name")

        # 先尝试加载当前选中的工作流
        try:
            from backend.models import DeviceConfig
            from backend.models.CommonConfig import CommonConfig

            device = DeviceConfig.get_or_none(DeviceConfig.name == module_name)
            if device is not None:
                common_cfg, _ = CommonConfig.get_or_create(device=device)

                preferred_id = common_cfg.current_workflow_id
                if preferred_id:
                    preferred = (
                        Workflow.select()
                        .where(
                            Workflow.workflow_id == preferred_id,
                            Workflow.module_name == module_name,
                            Workflow.is_active == True,
                        )
                        .get()
                    )

                    return {
                        "workflow_id": preferred.workflow_id,
                        "workflow_data": json.loads(preferred.workflow_data),
                    }
        except Workflow.DoesNotExist:
            pass
        except Exception:
            # 任何异常都降级到“加载最新”逻辑
            pass

        try:
            # 查询module的最新工作流(按updated_at倒序)
            workflow = (
                Workflow.select()
                .where(Workflow.module_name == module_name, Workflow.is_active == True)
                .order_by(Workflow.updated_at.desc())
                .get()
            )

            return {
                "workflow_id": workflow.workflow_id,
                "workflow_data": json.loads(workflow.workflow_data)
            }
        except Workflow.DoesNotExist:
            # 返回空工作流而不是抛出异常
            self.logger.info(f"No workflow found for module {module_name}, returning empty workflow")
            return {
                "workflow_id": None,
                "workflow_data": {
                    "nodes": [],
                    "edges": []
                }
            }

    @handle_errors
    async def handle_workflow_start(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """启动工作流执行"""

        module_name = payload.get("module_name")
        workflow_id = payload.get("workflow_id")

        if not module_name or not workflow_id:
            raise ValueError("Missing module_name or workflow_id")

        # 从数据库加载工作流数据
        try:
            workflow = Workflow.get(
                Workflow.workflow_id == workflow_id,
                Workflow.module_name == module_name,
                Workflow.is_active == True,
            )
            workflow_data = json.loads(workflow.workflow_data)
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} not found")

        # 调用TaskScheduler启动工作流
        scheduler = self._get_scheduler(module_name)
        result = await scheduler.start_workflow(workflow_data)
        return result

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

        module_name = payload.get("module_name")
        if not module_name:
            raise ValueError("Missing module_name")

        workflows = []
        for wf in (
            Workflow.select()
            .where(Workflow.module_name == module_name)
            .order_by(Workflow.updated_at.desc())
        ):
            workflows.append(
                {
                    "workflow_id": wf.workflow_id,
                    "name": wf.name,
                    "description": wf.description,
                    "module_name": wf.module_name,
                    "is_active": bool(wf.is_active),
                    "created_at": wf.created_at.isoformat() if wf.created_at else None,
                    "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
                }
            )

        return {"workflows": workflows}

    @handle_errors
    async def handle_workflow_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """按 workflow_id 获取工作流详情。"""

        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            raise ValueError("Missing workflow_id")

        try:
            wf = Workflow.get(Workflow.workflow_id == workflow_id, Workflow.is_active == True)
            return {"workflow_id": wf.workflow_id, "workflow_data": json.loads(wf.workflow_data)}
        except Workflow.DoesNotExist:
            raise ValueError(f"Workflow {workflow_id} not found")

    @handle_errors
    async def handle_workflow_delete(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """软删除（停用）工作流。"""

        from datetime import datetime
        from backend.models.CommonConfig import CommonConfig

        workflow_id = payload.get("workflow_id")
        if not workflow_id:
            raise ValueError("Missing workflow_id")

        wf = Workflow.get_or_none(Workflow.workflow_id == workflow_id)
        if wf is None:
            return {"deleted": False}

        wf.is_active = False
        wf.updated_at = datetime.now()
        wf.save()

        # 若某设备正在引用该工作流，则清空 current_workflow_id
        (
            CommonConfig.update({CommonConfig.current_workflow_id: None, CommonConfig.workflow_enabled: False})
            .where(CommonConfig.current_workflow_id == workflow_id)
            .execute()
        )

        return {"deleted": True}

    @handle_errors
    async def handle_workflow_set_current(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """设置设备当前工作流（current_workflow_id）。"""

        from backend.models import DeviceConfig
        from backend.models.CommonConfig import CommonConfig

        device_id = payload.get("device_id")
        workflow_id = payload.get("workflow_id")

        if device_id is None:
            raise ValueError("Missing device_id")

        device = DeviceConfig.get_or_none(DeviceConfig.id == int(device_id))
        if device is None:
            raise ValueError(f"Device not found: {device_id}")

        common_cfg, _ = CommonConfig.get_or_create(device=device)

        if workflow_id:
            # 必须属于该设备且处于 active
            wf = Workflow.get_or_none(
                Workflow.workflow_id == workflow_id,
                Workflow.module_name == device.name,
                Workflow.is_active == True,
            )
            if wf is None:
                raise ValueError(f"Workflow not found for device: {workflow_id}")

            common_cfg.current_workflow_id = str(workflow_id)
            common_cfg.workflow_enabled = True
        else:
            common_cfg.current_workflow_id = None
            common_cfg.workflow_enabled = False

        common_cfg.save()

        return {
            "device_id": device.id,
            "module_name": device.name,
            "current_workflow_id": common_cfg.current_workflow_id,
            "workflow_enabled": bool(common_cfg.workflow_enabled),
        }

    @staticmethod
    def _blob_to_bool(v, default: bool = True) -> bool:
        if isinstance(v, (bytes, memoryview)):
            try:
                return bool(int.from_bytes(bytes(v), 'big'))
            except Exception:
                return default
        if isinstance(v, bool):
            return v
        return default

    @handle_errors
    async def handle_config_get(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from backend.models.Config import Config
        cfg, _ = Config.get_or_create(id=1)
        return {
            "dark_mode": self._blob_to_bool(cfg.dark_mode, True),
            "cap_tool": cfg.cap_tool or "MuMu",
            "touch_tool": cfg.touch_tool or "MaaTouch",
            "email": cfg.email,
            "password": cfg.password,
            "receiver": cfg.receiver,
        }

    @handle_errors
    async def handle_config_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from backend.models.Config import Config
        cfg, _ = Config.get_or_create(id=1)
        allowed = {"dark_mode", "cap_tool", "touch_tool", "email", "password", "receiver"}
        for key, value in payload.items():
            if key not in allowed:
                continue
            if key == "dark_mode":
                cfg.dark_mode = int(bool(value)).to_bytes(1, 'big')
            else:
                setattr(cfg, key, value)
        cfg.save()
        return await self.handle_config_get({})
