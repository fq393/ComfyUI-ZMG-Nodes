import cv2
import numpy as np
from modelscope.pipelines import pipeline
from modelscope.utils.constant import Tasks
from PIL import Image, ImageOps
import torch
import os
import time
import tempfile
import logging
from typing import Tuple, List, Optional
import folder_paths
from .config.NodeCategory import NodeCategory


class OldPhotoColorizationNode:
    """
    ComfyUI节点：老照片上色
    
    使用ModelScope的图像上色模型为黑白照片添加颜色。
    支持批量处理多张图片，自动处理临时文件。
    """

    def __init__(self):
        """初始化老照片上色节点"""
        self.colorizer: Optional[pipeline] = None
        self.input_dir = folder_paths.get_input_directory()
        os.makedirs(self.input_dir, exist_ok=True)
        
        # 设置日志
        self.logger = logging.getLogger(__name__)

    def _initialize_colorizer(self) -> bool:
        """
        延迟初始化上色模型
        
        Returns:
            bool: 初始化是否成功
        """
        if self.colorizer is None:
            try:
                self.colorizer = pipeline(
                    Tasks.image_colorization, 
                    model='damo/cv_unet_image-colorization'
                )
                self.logger.info("上色模型初始化成功")
                return True
            except Exception as e:
                self.logger.error(f"上色模型初始化失败: {str(e)}")
                return False
        return True

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        """
        定义节点的输入类型
        
        Returns:
            dict: 输入类型配置
        """
        return {
            "required": {
                "image": ("IMAGE",),
            },
            "optional": {
                "quality": (["high", "medium", "low"], {"default": "medium"}),
                "preserve_original_size": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("colorized_image", "process_info")
    FUNCTION = "colorize_images"
    CATEGORY = NodeCategory.IMAGE
    
    DESCRIPTION = """
使用ModelScope的AI上色技术为黑白照片添加颜色。
支持批量处理多张图片，提供多种质量级别选择。
自动处理临时文件，延迟模型加载优化性能。
"""

    def _tensor_to_pil(self, tensor: torch.Tensor) -> Image.Image:
        """
        将PyTorch张量转换为PIL图像
        
        Args:
            tensor (torch.Tensor): 输入张量
            
        Returns:
            Image.Image: PIL图像
        """
        # 确保张量在CPU上
        if tensor.is_cuda:
            tensor = tensor.cpu()
        
        # 移除批次维度并转换为numpy
        if tensor.dim() == 4:
            tensor = tensor.squeeze(0)
        
        numpy_array = tensor.numpy()
        
        # 转换为[0, 255]范围的uint8
        if numpy_array.max() <= 1.0:
            numpy_array = (numpy_array * 255).astype(np.uint8)
        else:
            numpy_array = numpy_array.astype(np.uint8)
        
        # 确保是HWC格式
        if numpy_array.shape[0] == 3:  # CHW -> HWC
            numpy_array = np.transpose(numpy_array, (1, 2, 0))
        
        return Image.fromarray(numpy_array)

    def _pil_to_tensor(self, pil_image: Image.Image) -> torch.Tensor:
        """
        将PIL图像转换为PyTorch张量
        
        Args:
            pil_image (Image.Image): PIL图像
            
        Returns:
            torch.Tensor: PyTorch张量
        """
        # 转换为RGB模式
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # 处理EXIF旋转信息
        pil_image = ImageOps.exif_transpose(pil_image)
        
        # 转换为numpy数组并归一化
        numpy_array = np.array(pil_image, dtype=np.float32) / 255.0
        
        # 转换为张量并添加批次维度
        tensor = torch.from_numpy(numpy_array).unsqueeze(0)
        
        return tensor

    def _colorize_single_image(self, pil_image: Image.Image, quality: str) -> Tuple[Image.Image, str]:
        """
        对单张图片进行上色处理
        
        Args:
            pil_image (Image.Image): 输入的PIL图像
            quality (str): 处理质量
            
        Returns:
            Tuple[Image.Image, str]: (上色后的图像, 处理信息)
        """
        original_size = pil_image.size
        
        # 根据质量设置调整图像大小
        if quality == "high":
            max_size = 1024
        elif quality == "medium":
            max_size = 512
        else:  # low
            max_size = 256
        
        # 调整图像大小以提高处理速度
        if max(original_size) > max_size:
            ratio = max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_input:
            input_path = temp_input.name
            pil_image.save(input_path, 'JPEG', quality=95)
        
        try:
            # 执行上色
            result = self.colorizer(input_path)
            
            if 'output_img' in result:
                # 处理输出图像
                output_img = result['output_img']
                
                # 转换BGR到RGB
                if len(output_img.shape) == 3 and output_img.shape[2] == 3:
                    output_img = cv2.cvtColor(output_img, cv2.COLOR_BGR2RGB)
                
                colorized_image = Image.fromarray(output_img)
                
                # 如果需要，恢复原始尺寸
                if colorized_image.size != original_size:
                    colorized_image = colorized_image.resize(original_size, Image.Resampling.LANCZOS)
                
                process_info = f"上色成功 - 原始尺寸: {original_size}, 质量: {quality}"
                return colorized_image, process_info
            else:
                return pil_image, "上色失败：模型未返回有效结果"
                
        except Exception as e:
            self.logger.error(f"上色处理失败: {str(e)}")
            return pil_image, f"上色失败: {str(e)}"
        finally:
            # 清理临时文件
            if os.path.exists(input_path):
                os.remove(input_path)

    def colorize_images(self, image: torch.Tensor, quality: str = "medium", 
                       preserve_original_size: bool = True) -> Tuple[torch.Tensor, str]:
        """
        对图像进行上色处理
        
        Args:
            image (torch.Tensor): 输入图像张量
            quality (str): 处理质量
            preserve_original_size (bool): 是否保持原始尺寸
            
        Returns:
            Tuple[torch.Tensor, str]: (上色后的图像张量, 处理信息)
        """
        # 初始化模型
        if not self._initialize_colorizer():
            error_msg = "模型初始化失败"
            # 返回原始图像和错误信息
            return image, error_msg
        
        try:
            output_images = []
            process_infos = []
            
            # 处理批次中的每张图像
            for i in range(image.shape[0]):
                single_image = image[i]
                
                # 转换为PIL图像
                pil_image = self._tensor_to_pil(single_image)
                
                # 执行上色
                colorized_pil, info = self._colorize_single_image(pil_image, quality)
                
                # 转换回张量
                colorized_tensor = self._pil_to_tensor(colorized_pil)
                output_images.append(colorized_tensor)
                process_infos.append(f"图像 {i+1}: {info}")
            
            # 合并所有处理后的图像
            result_tensor = torch.cat(output_images, dim=0)
            combined_info = " | ".join(process_infos)
            
            return result_tensor, combined_info
            
        except Exception as e:
            self.logger.error(f"批量上色处理失败: {str(e)}")
            return image, f"处理失败: {str(e)}"


NODE_CLASS_MAPPINGS = {
    "😋Old Photo Colorization Node": OldPhotoColorizationNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "😋Old Photo Colorization Node": "😋老照片上色"
}
