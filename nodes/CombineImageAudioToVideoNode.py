import os
import datetime
import subprocess
import torch
import numpy as np
import folder_paths
from comfy.comfy_types import IO
from comfy_api.latest import InputImpl
from .config.NodeCategory import NodeCategory


def _tensor_to_bytes_uint8(t):
    return (t.clamp(0.0, 1.0).mul(255).add(0.5).byte().cpu().numpy()).tobytes()


def _pingpong(seq):
    for x in seq:
        yield x
    for i in range(len(seq) - 2, 0, -1):
        yield seq[i]


class CombineImageAudioToVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "输入帧序列，形状 BxHxWxC，C=3/4"}),
                "frame_rate": ("FLOAT", {"default": 24.0, "min": 1.0, "step": 1.0, "tooltip": "视频帧率，常用 16/24/30"}),
                "filename_prefix": ("STRING", {"default": "ZMG", "tooltip": "文件名前缀，系统会自动追加计数与时间戳"}),
                "format": ([
                    "video/h264-mp4",
                    "video/vp9-webm",
                    "video/prores-mov",
                ], {"default": "video/h264-mp4", "tooltip": "视频容器/编码：mp4(H.264)、webm(VP9)、mov(ProRes)"}),
                "pix_fmt": ([
                    "yuv420p",
                    "yuva420p",
                    "yuva444p10le",
                ], {"default": "yuv420p", "tooltip": "像素格式：yuv420p(无透明)、yuva420p/yuva444p10le(有透明)"}),
                "crf": ("INT", {"default": 19, "min": 0, "max": 51, "step": 1, "tooltip": "质量系数：越小越清晰、体积越大(建议18-23)"}),
                "save_metadata": ("BOOLEAN", {"default": True, "tooltip": "写入创建时间等元数据"}),
                "trim_to_audio": ("BOOLEAN", {"default": False, "tooltip": "按音频长度裁剪；关闭则为视频补齐静音"}),
                "pingpong": ("BOOLEAN", {"default": False, "tooltip": "帧序列乒乓播放，延长时长"}),
                "save_output": ("BOOLEAN", {"default": True, "tooltip": "保存到output目录；关闭保存到temp目录"}),
            },
            "optional": {
                "audio": ("AUDIO", {"tooltip": "AUDIO字典：waveform+sample_rate"}),
            },
        }

    RETURN_TYPES = (IO.VIDEO,)
    RETURN_NAMES = ("video",)
    OUTPUT_IS_LIST = (False,)
    OUTPUT_NODE = True
    CATEGORY = NodeCategory.IMAGE
    FUNCTION = "combine"
    DESCRIPTION = "将IMAGE序列与AUDIO合成为视频文件"

    def _select_codec_and_ext(self, fmt):
        if fmt == "video/h264-mp4":
            return "libx264", "mp4"
        if fmt == "video/vp9-webm":
            return "libvpx-vp9", "webm"
        if fmt == "video/prores-mov":
            return "prores_ks", "mov"
        return "libx264", "mp4"

    def _ensure_even_dims(self, img):
        h, w = img.shape[0], img.shape[1]
        nh = h - (h % 2)
        nw = w - (w % 2)
        if nh == h and nw == w:
            return img
        return img[:nh, :nw]

    def combine(self, images, frame_rate, filename_prefix, format, pix_fmt, crf, save_metadata, trim_to_audio, pingpong, save_output, audio=None):
        b, h, w, c = images.shape
        has_alpha = c == 4
        if has_alpha and pix_fmt == "yuv420p":
            pix_fmt = "yuva420p"
        codec, ext = self._select_codec_and_ext(format)
        output_dir = folder_paths.get_output_directory() if save_output else folder_paths.get_temp_directory()
        full_output_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(filename_prefix, output_dir, w, h)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file = f"{filename}_{counter:05}_{ts}.{ext}"
        file_path = os.path.join(full_output_folder, file)

        images_np = images.cpu().numpy()
        images_np = images_np.astype(np.float32)
        frames = [self._ensure_even_dims(images_np[i]) for i in range(b)]
        if pingpong and b > 2:
            frames = list(_pingpong(frames))

        in_pix_fmt = "rgba" if has_alpha else "rgb24"
        dims = (frames[0].shape[1], frames[0].shape[0])

        args = [
            "ffmpeg", "-v", "error",
            "-f", "rawvideo", "-pix_fmt", in_pix_fmt,
            "-s", f"{dims[0]}x{dims[1]}", "-r", str(int(frame_rate)), "-i", "-",
            "-c:v", codec,
            "-pix_fmt", pix_fmt,
            "-crf", str(int(crf)),
        ]

        if save_metadata:
            args += ["-metadata", "creation_time=now"]

        args += [file_path]

        proc = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for f in frames:
                proc.stdin.write(_tensor_to_bytes_uint8(torch.from_numpy(f)))
            proc.stdin.flush()
            proc.stdin.close()
            _ = proc.stderr.read()
        except BrokenPipeError:
            err = proc.stderr.read()
            raise Exception(err.decode("utf-8", errors="ignore"))

        final_path = file_path

        if audio is not None and isinstance(audio, dict) and audio.get("waveform") is not None:
            channels = int(audio["waveform"].size(1))
            sample_rate = int(audio["sample_rate"])
            audio_bytes = audio["waveform"].squeeze(0).transpose(0, 1).numpy().tobytes()
            out_with_audio = f"{filename}_{counter:05}_{ts}-audio.{ext}"
            out_with_audio_path = os.path.join(full_output_folder, out_with_audio)
            apad = [] if trim_to_audio else ["-af", f"apad=whole_dur={len(frames)/frame_rate + 1}"]
            a_codec = "aac" if ext in ("mp4", "mov") else "libopus"
            mux = [
                "ffmpeg", "-v", "error", "-n",
                "-i", final_path,
                "-ar", str(sample_rate), "-ac", str(channels), "-f", "f32le", "-i", "-",
                "-c:v", "copy",
                "-c:a", a_codec,
            ] + apad + ["-shortest", out_with_audio_path]
            proc2 = subprocess.Popen(mux, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                proc2.stdin.write(audio_bytes)
                proc2.stdin.flush()
                proc2.stdin.close()
                _ = proc2.stderr.read()
                final_path = out_with_audio_path
                file = out_with_audio
            except BrokenPipeError:
                err = proc2.stderr.read()
                raise Exception(err.decode("utf-8", errors="ignore"))

        return (InputImpl.VideoFromFile(final_path),)


NODE_CLASS_MAPPINGS = {
    "CombineImageAudioToVideoNode": CombineImageAudioToVideoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CombineImageAudioToVideoNode": "Combine Image+Audio → Video"
}