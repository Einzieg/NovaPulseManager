"""WebSocket日志处理器"""
import logging
from typing import Optional


class WebSocketLogHandler(logging.Handler):
    """将日志通过WebSocket推送到前端"""
    
    def __init__(self, ws_server, module_name: str):
        super().__init__()
        self.ws_server = ws_server
        self.module_name = module_name
    
    def emit(self, record):
        try:
            log_entry = {
                "module": self.module_name,
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": record.created
            }
            # 异步广播日志
            import asyncio
            asyncio.create_task(
                self.ws_server.broadcast("log", log_entry)
            )
        except Exception:
            self.handleError(record)