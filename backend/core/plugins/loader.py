"""插件加载器"""
import json
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from .exceptions import PluginLoadError, PluginManifestError
from .base import PluginBase


class PluginLoader:
    """插件加载器,负责解析manifest和加载插件"""
    
    @staticmethod
    def load_manifest(plugin_dir: Path) -> Dict[str, Any]:
        """加载并解析manifest.json"""
        manifest_path = plugin_dir / "manifest.json"
        if not manifest_path.exists():
            raise PluginManifestError(f"manifest.json not found in {plugin_dir}")
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 验证必需字段
            required_fields = ["id", "name", "version", "entry_point"]
            for field in required_fields:
                if field not in manifest:
                    raise PluginManifestError(f"Missing required field: {field}")
            
            return manifest
        except json.JSONDecodeError as e:
            raise PluginManifestError(f"Invalid JSON in manifest.json: {e}")
    
    @staticmethod
    def load_plugin(plugin_dir: Path, manifest: Dict[str, Any]) -> type:
        """加载插件类"""
        entry_point = manifest["entry_point"]
        
        # 解析entry_point: "plugin.py:PluginClass"
        if ":" not in entry_point:
            raise PluginLoadError(f"Invalid entry_point format: {entry_point}")
        
        module_file, class_name = entry_point.split(":", 1)
        module_path = plugin_dir / module_file
        
        if not module_path.exists():
            raise PluginLoadError(f"Plugin module not found: {module_path}")
        
        # 动态加载模块
        module_name = f"plugins.{plugin_dir.name}.{module_file.replace('.py', '')}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Failed to load module spec: {module_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # 获取插件类
        if not hasattr(module, class_name):
            raise PluginLoadError(f"Class {class_name} not found in {module_file}")
        
        plugin_class = getattr(module, class_name)
        
        # 验证是否继承PluginBase
        if not issubclass(plugin_class, PluginBase):
            raise PluginLoadError(f"{class_name} must inherit from PluginBase")
        
        return plugin_class