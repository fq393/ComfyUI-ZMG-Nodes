#!/usr/bin/env python3
"""
测试重构后的__init__.py文件
"""
import sys
import os

# 模拟ComfyUI环境
class MockFolderPaths:
    @staticmethod
    def get_output_directory():
        return '/tmp'

class MockSaveImage:
    pass

class MockArgs:
    disable_metadata = False

sys.modules['folder_paths'] = MockFolderPaths()
sys.modules['comfy_nodes'] = type('MockNodes', (), {'SaveImage': MockSaveImage})()
sys.modules['comfy.cli_args'] = type('MockArgs', (), {'args': MockArgs()})()

# 测试基础节点（不依赖ComfyUI的节点）
basic_nodes = [
    'ApiRequestNode',
    'JsonParserNode', 
    'EmptyImageNode',
    'LoadImageFromUrlNode'
]

print("测试基础节点导入...")
for node_name in basic_nodes:
    try:
        module = __import__(f'nodes.{node_name}', fromlist=[node_name])
        print(f"✓ {node_name} 导入成功")
    except Exception as e:
        print(f"✗ {node_name} 导入失败: {e}")

print("\n测试NODE_CONFIG结构...")
try:
    # 创建NODE_CONFIG
    from nodes.ApiRequestNode import APIRequestNode
    from nodes.JsonParserNode import JsonParserNode
    from nodes.EmptyImageNode import EmptyImageNode
    from nodes.LoadImageFromUrlNode import LoadImageFromUrlNode
    
    NODE_CONFIG = {
        # Network nodes
        "😋API Request Node": {"class": APIRequestNode, "name": "😋API Request Node"},
        
        # Data processing nodes
        "😋JSON Parser Node": {"class": JsonParserNode, "name": "😋JSON Parser Node"},
        
        # Image processing nodes
        "LoadImageFromUrlNode": {"class": LoadImageFromUrlNode, "name": "LoadImageFromUrlNode"},
        
        # Utility nodes
        "😋Empty Image Node": {"class": EmptyImageNode, "name": "😋Empty Image Node"},
    }
    
    NODE_CLASS_MAPPINGS = {k: v["class"] for k, v in NODE_CONFIG.items()}
    NODE_DISPLAY_NAME_MAPPINGS = {k: v["name"] for k, v in NODE_CONFIG.items()}
    
    print(f"✓ NODE_CONFIG 包含 {len(NODE_CONFIG)} 个节点:")
    for key, value in NODE_CONFIG.items():
        print(f"  - {key}: {value['class'].__name__} -> {value['name']}")
        
    print(f"\n✓ NODE_CLASS_MAPPINGS 包含 {len(NODE_CLASS_MAPPINGS)} 个节点")
    print(f"✓ NODE_DISPLAY_NAME_MAPPINGS 包含 {len(NODE_DISPLAY_NAME_MAPPINGS)} 个节点")
    
except Exception as e:
    print(f"✗ NODE_CONFIG 创建失败: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成！")