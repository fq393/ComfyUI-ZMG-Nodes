import os
import io
import base64
import json
import torch
import numpy as np
import requests
from urllib.parse import parse_qs

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

try:
    import folder_paths
except Exception:
    folder_paths = None

from .config.NodeCategory import NodeCategory


def _read_bytes_from_url(url: str, timeout: int = 10) -> bytes:
    if url.startswith("data:audio/"):
        comma = url.find(",")
        if comma == -1:
            raise Exception("Invalid data URI")
        return base64.b64decode(url[comma + 1:])
    if url.startswith("file://"):
        path = url[7:]
        if not os.path.isfile(path):
            raise Exception(f"File {path} does not exist")
        with open(path, "rb") as f:
            return f.read()
    if url.startswith("http://") or url.startswith("https://"):
        r = requests.get(url, timeout=timeout)
        if r.status_code != 200:
            raise Exception(r.text)
        return r.content
    if url.startswith(('/view?', '/api/view?')):
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
            path = os.path.join(folder_paths.get_input_directory(), filename)
        elif dirtype[0] == "output":
            path = os.path.join(folder_paths.get_output_directory(), filename)
        elif dirtype[0] == "temp":
            path = os.path.join(folder_paths.get_temp_directory(), filename)
        else:
            raise Exception(f"Invalid url: {url}")
        with open(path, "rb") as f:
            return f.read()
    if url == "":
        return b""
    path = url
    if folder_paths:
        try:
            path = folder_paths.get_annotated_filepath(url)
        except Exception:
            path = url
    if not os.path.isfile(path):
        raise Exception(f"Invalid url: {url}")
    with open(path, "rb") as f:
        return f.read()


def _bytes_to_audio_segment(data: bytes, format_hint: str | None) -> AudioSegment:
    if AudioSegment is None:
        raise ImportError("pydub is required: pip install pydub")
    if format_hint:
        return AudioSegment.from_file(io.BytesIO(data), format=format_hint)
    return AudioSegment.from_file(io.BytesIO(data))


def _format_from_url(url: str) -> str | None:
    if url.startswith("data:audio/"):
        semi = url.find(";")
        if semi != -1:
            return url[len("data:audio/"):semi]
    _, ext = os.path.splitext(url)
    if ext:
        return ext[1:].lower()
    return None


def _segment_to_tensor(seg: AudioSegment, mono: bool, target_sample_rate: int) -> tuple[torch.Tensor, int, int]:
    if mono and seg.channels > 1:
        seg = seg.set_channels(1)
    if target_sample_rate and target_sample_rate > 0 and seg.frame_rate != target_sample_rate:
        seg = seg.set_frame_rate(target_sample_rate)
    sample_rate = seg.frame_rate
    channels = seg.channels
    array = np.array(seg.get_array_of_samples())
    if channels > 1:
        array = array.reshape((-1, channels)).T
    else:
        array = array.reshape((1, -1))
    scale = float(1 << (8 * seg.sample_width - 1))
    waveform = torch.from_numpy(array.astype(np.float32) / scale)
    return waveform.unsqueeze(0), sample_rate, channels


def _concat_waveforms(items: list[dict]) -> dict:
    if not items:
        return {
            "waveform": torch.zeros((1, 1, 16000), dtype=torch.float32),
            "sample_rate": 16000,
        }
    sr = items[0]["sample_rate"]
    ch = items[0]["waveform"].shape[1]
    for it in items:
        if it["sample_rate"] != sr:
            raise Exception("All audio clips must share the same sample_rate for concat")
        if it["waveform"].shape[1] != ch:
            raise Exception("All audio clips must share the same channel count for concat")
    waveforms = [it["waveform"].squeeze(0) for it in items]
    concat = torch.cat(waveforms, dim=2)
    return {"waveform": concat.unsqueeze(0), "sample_rate": sr}


class LoadAudioFromUrlNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("STRING", {
                    "default": "",
                    "placeholder": "每行一个音频URL，例如\nhttps://example.com/audio.mp3\nfile:///path/to/audio.wav\ndata:audio/wav;base64, ...",
                    "tooltip": "支持 http/https、file://、data:audio、ComfyUI /view?；多行按顺序处理。透传启用时取首个源的原始字节",
                    "multiline": True,
                    "dynamicPrompts": False,
                }),
            },
            "optional": {
                "mono": ("BOOLEAN", {"default": False, "label_on": "enabled", "label_off": "disabled", "tooltip": "强制单声道，仅在关闭透传时对解码后的音频生效"}),
                "target_sample_rate": ("INT", {"default": 0, "min": 0, "max": 192000, "step": 1000, "tooltip": "重采样到目标采样率，0 表示保持原采样率；仅在关闭透传时生效"}),
                "passthrough": ("BOOLEAN", {"default": True, "label_on": "enabled", "label_off": "disabled", "tooltip": "启用后直接输出原始字节(raw_bytes/mime/filename)，不进行解码。关闭则输出AUDIO字典"}),
            },
        }

    RETURN_TYPES = ("AUDIO", "BOOLEAN", "BYTES", "STRING", "STRING")
    RETURN_NAMES = ("audio", "has_audio", "raw_bytes", "mime", "filename")
    OUTPUT_IS_LIST = (False, False, False, False, False)
    CATEGORY = NodeCategory.AUDIO
    FUNCTION = "load_audio"
    DESCRIPTION = "从URL加载音频，支持HTTP/HTTPS、file://、data:audio/、ComfyUI内部路径；参数：audio(多源URL)、passthrough(透传原始字节)、mono(单声道)、target_sample_rate(重采样)"

    def load_audio(self, audio: str, mono: bool = False, target_sample_rate: int = 0, passthrough: bool = True):
        urls = [u.strip() for u in audio.strip().split("\n") if u.strip()]
        clips = []
        raw_bytes = b""
        mime = ""
        filename = ""
        for url in urls:
            data = _read_bytes_from_url(url)
            if not data:
                continue
            if raw_bytes == b"":
                raw_bytes = data
                fmt_hint = _format_from_url(url)
                if fmt_hint:
                    mime = f"audio/{fmt_hint}"
                # 生成文件名
                if url.startswith(('http://', 'https://', 'file://')):
                    base = url.split('?')[0]
                    base = base.replace('file://', '')
                    filename = os.path.basename(base) or 'audio'
                elif url.startswith(('data:audio/')):
                    filename = f"audio.{fmt_hint or 'bin'}"
                elif url.startswith(('/view?', '/api/view?')):
                    qs_idx = url.find("?")
                    qs = parse_qs(url[qs_idx + 1:])
                    name = qs.get("name", qs.get("filename", ["audio"]))[0]
                    filename = name
                else:
                    filename = os.path.basename(url) or 'audio'
            if not passthrough:
                fmt = _format_from_url(url)
                seg = _bytes_to_audio_segment(data, fmt)
                waveform, sample_rate, channels = _segment_to_tensor(seg, mono, target_sample_rate)
                clips.append({"waveform": waveform, "sample_rate": sample_rate, "channels": channels})
        has_audio = len(clips) > 0 or (raw_bytes != b"")
        if not has_audio:
            result = {"waveform": torch.zeros((1, 1, 16000), dtype=torch.float32), "sample_rate": 16000}
            return {"result": (result, False, b"", "", "")}
        audio_dict = None
        if not passthrough and clips:
            audio_dict = _concat_waveforms(clips)
        return {"result": (audio_dict if audio_dict else {"waveform": torch.zeros((1, 1, 1), dtype=torch.float32), "sample_rate": 1}, True, raw_bytes, mime or "application/octet-stream", filename or "audio")}


NODE_CLASS_MAPPINGS = {
    "LoadAudioFromUrlNode": LoadAudioFromUrlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadAudioFromUrlNode": "Load Audio From URL"
}