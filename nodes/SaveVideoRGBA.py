from __future__ import annotations
from typing_extensions import override
from typing import Optional, Tuple, Dict, Any
from fractions import Fraction
from enum import Enum
from PIL import Image
import torch
import numpy as np
import io
import json
import math
import av
import os
import random
import folder_paths
from comfy_api.latest._input import AudioInput, VideoInput
from comfy_api.latest import ComfyExtension, io, ui
from comfy_api.util import VideoComponents


class RGBAVideoCodec(str, Enum):
    """视频编解码器枚举"""
    AUTO = "auto"
    H264 = "h264"  # H.264 codec, no alpha channel
    VP9 = "libvpx-vp9"  # VP9 codec, supports alpha channel
    PRORES = "prores_ks"  # ProRes 4444, supports alpha channel

    @classmethod
    def as_input(cls) -> list[str]:
        """返回可用作节点输入的编解码器名称列表"""
        return [member.value for member in cls]

    @classmethod
    def get_default_for_alpha(cls, has_alpha: bool) -> str:
        """根据是否有alpha通道返回默认编解码器"""
        return cls.VP9.value if has_alpha else cls.H264.value


class RGBAVideoContainer(str, Enum):
    """视频容器格式枚举"""
    AUTO = "auto"
    MP4 = "mp4"  # MP4 container
    WEBM = "webm"  # WebM container, supports VP9 with alpha channel
    MOV = "mov"  # QuickTime MOV, supports ProRes with alpha channel

    @classmethod
    def as_input(cls) -> list[str]:
        """返回可用作节点输入的容器格式名称列表"""
        return [member.value for member in cls]

    @classmethod
    def get_extension(cls, value: str) -> str:
        """返回容器格式对应的文件扩展名"""
        if isinstance(value, str):
            try:
                value = cls(value)
            except ValueError:
                return "mp4"  # 默认扩展名
        
        extension_map = {
            cls.AUTO: "mp4",
            cls.MP4: "mp4",
            cls.WEBM: "webm",
            cls.MOV: "mov"
        }
        return extension_map.get(value, "mp4")

    @classmethod
    def get_default_for_alpha(cls, has_alpha: bool) -> str:
        """根据是否有alpha通道返回默认容器格式"""
        return cls.WEBM.value if has_alpha else cls.MP4.value

    @classmethod
    def supports_alpha(cls, format_str: str) -> bool:
        """检查格式是否支持alpha通道"""
        return format_str in ['webm', 'mov']


class VideoFormatConfig:
    """视频格式配置类，用于管理格式和编解码器的组合"""
    
    @staticmethod
    def get_pixel_format(codec: str, has_alpha: bool) -> str:
        """根据编解码器和alpha通道返回像素格式"""
        if has_alpha:
            pixel_formats = {
                'libvpx-vp9': 'yuva420p',
                'prores_ks': 'yuva444p10le'
            }
            return pixel_formats.get(codec, 'yuva420p')
        else:
            return 'yuv420p'

    @staticmethod
    def get_audio_codec(format_str: str) -> str:
        """根据容器格式返回音频编解码器"""
        return 'libopus' if format_str == 'webm' else 'aac'

    @staticmethod
    def validate_format_codec_combination(format_str: str, codec_str: str, has_alpha: bool) -> None:
        """验证格式和编解码器组合的有效性"""
        if has_alpha and not RGBAVideoContainer.supports_alpha(format_str):
            raise ValueError(f"Format '{format_str}' does not support alpha channel. Use 'webm' or 'mov'.")
        
        supported_codecs = ['h264', 'libvpx-vp9', 'prores_ks']
        if codec_str not in supported_codecs and codec_str != 'auto':
            raise ValueError(f"Unsupported codec '{codec_str}'. Supported codecs: {supported_codecs}")


