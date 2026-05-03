"""MVP测试脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.scheduler import TaskScheduler
from backend.models import DeviceConfig
from database.db_session import init_database

async def test_scheduler(temp_db_path=None):
    """测试调度器基本功能"""
    init_database(db_path=temp_db_path)
    print("=== 测试TaskScheduler ===")
    
    # 检查是否有设备
    devices = list(DeviceConfig.select())
    if not devices:
        print("警告: 数据库中没有设备,请先创建设备")
        return
    
    device = devices[0]
    print(f"使用设备: {device.name}")
    
    # 创建调度器
    plugins_dir = Path(__file__).parent / "plugins"
    scheduler = TaskScheduler(device.name, plugins_dir)
    
    # 获取状态
    status = scheduler.get_status()
    print(f"初始状态: {status}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_scheduler())
