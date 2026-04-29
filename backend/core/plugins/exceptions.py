"""插件系统异常定义"""


class PluginException(Exception):
    """插件系统基础异常"""
    pass


class PluginLoadError(PluginException):
    """插件加载失败"""
    pass


class PluginNotFoundError(PluginException):
    """插件未找到"""
    pass


class PluginManifestError(PluginException):
    """插件manifest.json格式错误"""
    pass


class PluginDependencyError(PluginException):
    """插件依赖错误"""
    pass


class PluginExecutionError(PluginException):
    """插件执行错误"""
    pass