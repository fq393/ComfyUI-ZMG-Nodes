"""
OSS Upload Node
阿里云OSS上传节点，支持文件、图片、视频、音频等任意类型输入上传
"""

import os
import io
import json
import base64
import hashlib
import mimetypes
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urljoin
import torch
import numpy as np
from PIL import Image
import requests

try:
    import oss2
except ImportError:
    oss2 = None

from .config.NodeCategory import NodeCategory


class OSSConfig:
    """阿里云OSS配置类"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.platform = config_dict.get('platform', 'aliyun-oss-1')
        self.enable_storage = config_dict.get('enable-storage', True)
        self.access_key = config_dict.get('access-key', '')
        self.secret_key = config_dict.get('secret-key', '')
        self.end_point = config_dict.get('end-point', '')
        self.bucket_name = config_dict.get('bucket-name', '')
        self.domain = config_dict.get('domain', '').rstrip('/')
        self.base_path = config_dict.get('base-path', '').strip('/')
        
    def validate(self) -> bool:
        """验证配置是否完整"""
        required_fields = ['access_key', 'secret_key', 'end_point', 'bucket_name']
        return all(getattr(self, field) for field in required_fields)


class OSSUploader:
    """阿里云OSS上传器"""
    
    def __init__(self, config: OSSConfig):
        self.config = config
        self._bucket = None
        
    def _get_bucket(self):
        """获取OSS bucket实例"""
        if self._bucket is None:
            if oss2 is None:
                raise ImportError("请安装oss2库: pip install oss2")
            
            auth = oss2.Auth(self.config.access_key, self.config.secret_key)
            self._bucket = oss2.Bucket(auth, self.config.end_point, self.config.bucket_name)
        return self._bucket
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str = None) -> Dict[str, Any]:
        """上传文件到OSS"""
        try:
            bucket = self._get_bucket()
            
            # 生成文件路径
            file_path = self._generate_file_path(filename)
            
            # 设置内容类型
            if content_type is None:
                content_type, _ = mimetypes.guess_type(filename)
                if content_type is None:
                    content_type = 'application/octet-stream'
            
            # 上传文件
            result = bucket.put_object(file_path, file_data, headers={'Content-Type': content_type})
            
            # 生成访问URL
            file_url = self._generate_file_url(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'file_url': file_url,
                'file_size': len(file_data),
                'content_type': content_type,
                'etag': result.etag,
                'upload_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': '',
                'file_url': '',
                'file_size': 0,
                'content_type': content_type or '',
                'etag': '',
                'upload_time': datetime.now().isoformat()
            }
    
    def _generate_file_path(self, filename: str) -> str:
        """生成文件在OSS中的路径"""
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        
        # 生成基于时间和哈希的唯一文件名
        timestamp = datetime.now().strftime('%Y%m%d/%H%M%S')
        file_hash = hashlib.md5(filename.encode()).hexdigest()[:8]
        unique_filename = f"{file_hash}_{filename}"
        
        # 组合完整路径
        if self.config.base_path:
            return f"{self.config.base_path}/{timestamp}/{unique_filename}"
        else:
            return f"{timestamp}/{unique_filename}"
    
    def _generate_file_url(self, file_path: str) -> str:
        """生成文件访问URL"""
        if self.config.domain:
            return f"{self.config.domain}/{file_path}"
        else:
            return f"https://{self.config.bucket_name}.{self.config.end_point}/{file_path}"


class OSSUploadNode:
    """OSS上传节点"""
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_data": ("*", {"tooltip": "支持任意类型输入：图片、视频、音频、文件等"}),
                "filename": ("STRING", {
                    "default": "upload_file",
                    "tooltip": "上传文件名（不包含扩展名，系统会自动添加）"
                }),
                "access_key": ("STRING", {
                    "default": "TXDnBuS9L0npguDb",
                    "tooltip": "阿里云OSS Access Key"
                }),
                "secret_key": ("STRING", {
                    "default": "HBUrehUjtIHelR0ioXCmNd7QR0poPe",
                    "tooltip": "阿里云OSS Secret Key"
                }),
                "end_point": ("STRING", {
                    "default": "oss-cn-hz-zjgbdst-d01-a.cloud.ops.zrtgcloud.com",
                    "tooltip": "OSS端点地址"
                }),
                "bucket_name": ("STRING", {
                    "default": "ai-portal",
                    "tooltip": "OSS存储桶名称"
                }),
                "domain": ("STRING", {
                    "default": "https://ai-oss.zmg.com.cn:10004",
                    "tooltip": "自定义域名（可选）"
                }),
                "base_path": ("STRING", {
                    "default": "ai-portal",
                    "tooltip": "基础路径前缀"
                })
            },
            "optional": {
                "content_type": ("STRING", {
                    "default": "",
                    "tooltip": "文件MIME类型（留空自动检测）"
                }),
                "enable_upload": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否启用上传功能"
                })
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "BOOLEAN", "STRING")
    RETURN_NAMES = ("file_url", "file_path", "upload_info", "file_size", "upload_success", "error_message")
    CATEGORY = NodeCategory.UTILS
    FUNCTION = "upload_to_oss"
    
    DESCRIPTION = """
阿里云OSS上传节点 - 支持任意类型文件上传

功能特点：
• 支持任意类型输入：
  - 图片张量 (IMAGE)
  - 视频文件 (VIDEO)
  - 音频文件 (AUDIO)
  - 文本数据 (STRING)
  - 二进制文件数据
• 自动文件类型检测和MIME类型设置
• 智能文件路径生成（基于时间戳和哈希）
• 支持自定义域名和基础路径
• 详细的上传结果信息
• 错误处理和状态反馈
• 可配置的上传开关

