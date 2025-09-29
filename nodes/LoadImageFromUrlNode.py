"""
Load Image From URL Node
从URL加载图像的节点，支持多种图像源格式
"""

import os
import io
import base64
import torch
import numpy as np
from PIL import Image, ImageOps
from urllib.parse import urlparse, parse_qs
import requests
from typing import Tuple, Optional, List

try:
    import folder_paths
except ImportError:
    folder_paths = None

from .config.NodeCategory import NodeCategory


class LoadImageFromUrlNode:
    """
    从URL加载图像的节点
    支持多种图像源格式和批量处理
    当URL为空时，返回空白图像
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "urls": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "placeholder": "输入图像URL或路径，每行一个。支持格式：\nhttps://example.com/image.png\nfile:///path/to/image.jpg\n\n或使用下方的文件上传按钮"
                })
            },
            "optional": {
                "upload": ("IMAGEUPLOAD", {
                    "image_upload": True
                }),
                "keep_alpha_channel": (
                    "BOOLEAN",
                    {"default": False, "label_on": "保留", "label_off": "移除"}
                ),
                "output_mode": (
                    "BOOLEAN", 
                    {"default": False, "label_on": "列表", "label_off": "批次"}
                ),
                "timeout": ("INT", {
                    "default": 30,
                    "min": 5,
                    "max": 120,
                    "step": 5,
                    "display": "number"
                })
            }
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN")
    RETURN_NAMES = ("images", "masks", "has_images")
    OUTPUT_IS_LIST = (True, True, False)
    FUNCTION = "load_images"
    CATEGORY = NodeCategory.IMAGE
    
    DESCRIPTION = """
从URL加载图像的高级节点 - 支持多种图像源和批量处理

功能特点：
• 支持多种图像源格式：
  - HTTP/HTTPS URL: https://example.com/image.png
  - 本地文件路径: /path/to/image.jpg
  - File协议: file:///path/to/image.jpg
  - Data URI: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
  - ComfyUI内部路径: /view?filename=image.png&type=input
• 多行URL输入，支持批量加载多个图像
• 自动处理图像格式转换和EXIF旋转
• 可选保留Alpha通道（透明度）
• 灵活的输出模式：批次模式或列表模式
• 自定义网络请求超时时间
• 智能错误处理：加载失败时返回空白图像
• 兼容ComfyUI的图像张量格式

支持的图像格式：
• JPEG、PNG、GIF、BMP、TIFF、WebP等
• 自动转换为RGB/RGBA格式以确保兼容性

