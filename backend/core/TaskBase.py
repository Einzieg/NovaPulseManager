"""TaskBase兼容层 - 已迁移到 backend.core.legacy.TaskBase

此文件保留用于向后兼容。新代码应直接从 backend.core.legacy.TaskBase 导入。
"""
import warnings
from backend.core.legacy.TaskBase import (
    TaskBase,
    WAITING,
    RUNNING,
    SUCCESS,
    FAILED,
    fleet_map
)

warnings.warn(
    "backend.core.TaskBase 已迁移至 backend.core.legacy.TaskBase，"
    "请更新导入路径以避免未来版本中的兼容性问题",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['TaskBase', 'WAITING', 'RUNNING', 'SUCCESS', 'FAILED', 'fleet_map']
