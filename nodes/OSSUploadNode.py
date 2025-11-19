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
from .utils.TypeUtils import ANY_TYPE


# ============================================================================
# 工具类和函数
# ============================================================================


# 简单的缓存和日志函数实现
def cache(*args, **kwargs):
    """简单的缓存函数占位符"""
    pass


def update_cache(*args, **kwargs):
    """简单的更新缓存函数占位符"""
    pass


def remove_cache(cache_key):
    """简单的移除缓存函数占位符"""
    print(f"清除缓存: {cache_key}")


def log_node_info(node_name, message):
    """简单的节点信息日志函数"""
    print(f"[INFO] {node_name}: {message}")


def log_node_warn(node_name, message):
    """简单的节点警告日志函数"""
    print(f"[WARN] {node_name}: {message}")


# ============================================================================
# OSS上传相关类
# ============================================================================


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
            
            # 上传文件并设置公共读权限
            headers = {
                'Content-Type': content_type,
                'x-oss-object-acl': 'public-read'  # 设置文件为公共读
            }
            result = bucket.put_object(file_path, file_data, headers=headers)
            
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
                "input_data": (ANY_TYPE, {"tooltip": "接受任意类型数据：图片、音频、视频、文本等"}),
                "access_key": ("STRING", {
                    "default": "",
                    "tooltip": "阿里云OSS Access Key（请输入您的密钥）"
                }),
                "secret_key": ("STRING", {
                    "default": "",
                    "tooltip": "阿里云OSS Secret Key（请输入您的密钥）"
                }),
                "end_point": ("STRING", {
                    "default": "",
                    "tooltip": "OSS端点地址（如：oss-cn-hangzhou.aliyuncs.com）"
                }),
                "bucket_name": ("STRING", {
                    "default": "",
                    "tooltip": "OSS存储桶名称（请输入您的bucket名称）"
                }),
                "domain": ("STRING", {
                    "default": "",
                    "tooltip": "自定义域名（可选，如：https://your-domain.com）"
                }),
                "base_path": ("STRING", {
                    "default": "",
                    "tooltip": "基础路径前缀（可选，如：uploads）"
                }),
                "video_fps": ("FLOAT", {
                    "default": 16.0,
                    "min": 1.0,
                    "max": 120.0,
                    "step": 0.1,
                    "tooltip": "视频帧率（当输入多张图片时用于合成视频）"
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
阿里云OSS上传节点 - 支持直接数据输入的文件上传

功能特点：
• 直接数据输入：支持图片张量、视频、音频、文本等多种数据类型
• 多图片自动合成视频：当输入多张图片时，自动合成为视频文件
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
    
    def upload_to_oss(self, access_key: str, secret_key: str,
                     end_point: str, bucket_name: str, domain: str = "", base_path: str = "",
                     video_fps: float = 30.0,
                     input_data: Any = None, content_type: str = "", 
                     enable_upload: bool = True) -> Tuple[str, str, str, int, bool, str]:
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
            
            # 处理数据输入
            if input_data is None:
                error_msg = "必须提供input_data参数"
                return ("", "", json.dumps({"error": error_msg}), 0, False, error_msg)
            
            # 根据输入类型自动生成文件名和后缀
            file_data, actual_filename, detected_content_type = self._convert_input_to_bytes(
                input_data, content_type, video_fps
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
    
    def _images_to_video(self, images: torch.Tensor, fps: float = 30.0) -> bytes:
        """
        将图像列表转换为视频文件
        使用FFmpeg进行视频合成，提供更好的编码器兼容性
        """
        try:
            import cv2
        except ImportError:
            raise ImportError("需要安装opencv-python来支持视频生成功能: pip install opencv-python")
        
        # 确保输入是4D张量 [B, H, W, C]
        if len(images.shape) != 4:
            raise ValueError(f"期望4D张量 [B, H, W, C]，但得到形状: {images.shape}")
        
        batch_size, height, width, channels = images.shape
        print(f"视频合成参数: batch_size={batch_size}, height={height}, width={width}, channels={channels}, fps={fps}")
        
        if batch_size < 2:
            raise ValueError("需要至少2张图片才能生成视频")
        
        # 转换张量为numpy数组，确保数值范围正确
        if images.dtype == torch.float32:
            # 检查数值范围
            min_val, max_val = images.min().item(), images.max().item()
            print(f"输入图片数值范围: {min_val:.3f} - {max_val:.3f}")
            
            if max_val <= 1.0:
                # 假设值在0-1范围内，转换为0-255
                images_np = (images.cpu().numpy() * 255).astype(np.uint8)
            else:
                # 已经是0-255范围，直接转换
                images_np = np.clip(images.cpu().numpy(), 0, 255).astype(np.uint8)
        else:
            images_np = np.clip(images.cpu().numpy(), 0, 255).astype(np.uint8)
        
        print(f"转换后图片数值范围: {images_np.min()} - {images_np.max()}")
        
        # 检查FFmpeg是否可用
        import shutil
        import subprocess
        import time
        
        ffmpeg_path = shutil.which('ffmpeg')
        if not ffmpeg_path:
            # 尝试常见的FFmpeg路径
            possible_paths = [
                '/usr/local/bin/ffmpeg',
                '/usr/bin/ffmpeg',
                '/opt/homebrew/bin/ffmpeg',
                'ffmpeg'
            ]
            for path in possible_paths:
                if shutil.which(path):
                    ffmpeg_path = path
                    break
            
            if not ffmpeg_path:
                print("警告: 未找到FFmpeg，回退到OpenCV方法")
                return self._images_to_video_opencv(images_np, fps, channels, width, height, batch_size)
        
        try:
            # 确保尺寸是偶数（H.264要求）
            width = width if width % 2 == 0 else width - 1
            height = height if height % 2 == 0 else height - 1
            
            # 创建临时目录存储帧
            temp_dir = self._get_temp_dir()
            frames_dir = os.path.join(temp_dir, f"frames_{int(time.time())}")
            os.makedirs(frames_dir, exist_ok=True)
            
            try:
                # 保存所有帧为临时图像文件
                frame_paths = []
                for i in range(batch_size):
                    frame_path = os.path.join(frames_dir, f"frame_{i:06d}.png")
                    
                    frame = images_np[i]
                    if channels == 4:  # RGBA
                        frame_rgb = frame[:, :, :3]  # 只取RGB通道
                    elif channels == 3:  # RGB
                        frame_rgb = frame
                    else:
                        raise ValueError(f"不支持的通道数: {channels}")
                    
                    # 调整尺寸
                    if frame_rgb.shape[:2] != (height, width):
                        frame_rgb = cv2.resize(frame_rgb, (width, height))
                    
                    # 转换为BGR并保存
                    frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
                    cv2.imwrite(frame_path, frame_bgr)
                    frame_paths.append(frame_path)
                
                # 生成输出路径
                output_path = self._create_temp_file(prefix="video_", suffix=".mp4")
                
                # 构建FFmpeg命令
                # 使用图像序列作为输入，输出H.264编码的MP4
                cmd = [
                    ffmpeg_path,
                    '-y',  # 覆盖输出文件
                    '-framerate', str(fps),  # 输入帧率
                    '-i', os.path.join(frames_dir, 'frame_%06d.png'),  # 输入图像序列
                    '-c:v', 'libx264',  # 使用H.264编码器
                    '-pix_fmt', 'yuv420p',  # 像素格式，兼容性最好
                    '-crf', '23',  # 质量控制，23是较好的质量
                    '-preset', 'medium',  # 编码速度预设
                    '-movflags', '+faststart',  # 优化网络播放
                    '-s', f'{width}x{height}',  # 设置输出尺寸
                    output_path
                ]
                
                print(f"执行FFmpeg命令: {' '.join(cmd)}")
                
                # 执行FFmpeg命令
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode != 0:
                    print(f"FFmpeg错误: {result.stderr}")
                    # 尝试使用更兼容的编码器
                    cmd_fallback = [
                        ffmpeg_path,
                        '-y',
                        '-framerate', str(fps),
                        '-i', os.path.join(frames_dir, 'frame_%06d.png'),
                        '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p',
                        '-profile:v', 'baseline',  # 使用baseline profile提高兼容性
                        '-level', '3.0',
                        '-crf', '28',  # 稍微降低质量以提高兼容性
                        '-preset', 'fast',
                        '-movflags', '+faststart',
                        '-s', f'{width}x{height}',
                        output_path
                    ]
                    
                    print(f"尝试兼容性编码: {' '.join(cmd_fallback)}")
                    result = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode != 0:
                        print(f"FFmpeg兼容性编码也失败: {result.stderr}")
                        raise Exception(f"FFmpeg视频编码失败: {result.stderr}")
                
                # 检查输出文件
                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    raise Exception("生成的视频文件为空或不存在")
                
                # 读取生成的视频文件
                with open(output_path, 'rb') as f:
                    video_data = f.read()
                
                print(f"视频合成成功: {output_path}, 大小: {len(video_data)} bytes")
                
                # 清理输出文件
                if os.path.exists(output_path):
                    os.unlink(output_path)
                
                return video_data
                
            finally:
                # 清理临时帧文件
                if os.path.exists(frames_dir):
                    shutil.rmtree(frames_dir)
                    
        except subprocess.TimeoutExpired:
            raise Exception("视频编码超时")
        except Exception as e:
            print(f"FFmpeg视频合成失败: {str(e)}")
            # 回退到OpenCV方法
            return self._images_to_video_opencv(images_np, fps, channels, width, height, batch_size)
    
    def _images_to_video_opencv(self, images_np, fps, channels, width, height, batch_size):
        """
        使用OpenCV进行视频合成的回退方法
        """
        try:
            import cv2
        except ImportError:
            raise ImportError("需要安装opencv-python来支持视频生成功能: pip install opencv-python")
        
        # 确保尺寸是偶数
        width = width if width % 2 == 0 else width - 1
        height = height if height % 2 == 0 else height - 1
        
        # 生成输出路径
        temp_path = self._create_temp_file(prefix="video_", suffix=".mp4")
        
        # 尝试多种编码器，按优先级排序
        codecs = [
            ('mp4v', '.mp4'),  # MPEG-4编码器，兼容性好
            ('XVID', '.avi'),  # Xvid编码器
            ('MJPG', '.avi'),  # Motion JPEG，兼容性最好但文件较大
        ]
        
        for codec, ext in codecs:
            try:
                # 如果指定了特定扩展名，调整输出路径
                if not temp_path.endswith(ext):
                    base_path = os.path.splitext(temp_path)[0]
                    current_output_path = base_path + ext
                else:
                    current_output_path = temp_path
                
                print(f"尝试使用编码器: {codec}")
                
                # 创建VideoWriter对象
                fourcc = cv2.VideoWriter_fourcc(*codec)
                out = cv2.VideoWriter(current_output_path, fourcc, fps, (width, height))
                
                if not out.isOpened():
                    print(f"无法打开编码器: {codec}")
                    continue
                
                # 写入帧
                frames_written = 0
                for i in range(batch_size):
                    try:
                        frame = images_np[i]
                        
                        # 处理图像格式
                        if channels == 4:  # RGBA
                            frame = frame[:, :, :3]  # 只取RGB通道
                        elif channels == 3:  # RGB
                            pass  # 保持原样
                        else:
                            raise ValueError(f"不支持的通道数: {channels}")
                        
                        # 调整尺寸
                        if frame.shape[:2] != (height, width):
                            frame = cv2.resize(frame, (width, height))
                        
                        # 转换为BGR
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                        
                        # 确保数据类型正确
                        if frame_bgr.dtype != np.uint8:
                            frame_bgr = frame_bgr.astype(np.uint8)
                        
                        # 写入帧
                        success = out.write(frame_bgr)
                        if success:
                            frames_written += 1
                        else:
                            print(f"写入第{i}帧失败")
                            
                    except Exception as frame_error:
                        print(f"处理第{i}帧时出错: {str(frame_error)}")
                        continue
                
                # 释放资源
                out.release()
                
                # 检查结果
                if os.path.exists(current_output_path) and os.path.getsize(current_output_path) > 0:
                    print(f"使用{codec}编码器成功创建视频: {current_output_path}")
                    print(f"写入帧数: {frames_written}/{batch_size}")
                    print(f"文件大小: {os.path.getsize(current_output_path)} bytes")
                    
                    # 读取生成的视频文件
                    with open(current_output_path, 'rb') as f:
                        video_data = f.read()
                    
                    # 清理临时文件
                    if os.path.exists(current_output_path):
                        os.unlink(current_output_path)
                    
                    return video_data
                else:
                    print(f"使用{codec}编码器创建的视频文件为空")
                    if os.path.exists(current_output_path):
                        os.remove(current_output_path)
                    
            except Exception as e:
                print(f"使用编码器{codec}时出错: {str(e)}")
                continue
        
        raise Exception("所有视频编码器都失败了，无法创建视频文件")
    
    def _get_temp_dir(self) -> str:
        """获取ComfyUI临时目录路径"""
        # 获取ComfyUI家目录路径
        # 从插件路径 /app/ComfyUI/custom_nodes/ComfyUI-ZMG-Nodes/nodes/OSSUploadNode.py 向上4级找到 /app/ComfyUI
        current_file = os.path.abspath(__file__)
        # 向上4级: nodes -> ComfyUI-ZMG-Nodes -> custom_nodes -> ComfyUI
        comfyui_home = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
        temp_dir = os.path.join(comfyui_home, 'temp')
        
        # 确保临时目录存在
        os.makedirs(temp_dir, exist_ok=True)
        
        return temp_dir
    
    def _create_temp_file(self, prefix: str = "", suffix: str = "") -> str:
        """创建临时文件路径"""
        import uuid
        
        temp_dir = self._get_temp_dir()
        
        # 生成唯一的文件名
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{prefix}{unique_id}{suffix}"
        
        return os.path.join(temp_dir, filename)

    def _generate_random_filename(self, extension: str = "") -> str:
        """生成随机文件名"""
        import uuid
        import time
        
        # 生成基于时间戳和UUID的随机名
        timestamp = str(int(time.time()))
        random_id = str(uuid.uuid4())[:8]
        random_name = f"{timestamp}_{random_id}"
        
        if extension:
            if not extension.startswith('.'):
                extension = '.' + extension
            return random_name + extension
        return random_name
    

    def _convert_input_to_bytes(self, input_data: Any, content_type: str, video_fps: float = 30.0) -> Tuple[bytes, str, str]:
        """将输入数据转换为字节数据"""
        
        # 优先：字符串且是文件路径
        if isinstance(input_data, str) and os.path.isfile(input_data):
            file_path = input_data
            with open(file_path, 'rb') as f:
                file_data = f.read()
            actual_filename = os.path.basename(file_path)
            detected_content_type = content_type or (mimetypes.guess_type(actual_filename)[0] or 'application/octet-stream')
            return file_data, actual_filename, detected_content_type

        # 尝试：对象中提取文件路径/句柄/字节
        def try_extract_file_from_object(obj) -> Optional[Tuple[bytes, str, str]]:
            try:
                # 常见属性名称
                candidate_attrs = ['path', 'video_path', 'file_path', 'filepath']
                for attr in candidate_attrs:
                    if hasattr(obj, attr):
                        p = getattr(obj, attr)
                        if isinstance(p, str) and os.path.isfile(p):
                            with open(p, 'rb') as f:
                                data = f.read()
                            name = os.path.basename(p)
                            ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                            return data, name, ctype
                # 文件句柄
                if hasattr(obj, 'file') and hasattr(getattr(obj, 'file'), 'read'):
                    fobj = getattr(obj, 'file')
                    data = fobj.read()
                    name = getattr(obj, 'filename', getattr(fobj, 'name', self._generate_random_filename('bin')))
                    name = os.path.basename(name)
                    ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                    return data, name, ctype
                # 原始字节
                if hasattr(obj, 'to_bytes') and callable(getattr(obj, 'to_bytes')):
                    data = obj.to_bytes()
                    name = os.path.basename(getattr(obj, 'filename', 'file.bin'))
                    ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                    return data, name, ctype
                if hasattr(obj, 'bytes'):
                    data = getattr(obj, 'bytes')
                    name = os.path.basename(getattr(obj, 'filename', 'file.bin'))
                    ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                    return data, name, ctype
                # 扫描 __dict__ 中的所有字符串属性，寻找存在的路径
                if hasattr(obj, '__dict__') and isinstance(obj.__dict__, dict):
                    for k, v in obj.__dict__.items():
                        if isinstance(v, str) and os.path.isfile(v):
                            with open(v, 'rb') as f:
                                data = f.read()
                            name = os.path.basename(v)
                            ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                            return data, name, ctype
                # repr 探测 ComfyAPI 视频对象
                r = repr(obj)
                if 'VideoFromFile' in r:
                    # 最后再尝试常见属性
                    for attr in candidate_attrs + ['filename', 'name']:
                        if hasattr(obj, attr):
                            p = getattr(obj, attr)
                            if isinstance(p, str) and os.path.isfile(p):
                                with open(p, 'rb') as f:
                                    data = f.read()
                                name = os.path.basename(p)
                                ctype = content_type or (mimetypes.guess_type(name)[0] or 'application/octet-stream')
                                return data, name, ctype
            except Exception:
                pass
            return None

        extracted = try_extract_file_from_object(input_data)
        if extracted is not None:
            return extracted
        
        # 处理AUDIO类型数据（ComfyUI音频格式）
        if isinstance(input_data, dict) and 'waveform' in input_data and 'sample_rate' in input_data:
            # ComfyUI音频格式: {"waveform": tensor, "sample_rate": int}
            waveform = input_data['waveform']
            sample_rate = input_data['sample_rate']
            
            try:
                from pydub import AudioSegment
                import wave
            except ImportError:
                raise ImportError("需要安装pydub来支持MP3音频生成功能: pip install pydub")
            
            # 确保音频数据在正确范围内
            if isinstance(waveform, torch.Tensor):
                audio_data = waveform.cpu().numpy()
            else:
                audio_data = waveform
                
            # 如果是多声道，取第一个声道或混合
            if len(audio_data.shape) > 1:
                if audio_data.shape[0] == 1:  # [1, samples]
                    audio_data = audio_data[0]
                elif audio_data.shape[1] == 1:  # [samples, 1]
                    audio_data = audio_data[:, 0]
                else:  # 多声道，取平均
                    audio_data = np.mean(audio_data, axis=0 if audio_data.shape[0] > audio_data.shape[1] else 1)
            
            # 归一化到16位整数范围
            if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                audio_data = (audio_data * 32767).astype(np.int16)
            
            # 先创建WAV格式的音频段
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
            
            # 转换为MP3格式
            wav_buffer.seek(0)
            audio_segment = AudioSegment.from_wav(wav_buffer)
            mp3_buffer = io.BytesIO()
            audio_segment.export(mp3_buffer, format="mp3")
            
            file_data = mp3_buffer.getvalue()
            # 自动生成随机文件名，固定使用.mp3后缀
            actual_filename = self._generate_random_filename("mp3")
            detected_content_type = content_type or "audio/mp3"
            
        # 处理图片张量
        elif isinstance(input_data, torch.Tensor):
            if len(input_data.shape) == 4:  # 批次图片 [B, H, W, C]
                batch_size = input_data.shape[0]
                
                # 如果有多张图片（batch_size >= 2），生成视频
                if batch_size >= 2:
                    try:
                        file_data = self._images_to_video(input_data, video_fps)
                        # 自动生成随机文件名，固定使用.mp4后缀
                        actual_filename = self._generate_random_filename("mp4")
                        detected_content_type = content_type or "video/mp4"
                    except Exception as e:
                        # 如果视频生成失败，回退到处理第一张图片
                        print(f"视频生成失败，回退到单图片模式: {str(e)}")
                        image_tensor = input_data[0]
                else:
                    # 只有一张图片，按单图片处理
                    image_tensor = input_data[0]
                
                # 如果定义了image_tensor，处理单图片
                if 'image_tensor' in locals():
                    # 转换为PIL图片
                    if image_tensor.dtype == torch.float32:
                        image_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                    else:
                        image_array = image_tensor.cpu().numpy()
                    
                    image = Image.fromarray(image_array)
                    
                    # 保存为PNG格式
                    buffer = io.BytesIO()
                    image.save(buffer, format='PNG')
                    file_data = buffer.getvalue()
                    
                    # 自动生成随机文件名，固定使用.png后缀
                    actual_filename = self._generate_random_filename("png")
                    detected_content_type = content_type or "image/png"
                    
            elif len(input_data.shape) == 3:  # 单张图片 [H, W, C]
                image_tensor = input_data
                # 转换为PIL图片
                if image_tensor.dtype == torch.float32:
                    image_array = (image_tensor.cpu().numpy() * 255).astype(np.uint8)
                else:
                    image_array = image_tensor.cpu().numpy()
                
                image = Image.fromarray(image_array)
                
                # 保存为PNG格式
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                file_data = buffer.getvalue()
                
                # 自动生成随机文件名，固定使用.png后缀
                actual_filename = self._generate_random_filename("png")
                detected_content_type = content_type or "image/png"
                
            elif len(input_data.shape) == 2:  # 可能是音频数据 [channels, samples] 或 [samples, channels]
                # 尝试作为音频处理
                audio_data = input_data.cpu().numpy()
                
                # 判断哪个维度是样本数（通常更大的维度）
                if audio_data.shape[0] > audio_data.shape[1]:
                    audio_data = audio_data.T  # 转置为 [channels, samples]
                
                # 如果是多声道，取第一个声道
                if len(audio_data.shape) > 1 and audio_data.shape[0] > 1:
                    audio_data = audio_data[0]
                else:
                    audio_data = audio_data.flatten()
                
                # 归一化到16位整数范围
                if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                    audio_data = (audio_data * 32767).astype(np.int16)
                
                # 默认采样率
                sample_rate = 44100
                
                try:
                    from pydub import AudioSegment
                    import wave
                except ImportError:
                    raise ImportError("需要安装pydub来支持MP3音频生成功能: pip install pydub")
                
                # 先创建WAV格式的音频段
                wav_buffer = io.BytesIO()
                with wave.open(wav_buffer, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 单声道
                    wav_file.setsampwidth(2)  # 16位
                    wav_file.setframerate(sample_rate)
                    wav_file.writeframes(audio_data.tobytes())
                
                # 转换为MP3格式
                wav_buffer.seek(0)
                audio_segment = AudioSegment.from_wav(wav_buffer)
                mp3_buffer = io.BytesIO()
                audio_segment.export(mp3_buffer, format="mp3")
                
                file_data = mp3_buffer.getvalue()
                # 自动生成随机文件名，固定使用.mp3后缀
                actual_filename = self._generate_random_filename("mp3")
                detected_content_type = content_type or "audio/mp3"
            else:
                raise ValueError(f"不支持的张量形状: {input_data.shape}")
            
        # 处理字符串数据
        elif isinstance(input_data, str):
            file_data = input_data.encode('utf-8')
            # 自动生成随机文件名，固定使用.txt后缀
            actual_filename = self._generate_random_filename("txt")
            detected_content_type = content_type or "text/plain; charset=utf-8"
            
        # 处理字节数据
        elif isinstance(input_data, bytes):
            file_data = input_data
            # 自动生成随机文件名，使用.bin后缀
            actual_filename = self._generate_random_filename("bin")
            detected_content_type = content_type or "application/octet-stream"
            
        # 处理numpy数组
        elif isinstance(input_data, np.ndarray):
            if len(input_data.shape) == 3:  # 图片数组
                image = Image.fromarray(input_data.astype(np.uint8))
                buffer = io.BytesIO()
                image_format = 'PNG' if input_data.shape[2] == 4 else 'JPEG'
                image.save(buffer, format=image_format)
                file_data = buffer.getvalue()
                # 自动生成随机文件名，根据图片格式确定后缀
                actual_filename = self._generate_random_filename(image_format.lower())
                detected_content_type = content_type or f"image/{image_format.lower()}"
            else:
                # 其他数组数据保存为numpy格式
                buffer = io.BytesIO()
                np.save(buffer, input_data)
                file_data = buffer.getvalue()
                # 自动生成随机文件名，固定使用.npy后缀
                actual_filename = self._generate_random_filename("npy")
                detected_content_type = content_type or "application/octet-stream"
                
        # 处理列表和字典
        elif isinstance(input_data, (list, dict)):
            json_str = json.dumps(input_data, ensure_ascii=False, indent=2)
            file_data = json_str.encode('utf-8')
            # 自动生成随机文件名，固定使用.json后缀
            actual_filename = self._generate_random_filename("json")
            detected_content_type = content_type or "application/json; charset=utf-8"
            
        else:
            # 尝试转换为字符串
            try:
                str_data = str(input_data)
                file_data = str_data.encode('utf-8')
                # 自动生成随机文件名，固定使用.txt后缀
                actual_filename = self._generate_random_filename("txt")
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