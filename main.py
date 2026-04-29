import asyncio
import logging
import os
import subprocess
from pathlib import Path

from backend.core.api.app import create_app
from backend.core.api.server import start_api_server
from backend.core.api.ws_manager import FastApiWebSocketManager
from backend.core.logging.config import configure_logging
from backend.core.websocket.handlers import MessageHandlers
from database.db_session import init_database


def environ_init():
    # 初始化ADB
    adb_path = Path(__file__).resolve().parent / "backend/static/platform-tools"
    os.environ["PATH"] = str(adb_path) + os.pathsep + os.environ["PATH"]
    try:
        subprocess.run(["adb", "version"], check=True)
        logging.info(f"ADB 环境设置成功 {adb_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"ADB 环境变量设置失败: {e}")


async def main():
    """主函数"""
    configure_logging(level=logging.INFO)
    environ_init()
    init_database()

    plugins_dir = Path(__file__).parent / "backend/plugins"

    ws_manager = FastApiWebSocketManager()
    handlers = MessageHandlers(plugins_dir, ws_manager)
    api_app = create_app(handlers, ws_manager)

    host = os.getenv("NOVA_FASTAPI_HOST", "127.0.0.1")
    port = int(os.getenv("NOVA_FASTAPI_PORT", "8765"))

    await start_api_server(api_app, host, port)


if __name__ == "__main__":
    asyncio.run(main())
