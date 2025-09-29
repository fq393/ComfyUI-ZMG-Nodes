"""
Load Image From URL Node
从URL加载图像的节点，支持本地文件路径和网络URL
"""

import os
import io
import torch
import numpy as np
from PIL import Image, ImageOps
from urllib.parse import urlparse
from urllib.request import urlopen
import requests
from typing import Tuple, Optional

from .config.NodeCategory import NodeCategory


class LoadImageFromUrlNode:
    """
    从URL加载图像的节点
    支持本地文件路径、网络URL等多种图像源
    当URL为空时，返回空白图像
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入图像URL或本地文件路径"
                }),
                "width": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 4096,
                    "step": 8,
                    "display": "number"
                }),
                "height": ("INT", {
                    "default": 512,
                    "min": 64,
                    "max": 4096,
                    "step": 8,
                    "display": "number"
                }),
                "color": ("STRING", {
                    "default": "black",
                    "multiline": False,
                    "placeholder": "空图像颜色 (black/white/red/green/blue 或 #RRGGBB)"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "load_image"
    CATEGORY = NodeCategory.IMAGE
    
    DESCRIPTION = """
从URL加载图像的高级节点

功能特点：
• 支持多种图像源：本地文件路径、HTTP/HTTPS URL
• 自动处理图像格式转换和EXIF旋转
• URL为空时自动生成指定尺寸的空白图像
• 支持自定义空图像的颜色
• 错误处理：加载失败时返回空白图像
• 兼容ComfyUI的图像张量格式

支持的图像格式：
• JPEG、PNG、GIF、BMP、TIFF、WebP等
• 自动转换为RGB格式以确保兼容性

使用场景：
• 从网络加载图像进行处理
• 批量处理本地图像文件
• 作为图像处理流水线的输入源
• 测试和调试时的占位图像
"""
    
    def _pil_to_tensor(self, image: Image.Image) -> torch.Tensor:
        """将PIL图像转换为PyTorch张量"""
        # 确保图像是RGB格式
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # 处理EXIF旋转
        image = ImageOps.exif_transpose(image)
        
        # 转换为numpy数组并归一化到[0,1]
        image_array = np.array(image).astype(np.float32) / 255.0
        
        # 转换为PyTorch张量并添加批次维度
        return torch.from_numpy(image_array).unsqueeze(0)
    
    def _create_empty_image(self, width: int, height: int, color: str) -> Image.Image:
        """创建空白图像"""
        # 解析颜色
        if color.startswith('#'):
            # 十六进制颜色
            try:
                color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            except ValueError:
                color_rgb = (0, 0, 0)  # 默认黑色
        else:
            # 预定义颜色
            color_map = {
                'black': (0, 0, 0),
                'white': (255, 255, 255),
                'red': (255, 0, 0),
                'green': (0, 255, 0),
                'blue': (0, 0, 255),
                'gray': (128, 128, 128),
                'grey': (128, 128, 128)
            }
            color_rgb = color_map.get(color.lower(), (0, 0, 0))
        
        return Image.new('RGB', (width, height), color_rgb)
    
    def _load_image_from_url(self, url: str) -> Optional[Image.Image]:
        """从URL加载图像"""
        try:
            parsed_url = urlparse(url)
            
            if parsed_url.scheme in ('http', 'https'):
                # 网络URL
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
            elif parsed_url.scheme == 'file' or not parsed_url.scheme:
                # 本地文件路径
                file_path = parsed_url.path if parsed_url.scheme == 'file' else url
                if not os.path.exists(file_path):
                    return None
                image = Image.open(file_path)
            else:
                return None
            
            return image
            
        except Exception as e:
            print(f"加载图像失败: {e}")
            return None
    
    def load_image(self, url: str, width: int, height: int, color: str) -> Tuple[torch.Tensor]:
        """
        从URL加载图像
        
        Args:
            url: 图像URL或本地文件路径
            width: 空图像宽度（当URL为空或加载失败时使用）
            height: 空图像高度（当URL为空或加载失败时使用）
            color: 空图像颜色
            
        Returns:
            tuple: 包含图像张量的元组
        """
        # 如果URL为空，直接创建空图像
        if not url or url.strip() == "":
            empty_image = self._create_empty_image(width, height, color)
            tensor = self._pil_to_tensor(empty_image)
            return (tensor,)
        
        # 尝试从URL加载图像
        image = self._load_image_from_url(url.strip())
        
        if image is None:
            # 加载失败，创建空图像
            print(f"无法加载图像，使用空白图像替代: {url}")
            empty_image = self._create_empty_image(width, height, color)
            tensor = self._pil_to_tensor(empty_image)
            return (tensor,)
        
        # 成功加载图像
        tensor = self._pil_to_tensor(image)
        return (tensor,)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LoadImageFromUrlNode": LoadImageFromUrlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromUrlNode": "Load Image From URL"
}