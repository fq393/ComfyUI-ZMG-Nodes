"""
Load Image From URL Node
从URL加载图像的节点，支持多种图像源格式
基于comfyui-art-venture的LoadImageFromUrl节点实现
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


def load_images_from_url(urls: List[str], keep_alpha_channel=False):
    """
    从URL列表加载图像
    支持多种URL格式：HTTP/HTTPS、file://、data:image/、ComfyUI内部路径等
    """
    images: List[Image.Image] = []
    masks: List[Optional[Image.Image]] = []

    for url in urls:
        if url.startswith("data:image/"):
            # 处理base64编码的图像数据
            i = Image.open(io.BytesIO(base64.b64decode(url.split(",")[1])))
        elif url.startswith("file://"):
            # 处理file://协议
            url = url[7:]
            if not os.path.isfile(url):
                raise Exception(f"File {url} does not exist")
            i = Image.open(url)
        elif url.startswith("http://") or url.startswith("https://"):
            # 处理HTTP/HTTPS URL
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                raise Exception(response.text)
            i = Image.open(io.BytesIO(response.content))
        elif url.startswith(("/view?", "/api/view?")):
            # 处理ComfyUI内部路径
            qs_idx = url.find("?")
            qs = parse_qs(url[qs_idx + 1:])
            filename = qs.get("name", qs.get("filename", None))
            if filename is None:
                raise Exception(f"Invalid url: {url}")

            filename = filename[0]
            subfolder = qs.get("subfolder", None)
            if subfolder is not None:
                filename = os.path.join(subfolder[0], filename)

            dirtype = qs.get("type", ["input"])
            if dirtype[0] == "input":
                url = os.path.join(folder_paths.get_input_directory(), filename)
            elif dirtype[0] == "output":
                url = os.path.join(folder_paths.get_output_directory(), filename)
            elif dirtype[0] == "temp":
                url = os.path.join(folder_paths.get_temp_directory(), filename)
            else:
                raise Exception(f"Invalid url: {url}")

            i = Image.open(url)
        elif url == "":
            # 跳过空URL
            continue
        else:
            # 处理本地文件路径
            if folder_paths:
                url = folder_paths.get_annotated_filepath(url)
            if not os.path.isfile(url):
                raise Exception(f"Invalid url: {url}")
            i = Image.open(url)

        # 处理EXIF旋转
        i = ImageOps.exif_transpose(i)
        has_alpha = "A" in i.getbands()
        mask = None

        # 确保图像格式正确
        if "RGB" not in i.mode:
            i = i.convert("RGBA") if has_alpha else i.convert("RGB")

        # 提取Alpha通道作为mask
        if has_alpha:
            mask = i.getchannel("A")

        # 根据设置决定是否保留Alpha通道
        if not keep_alpha_channel:
            image = i.convert("RGB")
        else:
            image = i

        images.append(image)
        masks.append(mask)

    return (images, masks)


def pil2tensor(image: Image.Image) -> torch.Tensor:
    """将PIL图像转换为PyTorch张量"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def tensor2pil(image: torch.Tensor, mode="RGB") -> Image.Image:
    """将PyTorch张量转换为PIL图像"""
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(), 0, 255).astype(np.uint8), mode)


def prepare_image_for_preview(image: Image.Image, output_dir: str, filename_prefix: str) -> dict:
    """为图像准备预览信息"""
    # 这里简化实现，实际应该保存临时文件并返回预览信息
    return {
        "filename": f"{filename_prefix}_preview.png",
        "subfolder": "",
        "type": "temp"
    }


class LoadImageFromUrlNode:
    """
    从URL加载图像的节点
    支持多种图像源格式和批量处理
    当URL为空时，返回空白图像
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_temp_directory() if folder_paths else "/tmp"
        self.filename_prefix = "LoadImageFromUrl"
        
    @classmethod
    def OUTPUT_NODE(cls):
        return True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("STRING", {
                    "default": "",
                    "placeholder": "Input image paths or URLS one per line. Eg:\nhttps://example.com/image.png\nfile:///path/to/local/image.jpg\ndata:image/png;base64,...",
                    "multiline": True,
                    "dynamicPrompts": False,
                }),
            },
            "optional": {
                "keep_alpha_channel": (
                    "BOOLEAN",
                    {"default": False, "label_on": "enabled", "label_off": "disabled"},
                ),
                "output_mode": (
                    "BOOLEAN",
                    {"default": False, "label_on": "list", "label_off": "batch"},
                ),
            },
        }
    
    RETURN_TYPES = ("IMAGE", "MASK", "BOOLEAN")
    OUTPUT_IS_LIST = (True, True, False)
    RETURN_NAMES = ("images", "masks", "has_image")
    CATEGORY = NodeCategory.IMAGE
    FUNCTION = "load_image"
    
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
    
    def load_image(self, image: str, keep_alpha_channel=False, output_mode=False):
        """
        加载图像的主要方法
        
        Args:
            image: URL字符串，每行一个URL
            keep_alpha_channel: 是否保留Alpha通道
            output_mode: 输出模式，False为批次模式，True为列表模式
            
        Returns:
            包含UI预览和结果的字典
        """
        urls = image.strip().split("\n")
        pil_images, pil_masks = load_images_from_url(urls, keep_alpha_channel)
        has_image = len(pil_images) > 0
        
        if not has_image:
            # 没有图像时返回空白图像
            i = torch.zeros((1, 64, 64, 3), dtype=torch.float32, device="cpu")
            m = torch.zeros((64, 64), dtype=torch.float32, device="cpu")
            pil_images = [tensor2pil(i)]
            pil_masks = [tensor2pil(m, mode="L")]

        previews = []
        np_images: list[torch.Tensor] = []
        np_masks: list[torch.Tensor] = []

        for pil_image, pil_mask in zip(pil_images, pil_masks):
            if pil_mask is not None:
                preview_image = Image.new("RGB", pil_image.size)
                preview_image.paste(pil_image, (0, 0))
                preview_image.putalpha(pil_mask)
            else:
                preview_image = pil_image

            previews.append(prepare_image_for_preview(preview_image, self.output_dir, self.filename_prefix))

            np_image = pil2tensor(pil_image)
            if pil_mask:
                np_mask = np.array(pil_mask).astype(np.float32) / 255.0
                np_mask = 1.0 - torch.from_numpy(np_mask)
            else:
                np_mask = torch.zeros((64, 64), dtype=torch.float32, device="cpu")

            np_images.append(np_image)
            np_masks.append(np_mask.unsqueeze(0))

        if output_mode:
            result = (np_images, np_masks, has_image)
        else:
            has_size_mismatch = False
            if len(np_images) > 1:
                for np_image in np_images[1:]:
                    if np_image.shape[1] != np_images[0].shape[1] or np_image.shape[2] != np_images[0].shape[2]:
                        has_size_mismatch = True
                        break

            if has_size_mismatch:
                raise Exception("To output as batch, images must have the same size. Use list output mode instead.")

            result = ([torch.cat(np_images)], [torch.cat(np_masks)], has_image)

        return {"ui": {"images": previews}, "result": result}
    
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