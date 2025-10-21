import json
import requests
from typing import Dict, Any, Tuple, Union
from .config.NodeCategory import NodeCategory

# ComfyUI类型定义
any = "*"


class ElasticsearchUpdateNode:
    """
    ComfyUI节点：Elasticsearch更新处理器
    
    专门用于Elasticsearch的update_by_query操作，支持条件查询和脚本更新。
    提供完整的错误处理和超时机制。
    """

    def __init__(self):
        """初始化Elasticsearch更新节点"""
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
                "es_host": ("STRING", {
                    "default": "http://localhost:9200",
                    "placeholder": "Elasticsearch主机地址"
                }),
                "index_name": ("STRING", {
                    "default": "my-index",
                    "placeholder": "索引名称"
                }),
                "operation_type": (["update_by_query", "update", "delete_by_query"], {"default": "update_by_query"}),
                "document_id": ("STRING", {
                    "default": "",
                    "placeholder": "文档ID（仅update操作需要）"
                }),
                "query": ("STRING", {
                    "multiline": True,
                    "default": '{\n  "match_all": {}\n}',
                    "placeholder": "查询条件（JSON格式）"
                }),
                "script": ("STRING", {
                    "multiline": True,
                    "default": '{\n  "source": "ctx._source.field = params.value",\n  "params": {\n    "value": "new_value"\n  }\n}',
                    "placeholder": "更新脚本（JSON格式）"
                }),
                "pretty": ("BOOLEAN", {"default": True}),
                "timeout": ("INT", {
                    "default": 30,
                    "min": 1,
                    "max": 300,
                    "step": 1
                }),
                "authorization": ("STRING", {
                    "default": "",
                    "placeholder": "认证信息（可选，格式：Basic xxx）"
                }),
                "anything": (any, {"widget": False})
            },
        }

    RETURN_TYPES = ("STRING", "INT", any)
    RETURN_NAMES = ("response", "affected_count", "passthrough")
    FUNCTION = "execute_update"
    CATEGORY = NodeCategory.NETWORK
    
    DESCRIPTION = """
专门用于Elasticsearch更新操作的节点，支持：
- update_by_query: 根据查询条件批量更新文档
- update: 更新指定ID的单个文档
- delete_by_query: 根据查询条件批量删除文档

提供完整的错误处理和超时机制，支持认证和自定义脚本。
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

    def _build_url(self, es_host: str, index_name: str, operation_type: str, 
                   document_id: str = "", pretty: bool = True) -> str:
        """
        构建Elasticsearch请求URL
        
        Args:
            es_host (str): ES主机地址
            index_name (str): 索引名称
            operation_type (str): 操作类型
            document_id (str): 文档ID
            pretty (bool): 是否格式化输出
            
        Returns:
            str: 完整的请求URL
        """
        # 确保主机地址格式正确
        if not es_host.startswith(('http://', 'https://')):
            es_host = f"http://{es_host}"
        
        # 移除末尾的斜杠
        es_host = es_host.rstrip('/')
        
        # 构建URL
        if operation_type == "update" and document_id:
            url = f"{es_host}/{index_name}/_update/{document_id}"
        elif operation_type == "update_by_query":
            url = f"{es_host}/{index_name}/_update_by_query"
        elif operation_type == "delete_by_query":
            url = f"{es_host}/{index_name}/_delete_by_query"
        else:
            url = f"{es_host}/{index_name}/_update_by_query"
        
        if pretty:
            url += "?pretty"
            
        return url

    def _build_request_body(self, operation_type: str, query: str, script: str) -> Dict[str, Any]:
        """
        构建请求体
        
        Args:
            operation_type (str): 操作类型
            query (str): 查询条件
            script (str): 更新脚本
            
        Returns:
            Dict[str, Any]: 请求体
        """
        body = {}
        
        # 解析查询条件
        query_dict = self._parse_json_safely(query, {"match_all": {}})
        
        if operation_type in ["update_by_query", "delete_by_query"]:
            body["query"] = query_dict
            
            if operation_type == "update_by_query":
                # 解析脚本
                script_dict = self._parse_json_safely(script)
                if script_dict:
                    body["script"] = script_dict
        elif operation_type == "update":
            # 单文档更新
            script_dict = self._parse_json_safely(script)
            if script_dict:
                body["script"] = script_dict
        
        return body

    def _extract_affected_count(self, response_data: Dict[str, Any], operation_type: str) -> int:
        """
        从响应中提取受影响的文档数量
        
        Args:
            response_data (Dict): 响应数据
            operation_type (str): 操作类型
            
        Returns:
            int: 受影响的文档数量
        """
        try:
            if operation_type == "update_by_query":
                return response_data.get("updated", 0)
            elif operation_type == "delete_by_query":
                return response_data.get("deleted", 0)
            elif operation_type == "update":
                return 1 if response_data.get("result") == "updated" else 0
            else:
                return 0
        except (AttributeError, KeyError):
            return 0

    def execute_update(self, es_host: str, index_name: str, operation_type: str,
                      document_id: str, query: str, script: str, pretty: bool,
                      timeout: int, authorization: str, anything: Any) -> Tuple[str, int, Any]:
        """
        执行Elasticsearch更新操作
        
        Args:
            es_host (str): ES主机地址
            index_name (str): 索引名称
            operation_type (str): 操作类型
            document_id (str): 文档ID
            query (str): 查询条件JSON字符串
            script (str): 更新脚本JSON字符串
            pretty (bool): 是否格式化输出
            timeout (int): 超时时间（秒）
            authorization (str): 认证信息
            anything (Any): 透传数据
            
        Returns:
            Tuple[str, int, Any]: (响应内容, 受影响文档数, 透传数据)
        """
        try:
            # 构建URL
            url = self._build_url(es_host, index_name, operation_type, document_id, pretty)
            
            # 构建请求体
            request_body = self._build_request_body(operation_type, query, script)
            
            # 构建请求头
            headers = {"Content-Type": "application/json"}
            if authorization.strip():
                headers["Authorization"] = authorization.strip()
            
            # 执行请求
            response = requests.post(
                url,
                json=request_body,
                headers=headers,
                timeout=timeout
            )
            
            # 检查响应状态
            response.raise_for_status()
            
            # 解析响应
            try:
                response_data = response.json()
                affected_count = self._extract_affected_count(response_data, operation_type)
                
                # 格式化响应
                formatted_response = json.dumps(response_data, ensure_ascii=False, indent=2)
                return (formatted_response, affected_count, anything)
                
            except json.JSONDecodeError:
                return (response.text, 0, anything)
                
        except requests.exceptions.Timeout:
            return (f"Error: 请求超时（{timeout}秒）", 0, anything)
        except requests.exceptions.ConnectionError:
            return ("Error: 连接失败，请检查Elasticsearch服务是否运行", 0, anything)
        except requests.exceptions.HTTPError as e:
            error_msg = f"Error: HTTP错误 {e.response.status_code}"
            try:
                error_detail = e.response.json()
                error_msg += f" - {json.dumps(error_detail, ensure_ascii=False, indent=2)}"
            except:
                error_msg += f" - {e.response.text}"
            return (error_msg, 0, anything)
        except requests.exceptions.RequestException as e:
            return (f"Error: 请求异常 - {str(e)}", 0, anything)
        except Exception as e:
            return (f"Error: 未知错误 - {str(e)}", 0, anything)


NODE_CLASS_MAPPINGS = {
    "Elasticsearch Update Node": ElasticsearchUpdateNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Elasticsearch Update Node": "ES更新节点"
}