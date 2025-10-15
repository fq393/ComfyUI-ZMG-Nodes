"""
TextToImageNode - 文本转图片节点
将输入的文本转换为图片，支持自定义文字颜色、背景颜色，画布大小自动适应文字内容
支持中文、英文、数字和特殊字符
"""

import torch
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
from .config.NodeCategory import NodeCategory


def pil2tensor(image):
    """将PIL图像转换为tensor"""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def get_available_fonts():
    """获取fonts文件夹中的可用字体列表"""
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建fonts文件夹的相对路径
    font_dir = os.path.join(os.path.dirname(current_dir), "fonts")
    
    available_fonts = ["默认字体"]  # 默认选项
    
    if os.path.exists(font_dir):
        # 支持的字体文件扩展名
        font_extensions = ['.ttf', '.ttc', '.otf', '.woff', '.woff2']
        
        for filename in os.listdir(font_dir):
            if any(filename.lower().endswith(ext) for ext in font_extensions):
                # 移除扩展名作为显示名称
                font_name = os.path.splitext(filename)[0]
                available_fonts.append(font_name)
    
    return available_fonts


def get_font_path(font_name):
    """根据字体名称获取字体文件路径"""
    if font_name == "默认字体":
        return None
    
    # 获取当前文件的目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 构建font文件夹的相对路径
    font_dir = os.path.join(os.path.dirname(current_dir), "fonts")
    
    if os.path.exists(font_dir):
        # 支持的字体文件扩展名
        font_extensions = ['.ttf', '.ttc', '.otf', '.woff', '.woff2']
        
        for filename in os.listdir(font_dir):
            if any(filename.lower().endswith(ext) for ext in font_extensions):
                # 检查文件名（不含扩展名）是否匹配
                if os.path.splitext(filename)[0] == font_name:
                    return os.path.join(font_dir, filename)
    
    # 如果没有找到指定字体，返回None使用默认字体
    return None


def hex_to_rgb(hex_color):
    """将十六进制颜色转换为RGB元组"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    elif len(hex_color) == 3:
        return tuple(int(hex_color[i]*2, 16) for i in range(3))
    else:
        # 默认返回黑色
        return (0, 0, 0)


class TextToImageNode:
    """
    文本转图片节点
    
    功能：
    - 将文本转换为图片
    - 支持自定义文字颜色和背景颜色
    - 画布大小自动适应文字内容
    - 支持中文、英文、数字和特殊字符
    - 可调节字体大小和边距
    """
    
    def __init__(self):
        self.output_dir = tempfile.gettempdir()
        self.filename_prefix = "TextToImage"
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "Hello World\n你好世界",
                    "placeholder": "输入要转换为图片的文本..."
                }),
                "font_name": (get_available_fonts(), {
                    "default": get_available_fonts()[0] if get_available_fonts() else "默认字体"
                }),
                "font_size": ("INT", {
                    "default": 48,
                    "min": 12,
                    "max": 200,
                    "step": 1,
                    "display": "number"
                }),
                "text_color": ("STRING", {
                    "default": "#000000",
                    "placeholder": "文字颜色 (十六进制，如 #000000)"
                }),
                "background_color": ("STRING", {
                    "default": "#FFFFFF",
                    "placeholder": "背景颜色 (十六进制，如 #FFFFFF)"
                }),
                "padding": ("INT", {
                    "default": 20,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "display": "number"
                }),
                "line_spacing": ("FLOAT", {
                    "default": 1.2,
                    "min": 0.5,
                    "max": 3.0,
                    "step": 0.1,
                    "display": "number"
                })
            }
        }
    
    @classmethod
    def OUTPUT_NODE(cls):
        return True
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (False,)
    CATEGORY = NodeCategory.IMAGE
    FUNCTION = "text_to_image"
    
    DESCRIPTION = """
    文本转图片节点 - 将文本转换为图片
    
    功能特性：
    • 支持多行文本输入
    • 自定义文字颜色和背景颜色（十六进制格式）
    • 画布大小自动适应文字内容
    • 支持中文、英文、数字和特殊字符
    • 可调节字体大小、边距和行间距
    • 自动选择系统最佳字体
    
    输入参数：
    • text: 要转换的文本内容（支持多行）
    • font_size: 字体大小（12-200像素）
    • text_color: 文字颜色（十六进制，如 #000000）
    • background_color: 背景颜色（十六进制，如 #FFFFFF）
    • padding: 边距大小（0-100像素）
    • line_spacing: 行间距倍数（0.5-3.0）
    
    输出：
    • image: 生成的图片（IMAGE格式）
    """
    
    def text_to_image(self, text, font_name, font_size, text_color, background_color, padding, line_spacing):
        try:
            # 处理空文本
            if not text or text.strip() == "":
                text = "Empty Text"
            
            # 转换颜色
            text_rgb = hex_to_rgb(text_color)
            bg_rgb = hex_to_rgb(background_color)
            
            # 获取字体
            font_path = get_font_path(font_name)
            try:
                if font_path and os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                else:
                    font = ImageFont.load_default()
            except Exception as e:
                print(f"字体加载失败: {e}, 使用默认字体")
                font = ImageFont.load_default()
            
            # 分割文本为行
            lines = text.split('\n')
            
            # 创建临时图像来测量文本尺寸
            temp_img = Image.new('RGB', (1, 1), bg_rgb)
            temp_draw = ImageDraw.Draw(temp_img)
            
            # 计算每行的尺寸
            line_heights = []
            line_widths = []
            max_width = 0
            
            for line in lines:
                if line.strip() == "":
                    # 空行处理
                    line_width = 0
                    line_height = font_size
                else:
                    # 使用textbbox获取更准确的文本尺寸
                    bbox = temp_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]
                
                line_widths.append(line_width)
                line_heights.append(line_height)
                max_width = max(max_width, line_width)
            
            # 计算总高度
            if line_heights:
                base_line_height = max(line_heights)
                total_height = base_line_height * len(lines)
                # 添加行间距
                if len(lines) > 1:
                    total_height += base_line_height * (line_spacing - 1) * (len(lines) - 1)
            else:
                total_height = font_size
            
            # 计算画布尺寸
            canvas_width = max_width + (padding * 2)
            canvas_height = int(total_height) + (padding * 2)
            
            # 确保最小尺寸
            canvas_width = max(canvas_width, 100)
            canvas_height = max(canvas_height, 50)
            
            # 创建图像
            image = Image.new('RGB', (canvas_width, canvas_height), bg_rgb)
            draw = ImageDraw.Draw(image)
            
            # 绘制文本
            y_offset = padding
            for i, line in enumerate(lines):
                if line.strip() != "":
                    # 计算居中位置
                    x_offset = (canvas_width - line_widths[i]) // 2
                    draw.text((x_offset, y_offset), line, fill=text_rgb, font=font)
                
                # 移动到下一行
                if i < len(lines) - 1:
                    y_offset += int(line_heights[i] * line_spacing)
            
            # 转换为tensor
            image_tensor = pil2tensor(image)
            
            return (image_tensor,)
            
        except Exception as e:
            print(f"TextToImageNode错误: {str(e)}")
            # 创建错误图像
            error_img = Image.new('RGB', (400, 100), (255, 200, 200))
            error_draw = ImageDraw.Draw(error_img)
            error_draw.text((10, 10), f"错误: {str(e)}", fill=(255, 0, 0))
            return (pil2tensor(error_img),)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "TextToImageNode": TextToImageNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "TextToImageNode": "Text To Image"
}