配置说明：
• Access Key: 阿里云OSS访问密钥
• Secret Key: 阿里云OSS密钥
• End Point: OSS服务端点
• Bucket Name: 存储桶名称
• Domain: 自定义访问域名
• Base Path: 文件存储基础路径

输出信息：
• file_url: 文件访问URL
• file_path: 文件在OSS中的路径
• upload_info: 详细上传信息（JSON格式）
• file_size: 文件大小（字节）
• upload_success: 上传是否成功
• error_message: 错误信息（如有）

使用场景：
• 将ComfyUI生成的图片上传到云存储
• 批量上传处理后的媒体文件
• 为生成内容提供公网访问链接
• 构建云端媒体处理流水线
"""
    
    def upload_to_oss(self, input_data: Any, filename: str, access_key: str, secret_key: str,
                     end_point: str, bucket_name: str, domain: str = "", base_path: str = "",
                     content_type: str = "", enable_upload: bool = True) -> Tuple[str, str, str, int, bool, str]:
        """上传数据到OSS"""
        
        if not enable_upload:
            return ("", "", json.dumps({"message": "上传功能已禁用"}), 0, False, "上传功能已禁用")
        
        try:
            # 创建OSS配置
            config = OSSConfig({
                'access-key': access_key,
                'secret-key': secret_key,
                'end-point': end_point,
                'bucket-name': bucket_name,
                'domain': domain,
                'base-path': base_path
            })
            
            if not config.validate():
                error_msg = "OSS配置不完整，请检查必填字段"
                return ("", "", json.dumps({"error": error_msg}), 0, False, error_msg)
            
            # 转换输入数据为字节
            file_data, actual_filename, detected_content_type = self._convert_input_to_bytes(
                input_data, filename, content_type
            )
            
            # 创建上传器并上传
            uploader = OSSUploader(config)
            result = uploader.upload_file(file_data, actual_filename, detected_content_type)
            
            # 返回结果
            return (
                result.get('file_url', ''),
                result.get('file_path', ''),
                json.dumps(result, ensure_ascii=False, indent=2),
                result.get('file_size', 0),
                result.get('success', False),
                result.get('error', '')
            )
            
        except Exception as e:
            error_msg = f"上传失败: {str(e)}"
            error_result = {
                'success': False,
                'error': error_msg,
                'upload_time': datetime.now().isoformat()
            }
            return ("", "", json.dumps(error_result, ensure_ascii=False, indent=2), 0, False, error_msg)
    
    def _convert_input_to_bytes(self, input_data: Any, filename: str, content_type: str) -> Tuple[bytes, str, str]:
        """将输入数据转换为字节数据"""
        
        # 处理图片张量
        if isinstance(input_data, torch.Tensor):
            if len(input_data.shape) == 4:  # 批次图片 [B, H, W, C]
                # 取第一张图片
                image_tensor = input_data[0]
            elif len(input_data.shape) == 3:  # 单张图片 [H, W, C]
                image_tensor = input_data
            else:
                raise ValueError(f"不支持的张量形状: {input_data.shape}")
            
            # 转换为PIL图片
            if image_tensor.dtype == torch.float32:
                image_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
            else:
                image_array = image_tensor.cpu().numpy()
            
            image = Image.fromarray(image_array)
            
            # 保存为字节流
            buffer = io.BytesIO()
            image_format = 'PNG' if image.mode == 'RGBA' else 'JPEG'
            image.save(buffer, format=image_format)
            file_data = buffer.getvalue()
            
            actual_filename = f"{filename}.{image_format.lower()}"
            detected_content_type = content_type or f"image/{image_format.lower()}"
            
        # 处理字符串数据
        elif isinstance(input_data, str):
            file_data = input_data.encode('utf-8')
            actual_filename = f"{filename}.txt"
            detected_content_type = content_type or "text/plain; charset=utf-8"
            
        # 处理字节数据
        elif isinstance(input_data, bytes):
            file_data = input_data
            actual_filename = filename
            detected_content_type = content_type or "application/octet-stream"
            
        # 处理numpy数组
        elif isinstance(input_data, np.ndarray):
            if len(input_data.shape) == 3:  # 图片数组
                image = Image.fromarray(input_data.astype(np.uint8))
                buffer = io.BytesIO()
                image_format = 'PNG' if input_data.shape[2] == 4 else 'JPEG'
                image.save(buffer, format=image_format)
                file_data = buffer.getvalue()
                actual_filename = f"{filename}.{image_format.lower()}"
                detected_content_type = content_type or f"image/{image_format.lower()}"
            else:
                # 其他数组数据保存为numpy格式
                buffer = io.BytesIO()
                np.save(buffer, input_data)
                file_data = buffer.getvalue()
                actual_filename = f"{filename}.npy"
                detected_content_type = content_type or "application/octet-stream"
                
        # 处理列表和字典
        elif isinstance(input_data, (list, dict)):
            json_str = json.dumps(input_data, ensure_ascii=False, indent=2)
            file_data = json_str.encode('utf-8')
            actual_filename = f"{filename}.json"
            detected_content_type = content_type or "application/json; charset=utf-8"
            
        else:
            # 尝试转换为字符串
            try:
                str_data = str(input_data)
                file_data = str_data.encode('utf-8')
                actual_filename = f"{filename}.txt"
                detected_content_type = content_type or "text/plain; charset=utf-8"
            except Exception:
                raise ValueError(f"不支持的输入数据类型: {type(input_data)}")
        
        return file_data, actual_filename, detected_content_type


# 节点注册
NODE_CLASS_MAPPINGS = {
    "OSSUploadNode": OSSUploadNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OSSUploadNode": "OSS Upload 📤"
}