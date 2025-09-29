import json
import re
from typing import Dict, Any, Tuple, Union, List
from .config.NodeCategory import NodeCategory


class JsonParserNode:
    """
    ComfyUI节点：JSON解析器
    
    支持解析JSON字符串并通过路径提取特定值。
    支持数组索引、嵌套对象访问和多种输出格式。
    """

    def __init__(self):
        """初始化JSON解析器节点"""
        pass

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        定义节点的输入类型
        
        Returns:
            Dict[str, Any]: 输入类型配置
        """
        return {
            "required": {
                "input_type": (["json", "string"], {"default": "json"}),
                "input_string": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入JSON字符串或普通文本"
                }),
                "json_path": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "JSON路径，如: data.items[0].name"
                }),
                "output_format": (["string", "json", "pretty_json"], {"default": "string"}),
                "default_value": ("STRING", {
                    "default": "",
                    "placeholder": "路径不存在时的默认值"
                })
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("result", "path_info")
    FUNCTION = "parse_input"
    CATEGORY = NodeCategory.DATA
    
    DESCRIPTION = """
高级JSON解析器，支持解析JSON字符串并通过路径提取特定值。
支持数组索引、嵌套对象访问和多种输出格式。
提供强大的路径解析功能，适用于复杂的数据提取场景。
"""

    def _parse_json_path(self, data: Any, path: str) -> Tuple[Any, str]:
        """
        解析JSON路径并提取值
        
        Args:
            data (Any): 要解析的数据
            path (str): JSON路径字符串
            
        Returns:
            Tuple[Any, str]: (提取的值, 路径信息)
        """
        if not path.strip():
            return data, "根路径"
        
        # 分割路径，支持点号和方括号语法
        path_parts = []
        current_part = ""
        in_brackets = False
        
        for char in path:
            if char == '[':
                if current_part:
                    path_parts.append(current_part)
                    current_part = ""
                in_brackets = True
            elif char == ']':
                if in_brackets and current_part:
                    # 处理数组索引
                    try:
                        index = int(current_part)
                        path_parts.append(index)
                    except ValueError:
                        # 如果不是数字，当作字符串键处理
                        path_parts.append(current_part.strip('"\''))
                    current_part = ""
                in_brackets = False
            elif char == '.' and not in_brackets:
                if current_part:
                    path_parts.append(current_part)
                    current_part = ""
            else:
                current_part += char
        
        if current_part:
            path_parts.append(current_part)
        
        # 遍历路径提取值
        current_data = data
        traversed_path = []
        
        for part in path_parts:
            traversed_path.append(str(part))
            
            if isinstance(current_data, dict):
                if part in current_data:
                    current_data = current_data[part]
                else:
                    return None, f"键 '{part}' 在路径 '{'.'.join(traversed_path)}' 中不存在"
            elif isinstance(current_data, list):
                try:
                    index = int(part) if isinstance(part, str) else part
                    if 0 <= index < len(current_data):
                        current_data = current_data[index]
                    else:
                        return None, f"索引 {index} 超出数组范围 (长度: {len(current_data)})"
                except (ValueError, TypeError):
                    return None, f"无效的数组索引: {part}"
            else:
                return None, f"无法在类型 {type(current_data).__name__} 上使用路径 '{part}'"
        
        return current_data, f"成功提取路径: {path}"

    def _format_output(self, data: Any, output_format: str) -> str:
        """
        格式化输出数据
        
        Args:
            data (Any): 要格式化的数据
            output_format (str): 输出格式
            
        Returns:
            str: 格式化后的字符串
        """
        if data is None:
            return ""
        
        if output_format == "json":
            return json.dumps(data, ensure_ascii=False)
        elif output_format == "pretty_json":
            return json.dumps(data, ensure_ascii=False, indent=2)
        else:  # string
            if isinstance(data, (dict, list)):
                return json.dumps(data, ensure_ascii=False)
            return str(data)

    def parse_input(self, input_type: str, input_string: str, json_path: str, 
                   output_format: str, default_value: str) -> Tuple[str, str]:
        """
        解析输入数据
        
        Args:
            input_type (str): 输入类型
            input_string (str): 输入字符串
            json_path (str): JSON路径
            output_format (str): 输出格式
            default_value (str): 默认值
            
        Returns:
            Tuple[str, str]: (解析结果, 路径信息)
        """
        if input_type == "string":
            return (input_string, "直接返回字符串")
        
        # 处理JSON输入
        try:
            parsed_data = json.loads(input_string.strip())
        except json.JSONDecodeError as e:
            return (f"JSON解析错误: {str(e)}", "JSON格式无效")
        except Exception as e:
            return (f"解析异常: {str(e)}", "未知错误")
        
        # 如果没有指定路径，返回整个JSON
        if not json_path.strip():
            formatted_result = self._format_output(parsed_data, output_format)
            return (formatted_result, "返回完整JSON数据")
        
        # 解析JSON路径
        result, path_info = self._parse_json_path(parsed_data, json_path)
        
        if result is None:
            # 使用默认值
            if default_value:
                return (default_value, f"使用默认值: {path_info}")
            else:
                return ("", path_info)
        
        # 格式化输出
        formatted_result = self._format_output(result, output_format)
        return (formatted_result, path_info)


NODE_CLASS_MAPPINGS = {
    "JSON Parser Node": JsonParserNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "JSON Parser Node": "JSON解析器"
}

