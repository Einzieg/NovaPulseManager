"""日志管理器 - 兼容性重定向

此文件保持向后兼容性,实际实现已迁移到backend.core.logging.log_manager
"""
# 从新位置导入LogManager
from backend.core.logging import LogManager

__all__ = ["LogManager"]
