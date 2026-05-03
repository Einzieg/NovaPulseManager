"""插件管理器"""
import json
import logging
from pathlib import Path
from typing import Dict, List
from .base import PluginBase
from .loader import PluginLoader
from .exceptions import PluginNotFoundError, PluginLoadError


class PluginManager:
    """插件管理器,负责插件的发现、加载、卸载和生命周期管理"""
    
    def __init__(self, plugins_dir: Path):
        self.plugins_dir = plugins_dir
        self._loaded_plugins: Dict[str, type] = {}
        self._plugin_metadata: Dict[str, dict] = {}
        self._plugin_dirs: Dict[str, Path] = {}  # 保存插件ID到目录的映射
        self.logger = logging.getLogger(__name__)
    
    def discover_plugins(self) -> List[dict]:
        """发现所有可用插件"""
        plugins = []
        if not self.plugins_dir.exists():
            self.logger.warning(f"Plugins directory not found: {self.plugins_dir}")
            return plugins
        
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir():
                continue
            
            manifest_path = plugin_dir / "manifest.json"
            if not manifest_path.exists():
                continue
            
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    raw_manifest = json.load(f)
                if raw_manifest.get("kind") == "application":
                    continue

                manifest = PluginLoader.load_manifest(plugin_dir)
                plugin_id = manifest["id"]
                self._plugin_metadata[plugin_id] = manifest
                self._plugin_dirs[plugin_id] = plugin_dir  # 保存目录路径
                plugins.append(manifest)
            except Exception as e:
                self.logger.error(f"Failed to load manifest from {plugin_dir}: {e}")
        
        return plugins
    
    def load_plugin(self, plugin_id: str, target: str) -> PluginBase:
        """加载插件"""
        if plugin_id not in self._plugin_metadata:
            raise PluginNotFoundError(f"Plugin {plugin_id} not found")
        
        manifest = self._plugin_metadata[plugin_id]
        plugin_dir = self._plugin_dirs[plugin_id]  # 使用保存的目录路径
        
        try:
            plugin_class = self._loaded_plugins.get(plugin_id)
            if plugin_class is None:
                plugin_class = PluginLoader.load_plugin(plugin_dir, manifest)
                self._loaded_plugins[plugin_id] = plugin_class
            
            plugin_instance = plugin_class(target)
            plugin_instance.plugin_id = manifest["id"]
            plugin_instance.name = manifest["name"]
            plugin_instance.version = manifest["version"]
            plugin_instance.description = manifest.get("description", "")
            plugin_instance.author = manifest.get("author", "")
            
            self.logger.info(f"Plugin {plugin_id} loaded successfully for {target}")
            return plugin_instance
        except Exception as e:
            self.logger.error(f"Failed to load plugin {plugin_id}: {e}")
            raise PluginLoadError(f"Failed to load plugin {plugin_id}: {e}")
    
    def unload_plugin(self, plugin_id: str) -> None:
        """卸载插件"""
        if plugin_id in self._loaded_plugins:
            del self._loaded_plugins[plugin_id]
        self.logger.info(f"Plugin {plugin_id} unloaded")
    
    def get_plugin(self, plugin_id: str):
        """实例不再缓存；保留方法用于旧调用兼容。"""
        return None
    
    def list_loaded_plugins(self) -> List[str]:
        """列出所有已加载的插件"""
        return list(self._loaded_plugins.keys())