使用场景：
• 从网络批量加载图像进行处理
• 处理本地图像文件集合
• 作为图像处理流水线的输入源
• 测试和调试时的占位图像
• 处理包含透明度的图像
"""
    
    def _pil_to_tensor(self, image: Image.Image, keep_alpha_channel: bool = False) -> torch.Tensor:
        """将PIL图像转换为PyTorch张量"""
        # 处理EXIF旋转（如果还没有处理过）
        image = ImageOps.exif_transpose(image)
        
        # 根据设置决定目标格式
        if keep_alpha_channel and "A" in image.getbands():
            # 保留Alpha通道，转换为RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
        else:
            # 不保留Alpha通道，转换为RGB
            if image.mode != 'RGB':
                image = image.convert('RGB')
        
        # 转换为numpy数组并归一化到[0,1]
        image_array = np.array(image).astype(np.float32) / 255.0
        
        # 转换为PyTorch张量并添加批次维度
        return torch.from_numpy(image_array).unsqueeze(0)
    

    
    def _load_images_from_urls(self, urls: List[str], timeout: int = 30, keep_alpha_channel: bool = False) -> Tuple[List[Image.Image], List[Optional[Image.Image]]]:
        """从URL列表加载图像"""
        images: List[Image.Image] = []
        masks: List[Optional[Image.Image]] = []
        
        for url in urls:
            url = url.strip()
            if not url:
                continue
                
            try:
                image = self._load_single_image_from_url(url, timeout)
                if image is None:
                    continue
                    
                # 处理EXIF旋转
                image = ImageOps.exif_transpose(image)
                
                # 检查是否有Alpha通道
                has_alpha = "A" in image.getbands()
                mask = None
                
                # 确保图像格式正确
                if "RGB" not in image.mode:
                    image = image.convert("RGBA") if has_alpha else image.convert("RGB")
                
                # 提取Alpha通道作为mask
                if has_alpha:
                    mask = image.getchannel("A")
                
                # 根据设置决定是否保留Alpha通道
                if not keep_alpha_channel and has_alpha:
                    image = image.convert("RGB")
                
                images.append(image)
                masks.append(mask)
                
            except Exception as e:
                print(f"加载图像失败 {url}: {e}")
                continue
        
        return images, masks
    
    def _load_single_image_from_url(self, url: str, timeout: int = 30) -> Optional[Image.Image]:
        """从单个URL加载图像"""
        try:
            if url.startswith("data:image/"):
                # Data URI格式
                try:
                    if "," not in url:
                        print(f"无效的Data URI格式: {url[:100]}...")
                        return None
                    image_data = base64.b64decode(url.split(",")[1])
                    return Image.open(io.BytesIO(image_data))
                except Exception as e:
                    print(f"解析Data URI失败: {e}")
                    return None
                
            elif url.startswith("file://"):
                # File协议
                file_path = url[7:]  # 移除 "file://" 前缀
                if not os.path.isfile(file_path):
                    print(f"文件不存在: {file_path}")
                    return None
                try:
                    return Image.open(file_path)
                except Exception as e:
                    print(f"打开本地文件失败 {file_path}: {e}")
                    return None
                
            elif url.startswith(("http://", "https://")):
                # HTTP/HTTPS URL
                try:
                    print(f"正在下载图像: {url}")
                    response = requests.get(url, timeout=timeout, stream=True)
                    response.raise_for_status()
                    
                    # 检查内容类型
                    content_type = response.headers.get('content-type', '').lower()
                    if content_type and not content_type.startswith('image/'):
                        print(f"警告：内容类型不是图像 ({content_type}): {url}")
                    
                    return Image.open(io.BytesIO(response.content))
                except requests.exceptions.Timeout:
                    print(f"请求超时 ({timeout}秒): {url}")
                    return None
                except requests.exceptions.ConnectionError:
                    print(f"连接失败: {url}")
                    return None
                except requests.exceptions.HTTPError as e:
                    print(f"HTTP错误 {e.response.status_code}: {url}")
                    return None
                except Exception as e:
                    print(f"下载图像失败 {url}: {e}")
                    return None
                
            elif url.startswith(("/view?", "/api/view?")):
                # ComfyUI内部路径
                return self._load_comfyui_internal_image(url)
                
            else:
                # 本地文件路径
                # 尝试使用ComfyUI的路径解析（如果可用）
                if folder_paths:
                    try:
                        file_path = folder_paths.get_annotated_filepath(url)
                    except Exception as e:
                        print(f"ComfyUI路径解析失败，使用原始路径: {e}")
                        file_path = url
                else:
                    file_path = url
                    
                if not os.path.isfile(file_path):
                    print(f"文件不存在: {file_path}")
                    return None
                
                try:
                    return Image.open(file_path)
                except Exception as e:
                    print(f"打开本地文件失败 {file_path}: {e}")
                    return None
                
        except Exception as e:
            print(f"加载图像时发生未知错误 {url}: {e}")
            return None
    
    def _load_comfyui_internal_image(self, url: str) -> Optional[Image.Image]:
        """加载ComfyUI内部图像路径"""
        if not folder_paths:
            print("ComfyUI folder_paths不可用")
            return None
            
        try:
            qs_idx = url.find("?")
            qs = parse_qs(url[qs_idx + 1:])
            
            filename = qs.get("name", qs.get("filename", None))
            if filename is None:
                print(f"无效的URL: {url}")
                return None
            
            filename = filename[0]
            subfolder = qs.get("subfolder", None)
            if subfolder is not None:
                filename = os.path.join(subfolder[0], filename)
            
            dirtype = qs.get("type", ["input"])
            if dirtype[0] == "input":
                file_path = os.path.join(folder_paths.get_input_directory(), filename)
            elif dirtype[0] == "output":
                file_path = os.path.join(folder_paths.get_output_directory(), filename)
            elif dirtype[0] == "temp":
                file_path = os.path.join(folder_paths.get_temp_directory(), filename)
            else:
                print(f"无效的目录类型: {dirtype[0]}")
                return None
            
            return Image.open(file_path)
            
        except Exception as e:
            print(f"加载ComfyUI内部图像失败: {e}")
            return None
    
    def load_images(self, urls: str, upload=None, keep_alpha_channel: bool = False, 
                   output_mode: bool = False, timeout: int = 30) -> Tuple[List[torch.Tensor], List[torch.Tensor], bool]:
        """
        从URL列表或上传文件加载图像
        
        Args:
            urls: 图像URL列表，每行一个
            upload: 上传的图像文件
            keep_alpha_channel: 是否保留Alpha通道
            output_mode: 输出模式，False=批次模式，True=列表模式
            timeout: 网络请求超时时间（秒）
            
        Returns:
            tuple: (图像张量列表, mask张量列表, 是否有图像)
        """
        # 解析URL列表
        url_list = [url.strip() for url in urls.strip().split("\n") if url.strip()]
        
        # 处理上传的文件
        if upload is not None and hasattr(upload, 'get'):
            # 获取上传文件的路径
            upload_path = upload.get('image', None)
            if upload_path and folder_paths:
                # 构建完整的文件路径
                full_path = folder_paths.get_annotated_filepath(upload_path)
                if full_path and os.path.exists(full_path):
                    url_list.append(f"file://{full_path}")
        
        # 如果没有有效的URL或上传文件，返回空结果
        if not url_list:
            return ([], [], False)
        
        # 加载图像
        pil_images, pil_masks = self._load_images_from_urls(url_list, timeout, keep_alpha_channel)
        
        # 检查是否成功加载了图像
        has_images = len(pil_images) > 0
        
        if not has_images:
            # 没有成功加载任何图像，返回空图像
            empty_image = self._create_empty_image(width, height, color)
            image_tensor = self._pil_to_tensor(empty_image, keep_alpha_channel)
            mask_tensor = torch.zeros((height, width), dtype=torch.float32)
            return ([image_tensor], [mask_tensor], False)
        
        # 转换为张量
        image_tensors: List[torch.Tensor] = []
        mask_tensors: List[torch.Tensor] = []
        
        for pil_image, pil_mask in zip(pil_images, pil_masks):
            # 转换图像为张量
            image_tensor = self._pil_to_tensor(pil_image, keep_alpha_channel)
            image_tensors.append(image_tensor)
            
            # 转换mask为张量
            if pil_mask is not None:
                mask_array = np.array(pil_mask).astype(np.float32) / 255.0
                mask_tensor = 1.0 - torch.from_numpy(mask_array)  # 反转mask
            else:
                mask_tensor = torch.zeros((pil_image.height, pil_image.width), dtype=torch.float32)
            
            mask_tensors.append(mask_tensor)
        
        # 根据输出模式处理结果
        if output_mode:
            # 列表模式：返回图像列表
            return (image_tensors, mask_tensors, has_images)
        else:
            # 批次模式：尝试合并为批次
            if len(image_tensors) > 1:
                # 检查尺寸是否一致
                first_shape = image_tensors[0].shape
                has_size_mismatch = any(
                    tensor.shape[1:3] != first_shape[1:3] for tensor in image_tensors[1:]
                )
                
                if has_size_mismatch:
                    print("警告：图像尺寸不一致，自动切换到列表模式")
                    return (image_tensors, mask_tensors, has_images)
                
                # 合并为批次
                batch_images = torch.cat(image_tensors, dim=0)
                batch_masks = torch.stack(mask_tensors, dim=0)
                return ([batch_images], [batch_masks], has_images)
            else:
                 return (image_tensors, mask_tensors, has_images)
    
    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        """验证输入参数"""
        urls = kwargs.get("urls", "")
        timeout = kwargs.get("timeout", 30)
        
        # 验证超时参数
        if not isinstance(timeout, int) or timeout < 5 or timeout > 120:
            return "超时时间必须在5-120秒之间"
        
        # 验证URL格式（基本检查）
        if urls and isinstance(urls, str):
            url_list = [url.strip() for url in urls.strip().split("\n") if url.strip()]
            for url in url_list:
                if len(url) > 2048:  # URL长度限制
                    return f"URL过长（超过2048字符）: {url[:50]}..."
        
        return True
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        """检查输入是否发生变化"""
        # 对于URL输入，我们总是重新加载以确保获取最新内容
        urls = kwargs.get("urls", "")
        if urls and urls.strip():
            # 为网络URL添加时间戳以确保重新加载
            import time
            return str(time.time())
        return kwargs.get("urls", "")


# 节点映射
NODE_CLASS_MAPPINGS = {
    "LoadImageFromUrlNode": LoadImageFromUrlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadImageFromUrlNode": "Load Images From URL"
}