class SaveVideoRGBA(io.ComfyNode):
    """保存RGBA视频的ComfyUI节点"""

    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id="SaveVideoRGBA",
            display_name="Save Video (RGBA)",
            category="image/animation",
            inputs=[
                io.Image.Input("images"),
                io.Float.Input("fps", default=24.0, min=1.0, max=120.0, step=1.0),
                io.String.Input(
                    "filename_prefix", 
                    default="video/ComfyUI", 
                    tooltip="文件保存前缀。可包含格式化信息如 %date:yyyy-MM-dd% 或 %Empty Latent Image.width%"
                ),
                io.Combo.Input(
                    "format",
                    default="auto",
                    options=RGBAVideoContainer.as_input(),
                    tooltip="视频容器格式。auto会根据是否有alpha通道自动选择"
                ),
                io.Combo.Input(
                    "codec",
                    default="auto", 
                    options=RGBAVideoCodec.as_input(),
                    tooltip="视频编解码器。auto会根据是否有alpha通道自动选择"
                ),
                io.Boolean.Input("only_preview", default=False),
                io.Audio.Input("audio", optional=True),
            ],
            outputs=[
                # io.Video.Output("VIDEO")  # 可根据需要启用视频输出
            ],
            hidden=[io.Hidden.unique_id],
            is_output_node=True
        )

    @classmethod
    def execute(cls, images: torch.Tensor, fps: float, filename_prefix: str, format: str,
                codec: str, only_preview: bool, audio: Optional[Dict[str, Any]] = None, **kwargs) -> io.NodeOutput:
        """执行视频保存操作"""
        try:
            # 获取图像尺寸和通道信息
            B, H, W, C = images.shape
            has_alpha = C == 4

            # 验证格式和编解码器组合的有效性
            if format != "auto" and codec != "auto":
                VideoFormatConfig.validate_format_codec_combination(format, codec, has_alpha)

            # 调整图像尺寸以确保能被2整除（视频编码要求）
            images = cls._resize_images_if_needed(images, divisible_by=2)
            
            # 创建视频组件
            video = RGBAVideoFromComponents(
                VideoComponents(
                    images=images,
                    audio=audio,
                    frame_rate=Fraction(fps),
                )
            )

            width, height = video.get_dimensions()
            results = []

            # 处理预览和保存
            if only_preview or has_alpha:
                preview_result = cls._save_preview(video, width, height, has_alpha)
                if preview_result:
                    results.append(preview_result)

            if not only_preview:
                save_result = cls._save_final(video, filename_prefix, width, height, has_alpha, format, codec)
                if save_result:
                    results.append(save_result)

            return io.NodeOutput(ui=ui.PreviewVideo(results))
            
        except Exception as e:
            print(f"SaveVideoRGBA执行错误: {str(e)}")
            raise

    @staticmethod
    def _resize_images_if_needed(images: torch.Tensor, divisible_by: int = 2) -> torch.Tensor:
        """如果需要，调整图像尺寸以满足编码要求"""
        B, H, W, C = images.shape
        
        if W % divisible_by == 0 and H % divisible_by == 0:
            return images

        new_width = W - (W % divisible_by)
        new_height = H - (H % divisible_by)
        
        print(f'调整视频尺寸从 {W}x{H} 到 {new_width}x{new_height}')

        # 批量处理图像调整大小，提高性能
        images_np = (images.cpu().numpy() * 255).astype(np.uint8)
        resized_images = []
        
        for i in range(B):
            img = Image.fromarray(images_np[i])
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            resized_tensor = torch.from_numpy(np.array(resized_img).astype(np.float32) / 255.0)
            resized_images.append(resized_tensor)

        return torch.stack(resized_images, dim=0)

    @staticmethod
    def _save_preview(video: 'RGBAVideoFromComponents', width: int, height: int, has_alpha: bool) -> Optional[ui.SavedResult]:
        """保存预览视频"""
        try:
            output_dir = folder_paths.get_temp_directory()
            prefix_append = "ComfyUI_temp_" + ''.join(random.choice("abcdefghijklmnopqrstupvxyz") for _ in range(5))
            
            full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
                prefix_append, output_dir, width, height
            )
            
            format_str = RGBAVideoContainer.get_default_for_alpha(has_alpha)
            file_ext = RGBAVideoContainer.get_extension(format_str)
            file = f"{filename}_{counter:05}_.{file_ext}"
            
            video.save_to(
                path=os.path.join(full_output_folder, file),
                format=format_str,
                codec='auto',
                metadata=None,
            )

            return ui.SavedResult(file, subfolder, io.FolderType.temp)
            
        except Exception as e:
            print(f"保存预览视频失败: {str(e)}")
            return None

    @staticmethod
    def _save_final(video: 'RGBAVideoFromComponents', filename_prefix: str, 
                   width: int, height: int, has_alpha: bool, format: str, codec: str) -> Optional[ui.SavedResult]:
        """保存最终视频"""
        try:
            output_dir = folder_paths.get_output_directory()
            
            full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
                filename_prefix, output_dir, width, height
            )
            
            # 使用用户选择的格式和编解码器
            format_str = format
            codec_str = codec
            
            # 如果是auto，则根据alpha通道自动选择
            if format_str == "auto":
                format_str = RGBAVideoContainer.get_default_for_alpha(has_alpha)
            if codec_str == "auto":
                codec_str = RGBAVideoCodec.get_default_for_alpha(has_alpha)
            
            file_ext = RGBAVideoContainer.get_extension(format_str)
            file = f"{filename}_{counter:05}_.{file_ext}"
            
            video.save_to(
                path=os.path.join(full_output_folder, file),
                format=format_str,
                codec=codec_str,
                metadata=None,
            )

            # 返回保存结果
            return ui.SavedResult(file, subfolder, io.FolderType.output)
                
        except Exception as e:
            print(f"保存最终视频失败: {str(e)}")
            
        return None


