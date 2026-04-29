"""WebSocket 相关（FastAPI-only）。"""

from .handlers import MessageHandlers, handle_errors

__all__ = ["MessageHandlers", "handle_errors"]
