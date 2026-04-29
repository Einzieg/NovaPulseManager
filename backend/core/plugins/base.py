"""插件基类"""
from abc import ABC
from typing import Optional
import sys
from pathlib import Path
from backend.core.legacy.TaskBase import TaskBase


class PluginBase(TaskBase, ABC):
    """插件基类,继承TaskBase以保持向后兼容"""

    # 插件元数据
    plugin_id: str = ""
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""

    # 子类覆盖此变量以绑定插件专属配置 Model
    ConfigModel = None

    def __init__(self, target: str):
        super().__init__(target)
        self.enabled = True
        self._plugin_config_cache = None

    @property
    def plugin_config(self):
        if self._plugin_config_cache is None and self.ConfigModel is not None:
            self._plugin_config_cache, _ = self.ConfigModel.get_or_create(
                device=self.device_config
            )
        return self._plugin_config_cache

    async def on_install(self) -> None:
        """插件安装时调用"""
        pass

    async def on_uninstall(self) -> None:
        """插件卸载时调用"""
        pass

    async def on_enable(self) -> None:
        """插件启用时调用"""
        self.enabled = True

    async def on_disable(self) -> None:
        """插件禁用时调用"""
        self.enabled = False

    def get_metadata(self) -> dict:
        """获取插件元数据"""
        return {
            "plugin_id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "enabled": self.enabled
        }
