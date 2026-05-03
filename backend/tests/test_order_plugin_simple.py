"""订单插件简化测试（无需依赖）"""
import json
import py_compile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def test_manifest_format():
    """测试manifest.json格式"""
    print(">>> 测试 manifest.json 格式...")
    manifest_path = ROOT_DIR / "backend/plugins/order_task/manifest.json"
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    
    required_fields = ["id", "name", "version", "author", "description", "entry_point"]
    for field in required_fields:
        assert field in manifest, f"缺少必需字段: {field}"
    
    assert manifest["id"] == "order-task"
    assert manifest["name"] == "订单任务"
    assert manifest["entry_point"] == "plugin.py:OrderPlugin"
    print(f"✅ manifest.json 格式正确")
    print(f"   插件ID: {manifest['id']}")
    print(f"   插件名称: {manifest['name']}")
    print(f"   版本: {manifest['version']}")

def test_plugin_syntax():
    """测试plugin.py语法"""
    print("\n>>> 测试 plugin.py 语法...")
    plugin_path = ROOT_DIR / "backend/plugins/order_task/plugin.py"
    
    py_compile.compile(str(plugin_path), doraise=True)
    
    # 统计代码行数
    with open(plugin_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
    print(f"✅ plugin.py 语法检查通过")
    print(f"   总行数: {len(lines)}")
    print(f"   代码行数: {len(code_lines)}")

def test_plugin_structure():
    """测试插件类结构"""
    print("\n>>> 测试插件类结构...")
    plugin_path = ROOT_DIR / "backend/plugins/order_task/plugin.py"
    
    with open(plugin_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键类和方法
    assert 'class OrderPlugin(PluginBase):' in content, "未找到 OrderPlugin 类"
    assert 'async def prepare(self):' in content, "未找到 prepare 方法"
    assert 'async def execute(self):' in content, "未找到 execute 方法"
    assert 'async def cleanup(self):' in content, "未找到 cleanup 方法"
    
    # 检查核心业务方法
    assert 'async def order_process(self):' in content, "未找到 order_process 方法"
    assert 'async def _process_pcba(self):' in content, "未找到 _process_pcba 方法"
    assert 'async def _process_manufacture_speedup(self):' in content, "未找到 _process_manufacture_speedup 方法"
    assert 'async def change_talent(self, mode):' in content, "未找到 change_talent 方法"
    
    print("✅ 插件类结构完整")
    print("   核心方法: prepare, execute, cleanup")
    print("   业务方法: order_process, _process_pcba, _process_manufacture_speedup, change_talent")

def test_directory_structure():
    """测试目录结构"""
    print("\n>>> 测试目录结构...")
    plugin_dir = ROOT_DIR / "backend/plugins/order_task"
    
    required_files = ["manifest.json", "plugin.py"]
    for file in required_files:
        file_path = plugin_dir / file
        assert file_path.exists(), f"缺少文件: {file}"
        print(f"✅ {file} 存在")

if __name__ == "__main__":
    print("="*60)
    print("开始测试 order_task 插件迁移...")
    print("="*60)
    
    try:
        test_directory_structure()
        test_manifest_format()
        test_plugin_syntax()
        test_plugin_structure()
        
        print("\n" + "="*60)
        print("🎉 所有测试通过！order_task 插件迁移成功！")
        print("="*60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
