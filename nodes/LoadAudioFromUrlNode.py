import os
import io
import base64
import requests
import torch
import numpy as np
from urllib.parse import parse_qs, unquote

try:
    import folder_paths
except Exception:
    folder_paths = None

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

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


def _format_from_url(url: str) -> str | None:
    if url.startswith("data:audio/"):
        semi = url.find(";")
        if semi != -1:
            return url[len("data:audio/"):semi]
        return None
    if url.startswith(("/view?", "/api/view?")):
        qs_idx = url.find("?")
        qs = parse_qs(url[qs_idx + 1:])
        filename = qs.get("name", qs.get("filename", [""]))[0]
        filename = unquote(filename)
        _, ext = os.path.splitext(filename)
        return ext[1:].lower() if ext else None
    if url.startswith(("http://", "https://", "file://")):
        base = url.split("?")[0]
        base = base.replace("file://", "")
        _, ext = os.path.splitext(base)
        return ext[1:].lower() if ext else None
    _, ext = os.path.splitext(url)
    return ext[1:].lower() if ext else None


def _decode_audio_bytes(data: bytes, fmt_hint: str | None):
    if AudioSegment is None:
        raise ImportError("pydub is not installed. Please install it using 'pip install pydub' to use LoadAudioFromUrlNode.")
    if AudioSegment is not None:
        seg = AudioSegment.from_file(io.BytesIO(data), format=fmt_hint) if fmt_hint else AudioSegment.from_file(io.BytesIO(data))
        sample_rate = seg.frame_rate
        channels = seg.channels
        array = np.array(seg.get_array_of_samples())
        if channels > 1:
            array = array.reshape((-1, channels)).T
        else:
            array = array.reshape((1, -1))
        scale = float(1 << (8 * seg.sample_width - 1))
        waveform = torch.from_numpy(array.astype(np.float32) / scale).unsqueeze(0)
        return {"waveform": waveform, "sample_rate": sample_rate}
    # 最小回退：无法解码时返回占位静音
    return {"waveform": torch.zeros((1, 1, 1), dtype=torch.float32), "sample_rate": 1}


class LoadAudioFromUrlNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "audio": ("STRING", {
                    "default": "",
                    "placeholder": "每行一个音频URL，例如\nhttps://example.com/audio.mp3\nfile:///path/to/audio.wav\ndata:audio/wav;base64, ...",
                    "tooltip": "支持 http/https、file://、data:audio、ComfyUI /view?；多行按顺序拼接为单一音轨",
                    "multiline": True,
                    "dynamicPrompts": False,
                }),
            },
            "optional": {
            },
        }

    RETURN_TYPES = ("AUDIO", "STRING", "BOOLEAN", "BOOLEAN")
    RETURN_NAMES = ("audio", "file_path", "saved", "has_audio")
    OUTPUT_IS_LIST = (False, False, False, False)
    CATEGORY = NodeCategory.AUDIO
    FUNCTION = "download_audio"
    DESCRIPTION = "从URL下载音频到ComfyUI的input目录，并输出AUDIO字典（仅解码为PCM，不重新编码）"

    def download_audio(self, audio: str):
        urls = [u.strip() for u in audio.strip().split("\n") if u.strip()]
        if not urls:
            empty = {"waveform": torch.zeros((1, 1, 1), dtype=torch.float32), "sample_rate": 1}
            return {"result": (empty, "", False, False)}
        url = urls[0]
        data = _read_bytes_from_url(url)
        if not data:
            empty = {"waveform": torch.zeros((1, 1, 1), dtype=torch.float32), "sample_rate": 1}
            return {"result": (empty, "", False, False)}
        fmt = _format_from_url(url) or "mp3"
        base_name = "audio"
        if url.startswith(('http://', 'https://', 'file://')):
            base = url.split('?')[0].replace('file://', '')
            bn = os.path.basename(base)
            if bn:
                base_name = unquote(bn)
        elif url.startswith(('data:audio/')):
            base_name = f"audio.{fmt}"
        elif url.startswith(('/view?', '/api/view?')):
            qs_idx = url.find("?")
            qs = parse_qs(url[qs_idx + 1:])
            name = qs.get("name", qs.get("filename", ["audio"]))[0]
            base_name = unquote(name)
        if not os.path.splitext(base_name)[1]:
            base_name = f"{base_name}.{fmt}"
        out_dir = folder_paths.get_input_directory() if folder_paths else os.path.join(os.getcwd(), "input")
        os.makedirs(out_dir, exist_ok=True)
        save_path = os.path.join(out_dir, base_name)
        idx = 1
        while os.path.exists(save_path):
            root, ext = os.path.splitext(base_name)
            save_path = os.path.join(out_dir, f"{root}_{idx}{ext}")
            idx += 1
        with open(save_path, "wb") as f:
            f.write(data)
        fmt_hint = _format_from_url(url)
        audio_dict = _decode_audio_bytes(data, fmt_hint)
        has_audio = bool(int(audio_dict.get("sample_rate", 0)) > 1 and audio_dict.get("waveform", torch.zeros(())).numel() > 1)
        return {"result": (audio_dict, save_path, True, has_audio)}


NODE_CLASS_MAPPINGS = {
    "LoadAudioFromUrlNode": LoadAudioFromUrlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadAudioFromUrlNode": "Load Audio From URL"
}