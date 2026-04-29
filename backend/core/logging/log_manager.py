"""日志管理器 - 重构版本,移除NiceGUI依赖"""
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from backend.core.logging.config import get_json_formatter


class LogManager:
    """日志管理器单例,支持文件日志和WebSocket推送"""
    
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance

    def __init__(self, ws_server=None):
        """
        初始化日志管理器
        
        Args:
            ws_server: WebSocket服务器实例,用于日志推送
        """
        if not hasattr(self, 'initialized'):
            self.loggers = {}
            self.log_dir = Path(os.getcwd()) / 'logs'
            self.log_dir.mkdir(exist_ok=True)
            self.ws_server = ws_server
            self.initialized = True

    def get_logger(self, module_name: str) -> logging.Logger:
        """
        获取指定模块的logger
        
        Args:
            module_name: 模块名称
            
        Returns:
            logging.Logger实例
        """
        if module_name not in self.loggers:
            logger = logging.getLogger(f"task.{module_name}")
            logger.setLevel(logging.INFO)
            logger.propagate = False

            # 移除已存在的处理器,避免重复
            logger.handlers.clear()

            # 配置日志格式（优先 JSON；若未安装 structlog 则回退为普通格式）
            formatter = get_json_formatter()

            # 文件处理器
            log_file = self.log_dir / f"{datetime.now().strftime('%Y-%m-%d')}_{module_name}.log"
            file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            # WebSocket处理器(如果提供了ws_server)
            if self.ws_server:
                from backend.core.logging.websocket_handler import WebSocketLogHandler
                ws_handler = WebSocketLogHandler(self.ws_server, module_name)
                ws_handler.setLevel(logging.INFO)
                ws_handler.setFormatter(formatter)
                logger.addHandler(ws_handler)

            self.loggers[module_name] = logger

        return self.loggers[module_name]

    def log(self, message: str, module_name: str, level: int = logging.INFO):
        """
        输出日志信息,兼容旧接口
        
        Args:
            message: 日志消息
            module_name: 模块名称
            level: 日志级别
        """
        logger = self.get_logger(module_name)
        logger.log(level, message)

    def set_level(self, module_name: str, level: int):
        """
        设置指定模块的日志级别
        
        Args:
            module_name: 模块名称
            level: 日志级别
        """
        logger = self.get_logger(module_name)
        logger.setLevel(level)

    def clear(self):
        """清空所有logger缓存"""
        self.loggers = {}