class RGBAVideoFromComponents(VideoInput):
    """从组件创建RGBA视频的类"""

    def __init__(self, components: VideoComponents):
        self.__components = components

    def get_components(self) -> VideoComponents:
        """获取视频组件"""
        return VideoComponents(
            images=self.__components.images,
            audio=self.__components.audio,
            frame_rate=self.__components.frame_rate
        )

    def get_dimensions(self) -> Tuple[int, int]:
        """获取视频尺寸"""
        return self.__components.images.shape[2], self.__components.images.shape[1]

    def save_to(self, path: str, format: str = "auto", codec: str = "auto", 
                metadata: Optional[Dict[str, Any]] = None) -> None:
        """保存视频到指定路径"""
        try:
            # 检查是否有alpha通道
            has_alpha = self.__components.images.shape[-1] == 4 if len(self.__components.images.shape) == 4 else False

            # 确定格式和编解码器
            format_str, codec_str = self._determine_format_and_codec(format, codec, has_alpha)
            
            # 验证格式和编解码器组合
            VideoFormatConfig.validate_format_codec_combination(format_str, codec_str, has_alpha)

            # 保存视频
            self._encode_video(path, format_str, codec_str, has_alpha, metadata)
            
        except Exception as e:
            print(f"视频保存失败: {str(e)}")
            raise

    def _determine_format_and_codec(self, format: str, codec: str, has_alpha: bool) -> Tuple[str, str]:
        """确定最终使用的格式和编解码器"""
        # 处理格式
        if format == "auto":
            format_str = RGBAVideoContainer.get_default_for_alpha(has_alpha)
        else:
            format_str = format

        # 处理编解码器
        if codec == "auto":
            codec_str = RGBAVideoCodec.get_default_for_alpha(has_alpha)
        else:
            codec_str = codec

        return format_str, codec_str

    def _encode_video(self, path: str, format_str: str, codec_str: str, 
                     has_alpha: bool, metadata: Optional[Dict[str, Any]]) -> None:
        """编码并保存视频"""
        # 准备选项
        options = {}
        if format_str in ['mp4', 'mov']:
            options['movflags'] = 'use_metadata_tags'

        # 确定输出格式
        output_format = None if format_str == "auto" else format_str

        with av.open(path, mode='w', format=output_format, options=options) as output:
            # 添加元数据
            if metadata:
                for key, value in metadata.items():
                    output.metadata[key] = json.dumps(value)

            # 创建视频流
            video_stream = self._create_video_stream(output, codec_str, has_alpha)
            
            # 创建音频流
            audio_stream = self._create_audio_stream(output, format_str)

            # 编码视频帧
            self._encode_video_frames(video_stream, output, has_alpha)

            # 编码音频
            if audio_stream:
                self._encode_audio_frames(audio_stream, output, video_stream.rate)

    def _create_video_stream(self, output: av.OutputContainer, codec_str: str, has_alpha: bool) -> av.VideoStream:
        """创建视频流"""
        frame_rate = Fraction(round(self.__components.frame_rate * 1000), 1000)
        video_stream = output.add_stream(codec_str, rate=frame_rate)
        video_stream.width = self.__components.images.shape[2]
        video_stream.height = self.__components.images.shape[1]
        video_stream.pix_fmt = VideoFormatConfig.get_pixel_format(codec_str, has_alpha)
        return video_stream

    def _create_audio_stream(self, output: av.OutputContainer, format_str: str) -> Optional[av.AudioStream]:
        """创建音频流"""
        if not self.__components.audio:
            return None
            
        audio_sample_rate = int(self.__components.audio['sample_rate'])
        audio_codec = VideoFormatConfig.get_audio_codec(format_str)
        return output.add_stream(audio_codec, rate=audio_sample_rate)

    def _encode_video_frames(self, video_stream: av.VideoStream, output: av.OutputContainer, has_alpha: bool) -> None:
        """编码视频帧"""
        for frame_tensor in self.__components.images:
            img = (frame_tensor * 255).clamp(0, 255).byte().cpu().numpy()

            # 创建视频帧
            if has_alpha:
                frame = av.VideoFrame.from_ndarray(img, format='rgba')
            else:
                frame = av.VideoFrame.from_ndarray(img, format='rgb24')
            
            frame = frame.reformat(format=video_stream.pix_fmt)
            
            # 编码并输出
            for packet in video_stream.encode(frame):
                output.mux(packet)

        # 刷新编码器
        for packet in video_stream.encode(None):
            output.mux(packet)

    def _encode_audio_frames(self, audio_stream: av.AudioStream, output: av.OutputContainer, frame_rate: Fraction) -> None:
        """编码音频帧"""
        if not self.__components.audio:
            return

        audio_sample_rate = int(self.__components.audio['sample_rate'])
        waveform = self.__components.audio['waveform']
        
        # 计算音频长度
        audio_length = math.ceil((audio_sample_rate / frame_rate) * self.__components.images.shape[0])
        waveform = waveform[:, :, :audio_length]
        
        # 创建音频帧
        audio_data = waveform.movedim(2, 1).reshape(1, -1).float().numpy()
        layout = 'mono' if waveform.shape[1] == 1 else 'stereo'
        
        frame = av.AudioFrame.from_ndarray(audio_data, format='flt', layout=layout)
        frame.sample_rate = audio_sample_rate
        frame.pts = 0
        
        # 编码并输出
        for packet in audio_stream.encode(frame):
            output.mux(packet)

        # 刷新编码器
        for packet in audio_stream.encode(None):
            output.mux(packet)


class NodeExtension(ComfyExtension):
    """ComfyUI节点扩展"""
    
    @override
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [SaveVideoRGBA]


async def comfy_entrypoint() -> NodeExtension:
    """ComfyUI入口点"""
    return NodeExtension()