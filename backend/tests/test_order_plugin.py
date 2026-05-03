"""订单插件测试"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.core.plugins.manager import PluginManager


def test_order_plugin_discovery():
    """测试订单插件能否被发现"""
    manager = PluginManager(ROOT_DIR / "backend/plugins")
    plugins = {plugin["id"]: plugin for plugin in manager.discover_plugins()}
    
    print("=== 已发现的插件 ===")
    for plugin_id, plugin_info in plugins.items():
        print(f"  - {plugin_id}: {plugin_info.get('name', 'Unknown')}")
    
    assert "order-task" in plugins, "order-task 插件未被发现！"
    print("\n✅ 测试通过：order-task 插件成功被发现")
    
    # 验证插件元数据
    order_plugin = plugins["order-task"]
    assert order_plugin["name"] == "订单任务"
    assert order_plugin["version"] == "1.0.0"
    assert order_plugin["author"] == "Nova Pulse Manager"
    print("✅ 测试通过：插件元数据验证成功")


def test_order_plugin_manifest():
    """测试manifest.json格式正确性"""
    import json
    manifest_path = ROOT_DIR / "backend/plugins/order_task/manifest.json"
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    required_fields = ["id", "name", "version", "author", "description", "entry_point"]
    for field in required_fields:
        assert field in manifest, f"manifest.json 缺少必需字段: {field}"
    
    assert manifest["entry_point"] == "plugin.py:OrderPlugin"
    print("✅ 测试通过：manifest.json 格式正确")


def test_order_plugin_syntax():
    """测试plugin.py语法正确性"""
    import py_compile
    plugin_path = ROOT_DIR / "backend/plugins/order_task/plugin.py"
    
    py_compile.compile(str(plugin_path), doraise=True)
    print("✅ 测试通过：plugin.py 语法检查成功")


if __name__ == "__main__":
    print("开始测试 order_task 插件...\n")
    
    try:
        test_order_plugin_syntax()
        test_order_plugin_manifest()
        test_order_plugin_discovery()
        
        print("\n" + "="*50)
        print("🎉 所有测试通过！order_task 插件迁移成功！")
        print("="*50)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
