"""MVP测试脚本"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.scheduler import TaskScheduler
from backend.models import Module

async def test_scheduler():
    """测试调度器基本功能"""
    print("=== 测试TaskScheduler ===")
    
    # 检查是否有Module
    modules = list(Module.select())
    if not modules:
        print("警告: 数据库中没有Module,请先创建Module")
        return
    
    module = modules[0]
    print(f"使用Module: {module.name}")
    
    # 创建调度器
    plugins_dir = Path(__file__).parent / "plugins"
    scheduler = TaskScheduler(module.name, plugins_dir)
    
    # 获取状态
    status = scheduler.get_status()
    print(f"初始状态: {status}")
    
    print("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_scheduler())