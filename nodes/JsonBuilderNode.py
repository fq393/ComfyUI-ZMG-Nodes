import json
import re
from typing import Any, Dict, List, Tuple, Union, Optional
from .config.NodeCategory import NodeCategory

from .utils.TypeUtils import ANY_TYPE


class JsonBuilderNode:
    """
    JSON构建器节点 - 支持多个key-value输入和JSON对象合并
    
    功能特性：
    - 支持5个key-value对输入
    - 自动类型识别（字符串、数字、布尔值、JSON对象）
    - 支持合并子JSON对象到父级key
    - 智能JSON解析
    - 格式化输出
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                # 5个key-value对
                "key1": ("STRING", {"default": "", "multiline": False}),
                "value1": ("STRING", {"default": "", "multiline": True}),
                "key2": ("STRING", {"default": "", "multiline": False}),
                "value2": ("STRING", {"default": "", "multiline": True}),
                "key3": ("STRING", {"default": "", "multiline": False}),
                "value3": ("STRING", {"default": "", "multiline": True}),
                "key4": ("STRING", {"default": "", "multiline": False}),
                "value4": ("STRING", {"default": "", "multiline": True}),
                "key5": ("STRING", {"default": "", "multiline": False}),
                "value5": ("STRING", {"default": "", "multiline": True}),
                
                # 子JSON对象合并
                "merge_json": ("STRING", {"default": "", "multiline": True}),
                "merge_to_key": ("STRING", {"default": "", "multiline": False}),
                
                # 输出选项
                "pretty_format": ("BOOLEAN", {"default": True}),
                "sort_keys": ("BOOLEAN", {"default": False}),
                
                # 传递数据
                "passthrough": (ANY_TYPE, {"default": None}),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", ANY_TYPE)
    RETURN_NAMES = ("json_string", "formatted_json", "passthrough")
    FUNCTION = "build_json"
    CATEGORY = NodeCategory.DATA
    
    def parse_value(self, value_str: str) -> Any:
        """
        智能解析值的类型
        
        Args:
            value_str: 输入的值字符串
            
        Returns:
            解析后的值（可能是字符串、数字、布尔值或JSON对象）
        """
        if not value_str or value_str.strip() == "":
            return ""
        
        value_str = value_str.strip()
        
        # 尝试解析为JSON对象或数组
        if (value_str.startswith('{') and value_str.endswith('}')) or \
           (value_str.startswith('[') and value_str.endswith(']')):
            try:
                return json.loads(value_str)
            except json.JSONDecodeError:
                return value_str
        
        # 尝试解析为布尔值
        if value_str.lower() in ['true', 'false']:
            return value_str.lower() == 'true'
        
        # 尝试解析为null
        if value_str.lower() == 'null':
            return None
        
        # 尝试解析为数字
        try:
            # 检查是否为整数
            if '.' not in value_str and 'e' not in value_str.lower():
                return int(value_str)
            else:
                return float(value_str)
        except ValueError:
            pass
        
        # 如果是引号包围的字符串，去掉引号
        if (value_str.startswith('"') and value_str.endswith('"')) or \
           (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]
        
        # 默认返回字符串
        return value_str
    
    def safe_json_parse(self, json_str: str) -> Optional[Dict]:
        """
        安全解析JSON字符串
        
        Args:
            json_str: JSON字符串
            
        Returns:
            解析后的字典对象，失败返回None
        """
        if not json_str or json_str.strip() == "":
            return None
        
        try:
            parsed = json.loads(json_str.strip())
            if isinstance(parsed, dict):
                return parsed
            else:
                return {"data": parsed}
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
    
    def merge_json_objects(self, base_obj: Dict, merge_obj: Dict, target_key: str) -> Dict:
        """
        将子JSON对象合并到父级对象的指定key中
        
        Args:
            base_obj: 基础JSON对象
            merge_obj: 要合并的JSON对象
            target_key: 目标key，如果为空则合并到根级别
            
        Returns:
            合并后的JSON对象
        """
        result = base_obj.copy()
        
        # 确保merge_obj是有效的
        if not isinstance(merge_obj, dict):
            print(f"警告: merge_json不是有效的JSON对象，跳过合并")
            return result
        
        # 处理target_key
        target_key = target_key.strip() if target_key else ""
        
        if target_key:
            # 如果指定了目标key
            if target_key in result:
                # 如果目标key已存在
                if isinstance(result[target_key], dict):
                    # 如果现有值是字典，则合并
                    result[target_key].update(merge_obj)
                else:
                    # 如果现有值不是字典，则替换
                    result[target_key] = merge_obj
            else:
                # 如果目标key不存在，直接设置
                result[target_key] = merge_obj
        else:
            # 如果没有指定目标key，直接合并到根级别
            result.update(merge_obj)
        
        return result
    
    def build_json(self, **kwargs):
        """
        构建JSON对象
        
        Returns:
            Tuple[str, str, Any]: (json_string, formatted_json, passthrough)
        """
        try:
            # 获取参数
            pretty_format = kwargs.get("pretty_format", True)
            sort_keys = kwargs.get("sort_keys", False)
            merge_json = kwargs.get("merge_json", "")
            merge_to_key = kwargs.get("merge_to_key", "")
            passthrough = kwargs.get("passthrough")
            
            # 构建基础JSON对象
            json_obj = {}
            
            # 处理5个key-value对
            for i in range(1, 6):
                key = kwargs.get(f"key{i}", "")
                value = kwargs.get(f"value{i}", "")
                
                if key and key.strip():
                    key = key.strip()
                    parsed_value = self.parse_value(value)
                    json_obj[key] = parsed_value
            
            # 处理子JSON对象合并
            if merge_json and merge_json.strip():
                print(f"调试: 开始处理JSON合并")
                print(f"调试: merge_json = {merge_json[:100]}...")  # 只显示前100个字符
                print(f"调试: merge_to_key = '{merge_to_key}'")
                
                merge_obj = self.safe_json_parse(merge_json)
                if merge_obj is not None:
                    print(f"调试: 成功解析merge_json，包含 {len(merge_obj)} 个键")
                    print(f"调试: 合并前的json_obj = {json_obj}")
                    
                    json_obj = self.merge_json_objects(json_obj, merge_obj, merge_to_key.strip())
                    
                    print(f"调试: 合并后的json_obj = {json_obj}")
                else:
                    print(f"调试: merge_json解析失败")
            else:
                print(f"调试: 跳过JSON合并 (merge_json为空)")
            
            # 生成JSON字符串
            if pretty_format:
                json_string = json.dumps(json_obj, ensure_ascii=False, indent=2, sort_keys=sort_keys)
                formatted_json = json_string
            else:
                json_string = json.dumps(json_obj, ensure_ascii=False, sort_keys=sort_keys)
                formatted_json = json.dumps(json_obj, ensure_ascii=False, indent=2, sort_keys=sort_keys)
            
            return (json_string, formatted_json, passthrough)
            
        except Exception as e:
            error_msg = f"JSON构建错误: {str(e)}"
            print(error_msg)
            
            # 返回错误信息
            error_json = {"error": error_msg, "success": False}
            error_string = json.dumps(error_json, ensure_ascii=False, indent=2)
            
            return (error_string, error_string, passthrough)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "JsonBuilderNode": JsonBuilderNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JsonBuilderNode": "JSON构建器"
}