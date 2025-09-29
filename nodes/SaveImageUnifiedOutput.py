import os
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import torch
from PIL import Image, ImageOps
from PIL.PngImagePlugin import PngInfo
from datetime import datetime

import folder_paths
from nodes import SaveImage
from comfy.cli_args import args
from .config.NodeCategory import NodeCategory


class SaveImageUnifiedOutput:
    """
    ComfyUI节点：统一图像保存输出
    
    提供统一的图像保存功能，支持批量保存、元数据嵌入、
    多种图像格式和自定义文件命名规则。
    """

    def __init__(self):
        """初始化图像保存节点"""
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4
        self.logger = logging.getLogger(__name__)

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        定义节点的输入类型
        
        Returns:
            Dict[str, Any]: 输入类型配置
        """
        return {
            "required": {
                "images": ("IMAGE",),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "placeholder": "文件名前缀"
                })
            },
            "optional": {
                "image_format": (["PNG", "JPEG", "WEBP"], {"default": "PNG"}),
                "quality": ("INT", {
                    "default": 95,
                    "min": 1,
                    "max": 100,
                    "step": 1
                }),
                "compress_level": ("INT", {
                    "default": 4,
                    "min": 0,
                    "max": 9,
                    "step": 1
                }),
                "include_timestamp": ("BOOLEAN", {"default": False}),
                "include_metadata": ("BOOLEAN", {"default": True}),
                "custom_subfolder": ("STRING", {
                    "default": "",
                    "placeholder": "自定义子文件夹（可选）"
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
                "unique_id": "UNIQUE_ID"
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("images", "save_info", "file_paths")
    FUNCTION = "save_images"
    CATEGORY = NodeCategory.IMAGE
    
    DESCRIPTION = """
