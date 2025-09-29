import json
import requests
from typing import Dict, Any, Tuple, Union
from .config.NodeCategory import NodeCategory

# ComfyUI类型定义
any = "*"


class APIRequestNode:
    """
    ComfyUI节点：API请求处理器
    
    支持GET和POST请求，可以处理JSON和表单数据格式。
    提供完整的错误处理和超时机制。
    """

    def __init__(self):
        """初始化API请求节点"""
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
                "api_url": ("STRING", {
                    "default": "https://api.example.com/endpoint",
                    "placeholder": "输入API URL"
                }),
                "request_method": (["GET", "POST", "PUT", "DELETE"], {"default": "GET"}),
                "data_format": (["json", "form"], {"default": "json"}),
                "request_params": ("STRING", {
                    "multiline": True, 
                    "default": "{}",
                    "placeholder": "JSON格式的请求参数"
                }),
                "headers": ("STRING", {
                    "multiline": True, 
                    "default": "{}",
                    "placeholder": "JSON格式的请求头"
                }),
                "timeout": ("INT", {
                    "default": 10,
                    "min": 1,
                    "max": 300,
                    "step": 1
                }),
                "anything": (any, {"widget": False})
            },
        }

    RETURN_TYPES = ("STRING", any)
    RETURN_NAMES = ("response", "passthrough")
    FUNCTION = "make_request"
    CATEGORY = NodeCategory.NETWORK
    
    DESCRIPTION = """
强大的HTTP请求处理器，支持GET、POST、PUT、DELETE方法。
提供完整的错误处理和超时机制，可以处理JSON和表单数据格式。
支持自定义请求头和参数，适用于各种API调用场景。
"""

    def _parse_json_safely(self, json_string: str, default: Dict = None) -> Dict[str, Any]:
        """
        安全解析JSON字符串
        
        Args:
            json_string (str): 要解析的JSON字符串
            default (Dict): 解析失败时的默认值
            
        Returns:
            Dict[str, Any]: 解析后的字典
        """
        if default is None:
            default = {}
            
        try:
            return json.loads(json_string.strip()) if json_string.strip() else default
        except (json.JSONDecodeError, AttributeError):
            return default

    def _validate_url(self, url: str) -> bool:
        """
        验证URL格式
        
        Args:
            url (str): 要验证的URL
            
        Returns:
            bool: URL是否有效
        """
        return url.startswith(('http://', 'https://')) and len(url) > 8

    def make_request(self, api_url: str, request_method: str, data_format: str, 
                    request_params: str, headers: str, timeout: int, anything: Any) -> Tuple[str, Any]:
        """
        执行API请求
        
        Args:
            api_url (str): API地址
            request_method (str): 请求方法
            data_format (str): 数据格式
            request_params (str): 请求参数JSON字符串
            headers (str): 请求头JSON字符串
            timeout (int): 超时时间（秒）
            anything (Any): 透传数据
            
        Returns:
            Tuple[str, Any]: (响应内容, 透传数据)
        """
        # 验证URL
        if not self._validate_url(api_url):
            return ("Error: 无效的URL格式", anything)

        # 解析请求参数和头信息
        params = self._parse_json_safely(request_params)
        header_dict = self._parse_json_safely(headers)
        
        # 设置默认Content-Type
        if data_format == "json" and "Content-Type" not in header_dict:
            header_dict["Content-Type"] = "application/json"

        try:
            # 根据请求方法执行请求
            if request_method == "GET":
                response = requests.get(
                    api_url, 
                    params=params, 
                    headers=header_dict, 
                    timeout=timeout
                )
            elif request_method == "POST":
                if data_format == "json":
                    response = requests.post(
                        api_url, 
                        json=params, 
                        headers=header_dict, 
                        timeout=timeout
                    )
                else:  # form data
                    response = requests.post(
                        api_url, 
                        data=params, 
                        headers=header_dict, 
                        timeout=timeout
                    )
            elif request_method == "PUT":
                if data_format == "json":
                    response = requests.put(
                        api_url, 
                        json=params, 
                        headers=header_dict, 
                        timeout=timeout
                    )
                else:
                    response = requests.put(
                        api_url, 
                        data=params, 
                        headers=header_dict, 
                        timeout=timeout
                    )
            elif request_method == "DELETE":
                response = requests.delete(
                    api_url, 
                    headers=header_dict, 
                    timeout=timeout
                )
            else:
                return (f"Error: 不支持的请求方法 {request_method}", anything)

            # 检查响应状态
            response.raise_for_status()
            
            # 尝试返回格式化的JSON响应，如果不是JSON则返回原始文本
            try:
                json_response = response.json()
                return (json.dumps(json_response, ensure_ascii=False, indent=2), anything)
            except json.JSONDecodeError:
                return (response.text, anything)
                
        except requests.exceptions.Timeout:
            return (f"Error: 请求超时（{timeout}秒）", anything)
        except requests.exceptions.ConnectionError:
            return ("Error: 连接失败，请检查网络或URL", anything)
        except requests.exceptions.HTTPError as e:
            return (f"Error: HTTP错误 {e.response.status_code} - {e.response.text}", anything)
        except requests.exceptions.RequestException as e:
            return (f"Error: 请求异常 - {str(e)}", anything)
        except Exception as e:
            return (f"Error: 未知错误 - {str(e)}", anything)


NODE_CLASS_MAPPINGS = {
    "API Request Node": APIRequestNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "API Request Node": "API请求节点"
}
