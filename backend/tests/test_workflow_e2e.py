"""端到端工作流测试 - 验证从保存到执行的完整链路"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.core.websocket.handlers import MessageHandlers
from backend.models import Workflow
from database.db_session import init_database


async def test_workflow_full_cycle(temp_db_path):
    """测试完整的工作流保存-加载-执行周期"""
    init_database(db_path=temp_db_path)
    
    print("=" * 60)
    print("🧪 端到端工作流测试")
    print("=" * 60)
    
    # 初始化
    handlers = MessageHandlers(
        plugins_dir=Path(__file__).parent.parent / "plugins",
        ws_server=None  # 测试环境不需要WebSocket
    )
    
    module_name = "test_module"
    workflow_id = f"workflow_{module_name}_{int(datetime.now().timestamp())}"
    
    print(f"\n📝 测试参数:")
    print(f"   模块名称: {module_name}")
    print(f"   工作流ID: {workflow_id}")
    
    # ============ Step 1: 保存工作流 ============
    print("\n" + "=" * 60)
    print("Step 1: 保存工作流")
    print("=" * 60)
    
    save_payload = {
        "module_name": module_name,
        "workflow_data": {
            "id": workflow_id,
            "name": f"{module_name} Test Workflow",
            "description": "E2E test workflow",
            "module_name": module_name,
            "nodes": [
                {
                    "id": "node1",
                    "plugin_id": "start_task",
                    "position": {"x": 100, "y": 100},
                    "config": {}
                },
                {
                    "id": "node2",
                    "plugin_id": "permanent_task",
                    "position": {"x": 300, "y": 100},
                    "config": {}
                }
            ],
            "edges": [
                {
                    "id": "edge1",
                    "source": "node1",
                    "target": "node2"
                }
            ]
        }
    }
    
    try:
        result = await handlers.handle_workflow_save(save_payload)
        print(f"✅ 保存成功:")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   是否新建: {result['created']}")
        print(f"   消息: {result['message']}")
        assert result["workflow_id"] == workflow_id, "工作流ID不匹配"
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        raise
    
    # ============ Step 2: 加载工作流 ============
    print("\n" + "=" * 60)
    print("Step 2: 加载工作流")
    print("=" * 60)
    
    try:
        load_payload = {"module_name": module_name}
        result = await handlers.handle_workflow_load(load_payload)
        print(f"✅ 加载成功:")
        print(f"   Workflow ID: {result['workflow_id']}")
        print(f"   节点数量: {len(result['workflow_data']['nodes'])}")
        print(f"   边数量: {len(result['workflow_data']['edges'])}")
        
        assert result["workflow_id"] == workflow_id, "加载的工作流ID不匹配"
        assert len(result["workflow_data"]["nodes"]) == 2, "节点数量不正确"
        assert len(result["workflow_data"]["edges"]) == 1, "边数量不正确"
        
        print("\n   节点详情:")
        for node in result["workflow_data"]["nodes"]:
            print(f"   - {node['id']}: {node['plugin_id']}")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        raise
    
    # ============ Step 3: 验证数据库 ============
    print("\n" + "=" * 60)
    print("Step 3: 验证数据库")
    print("=" * 60)
    
    try:
        workflow = Workflow.get(Workflow.workflow_id == workflow_id)
        print(f"✅ 数据库验证成功:")
        print(f"   ID: {workflow.id}")
        print(f"   名称: {workflow.name}")
        print(f"   模块: {workflow.module_name}")
        print(f"   激活状态: {workflow.is_active}")
        print(f"   创建时间: {workflow.created_at}")
        print(f"   更新时间: {workflow.updated_at}")
        
        # 验证JSON数据
        stored_data = json.loads(workflow.workflow_data)
        print(f"\n   存储的数据结构:")
        print(f"   - 包含 'id': {('id' in stored_data)}")
        print(f"   - 包含 'name': {('name' in stored_data)}")
        print(f"   - 包含 'nodes': {('nodes' in stored_data)}")
        print(f"   - 包含 'edges': {('edges' in stored_data)}")
        
        assert stored_data["id"] == workflow_id, "存储的工作流ID不匹配"
    except Workflow.DoesNotExist:
        print(f"❌ 数据库中未找到工作流: {workflow_id}")
        raise
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        raise
    
    # ============ Step 4: 测试更新 ============
    print("\n" + "=" * 60)
    print("Step 4: 测试更新现有工作流")
    print("=" * 60)
    
    try:
        # 添加第三个节点
        save_payload["workflow_data"]["nodes"].append({
            "id": "node3",
            "plugin_id": "radar_task",
            "position": {"x": 500, "y": 100},
            "config": {}
        })
        
        result = await handlers.handle_workflow_save(save_payload)
        print(f"✅ 更新成功:")
        print(f"   是否新建: {result['created']}")
        assert result["created"] == False, "应该是更新而非新建"
        
        # 重新加载验证
        result = await handlers.handle_workflow_load(load_payload)
        assert len(result["workflow_data"]["nodes"]) == 3, "更新后节点数量应为3"
        print(f"   验证: 节点数量已更新为 {len(result['workflow_data']['nodes'])}")
    except Exception as e:
        print(f"❌ 更新失败: {e}")
        raise
    
    # ============ 测试总结 ============
    print("\n" + "=" * 60)
    print("🎉 端到端测试全部通过!")
    print("=" * 60)
    print("\n✅ 验证通过的功能:")
    print("   1. 工作流保存 (创建新记录)")
    print("   2. 工作流加载 (正确的数据结构)")
    print("   3. 数据库持久化 (完整的JSON存储)")
    print("   4. 工作流更新 (更新现有记录)")
    print("\n📊 数据完整性:")
    print("   - 前端发送的数据包含所有必需字段 (id, name, module_name)")
    print("   - 后端正确处理嵌套的 workflow_data 结构")
    print("   - 数据库正确存储和检索 JSON 数据")
    print("\n💡 建议:")
    print("   - 可以继续测试工作流执行逻辑 (需要启动WebSocket服务)")
    print("   - 可以测试节点状态更新推送功能")
    print("\n" + "=" * 60)


async def cleanup_test_data():
    """清理测试数据"""
    try:
        # 删除测试工作流
        deleted = Workflow.delete().where(
            Workflow.module_name == "test_module"
        ).execute()
        print(f"\n🧹 清理完成: 删除了 {deleted} 条测试记录")
    except Exception as e:
        print(f"⚠️  清理失败: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(test_workflow_full_cycle())
        
        # 询问是否清理
        response = input("\n是否清理测试数据? (y/n): ")
        if response.lower() == 'y':
            asyncio.run(cleanup_test_data())
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