统一的图像保存功能，支持批量保存、元数据嵌入。
提供多种图像格式支持和自定义文件命名规则。
支持PNG、JPEG、WebP格式，可配置压缩质量和保存路径。
"""

    def _generate_filename(self, prefix: str, batch_number: int, counter: int,
                          include_timestamp: bool, image_format: str) -> str:
        """
        生成文件名
        
        Args:
            prefix (str): 文件名前缀
            batch_number (int): 批次编号
            counter (int): 计数器
            include_timestamp (bool): 是否包含时间戳
            image_format (str): 图像格式
            
        Returns:
            str: 生成的文件名
        """
        # 处理批次编号
        filename = prefix.replace("%batch_num%", str(batch_number))
        
        # 添加计数器
        filename += f"_{counter:05d}"
        
        # 添加时间戳
        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename += f"_{timestamp}"
        
        # 添加文件扩展名
        extension = image_format.lower()
        if extension == "jpeg":
            extension = "jpg"
        
        return f"{filename}.{extension}"

    def _create_metadata(self, prompt: Optional[Dict] = None,
                        extra_pnginfo: Optional[Dict] = None,
                        image_format: str = "PNG") -> Optional[PngInfo]:
        """
        创建图像元数据
        
        Args:
            prompt (Optional[Dict]): 提示词信息
            extra_pnginfo (Optional[Dict]): 额外PNG信息
            image_format (str): 图像格式
            
        Returns:
            Optional[PngInfo]: PNG元数据对象（仅PNG格式）
        """
        if image_format.upper() != "PNG":
            return None
        
        metadata = PngInfo()
        
        # 添加基本信息
        metadata.add_text("Software", "ComfyUI-ZMG-Nodes")
        metadata.add_text("Creation Time", datetime.now().isoformat())
        
        # 添加提示词信息
        if prompt is not None:
            metadata.add_text("prompt", json.dumps(prompt))
        
        # 添加额外信息
        if extra_pnginfo is not None:
            for key, value in extra_pnginfo.items():
                metadata.add_text(key, json.dumps(value))
        
        return metadata

    def _tensor_to_pil(self, tensor: torch.Tensor, image_format: str) -> Image.Image:
        """
        将张量转换为PIL图像
        
        Args:
            tensor (torch.Tensor): 输入张量
            image_format (str): 目标图像格式
            
        Returns:
            Image.Image: PIL图像
        """
        # 转换为numpy数组
        numpy_array = 255.0 * tensor.cpu().numpy()
        numpy_array = np.clip(numpy_array, 0, 255).astype(np.uint8)
        
        # 创建PIL图像
        pil_image = Image.fromarray(numpy_array)
        
        # 处理EXIF旋转
        pil_image = ImageOps.exif_transpose(pil_image)
        
        # 根据格式转换颜色模式
        if image_format.upper() == "JPEG":
            if pil_image.mode in ("RGBA", "LA", "P"):
                # JPEG不支持透明度，转换为RGB
                background = Image.new("RGB", pil_image.size, (255, 255, 255))
                if pil_image.mode == "P":
                    pil_image = pil_image.convert("RGBA")
                background.paste(pil_image, mask=pil_image.split()[-1] if pil_image.mode == "RGBA" else None)
                pil_image = background
        elif image_format.upper() == "WEBP":
            # WebP支持RGBA
            if pil_image.mode not in ("RGB", "RGBA"):
                pil_image = pil_image.convert("RGBA")
        
        return pil_image

    def _get_save_path(self, filename_prefix: str, custom_subfolder: str,
                      width: int, height: int) -> Tuple[str, str, int, str, str]:
        """
        获取保存路径信息
        
        Args:
            filename_prefix (str): 文件名前缀
            custom_subfolder (str): 自定义子文件夹
            width (int): 图像宽度
            height (int): 图像高度
            
        Returns:
            Tuple[str, str, int, str, str]: (完整输出文件夹, 文件名, 计数器, 子文件夹, 文件名前缀)
        """
        if custom_subfolder.strip():
            # 使用自定义子文件夹
            output_folder = os.path.join(self.output_dir, custom_subfolder.strip())
            os.makedirs(output_folder, exist_ok=True)
            
            # 生成计数器
            existing_files = [f for f in os.listdir(output_folder) 
                            if f.startswith(filename_prefix) and os.path.isfile(os.path.join(output_folder, f))]
            counter = len(existing_files) + 1
            
            return output_folder, filename_prefix, counter, custom_subfolder.strip(), filename_prefix
        else:
            # 使用默认路径生成逻辑
            return folder_paths.get_save_image_path(
                filename_prefix + self.prefix_append, 
                self.output_dir, 
                width, 
                height
            )

    def save_images(self, images: torch.Tensor, filename_prefix: str,
                   image_format: str = "PNG", quality: int = 95,
                   compress_level: int = 4, include_timestamp: bool = False,
                   include_metadata: bool = True, custom_subfolder: str = "",
                   prompt: Optional[Dict] = None, extra_pnginfo: Optional[Dict] = None,
                   unique_id: Optional[str] = None) -> Tuple[torch.Tensor, str, str]:
        """
        保存图像
        
        Args:
            images (torch.Tensor): 图像张量
            filename_prefix (str): 文件名前缀
            image_format (str): 图像格式
            quality (int): 图像质量（JPEG/WebP）
            compress_level (int): 压缩级别（PNG）
            include_timestamp (bool): 是否包含时间戳
            include_metadata (bool): 是否包含元数据
            custom_subfolder (str): 自定义子文件夹
            prompt (Optional[Dict]): 提示词信息
            extra_pnginfo (Optional[Dict]): 额外PNG信息
            unique_id (Optional[str]): 唯一ID
            
        Returns:
            Tuple[torch.Tensor, str, str]: (原始图像, 保存信息, 文件路径列表)
        """
        try:
            # 获取保存路径
            full_output_folder, filename, counter, subfolder, processed_prefix = self._get_save_path(
                filename_prefix, custom_subfolder, 
                images[0].shape[1], images[0].shape[0]
            )
            
            results = []
            file_paths = []
            saved_count = 0
            
            # 处理每张图像
            for batch_number, image in enumerate(images):
                try:
                    # 生成文件名
                    file_name = self._generate_filename(
                        filename, batch_number, counter + batch_number,
                        include_timestamp, image_format
                    )
                    
                    # 转换为PIL图像
                    pil_image = self._tensor_to_pil(image, image_format)
                    
                    # 创建元数据
                    metadata = None
                    if include_metadata:
                        metadata = self._create_metadata(prompt, extra_pnginfo, image_format)
                    
                    # 构建完整文件路径
                    file_path = os.path.join(full_output_folder, file_name)
                    
                    # 保存图像
                    save_kwargs = {}
                    if image_format.upper() == "PNG":
                        save_kwargs.update({
                            "pnginfo": metadata,
                            "compress_level": compress_level
                        })
                    elif image_format.upper() in ["JPEG", "WEBP"]:
                        save_kwargs["quality"] = quality
                        if image_format.upper() == "WEBP":
                            save_kwargs["lossless"] = quality >= 95
                    
                    pil_image.save(file_path, image_format, **save_kwargs)
                    
                    # 记录结果
                    results.append({
                        "filename": file_name,
                        "subfolder": subfolder,
                        "type": self.type,
                        "format": image_format,
                        "size": f"{pil_image.width}x{pil_image.height}"
                    })
                    
                    file_paths.append(file_path)
                    saved_count += 1
                    
                except Exception as e:
                    self.logger.error(f"保存第 {batch_number + 1} 张图像失败: {str(e)}")
                    continue
            
            # 生成保存信息
            save_info = f"成功保存 {saved_count}/{len(images)} 张图像到 {full_output_folder}"
            if subfolder:
                save_info += f" (子文件夹: {subfolder})"
            save_info += f" | 格式: {image_format}"
            if image_format.upper() == "PNG":
                save_info += f" | 压缩级别: {compress_level}"
            else:
                save_info += f" | 质量: {quality}"
            
            # 返回文件路径列表
            paths_json = json.dumps(file_paths, ensure_ascii=False, indent=2)
            
            return images, save_info, paths_json
            
        except Exception as e:
            self.logger.error(f"图像保存失败: {str(e)}")
            error_info = f"保存失败: {str(e)}"
            return images, error_info, "[]"


NODE_CLASS_MAPPINGS = {
    "😋Save Image Unified Output": SaveImageUnifiedOutput
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "😋Save Image Unified Output": "😋统一图像保存"
}
