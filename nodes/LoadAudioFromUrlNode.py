import os
import io
import base64
import requests
from urllib.parse import parse_qs, unquote

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


def _format_from_url(url: str) -> str | None:
    if url.startswith("data:audio/"):
        semi = url.find(";")
        if semi != -1:
            return url[len("data:audio/"):semi]
    _, ext = os.path.splitext(url)
    if ext:
        return ext[1:].lower()
    return None


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

    RETURN_TYPES = ("STRING", "BOOLEAN")
    RETURN_NAMES = ("file_path", "saved")
    OUTPUT_IS_LIST = (False, False)
    CATEGORY = NodeCategory.AUDIO
    FUNCTION = "download_audio"
    DESCRIPTION = "从URL下载音频到ComfyUI的input目录，不进行编码或解码"

    def download_audio(self, audio: str):
        urls = [u.strip() for u in audio.strip().split("\n") if u.strip()]
        if not urls:
            return {"result": ("", False)}
        url = urls[0]
        data = _read_bytes_from_url(url)
        if not data:
            return {"result": ("", False)}
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
        return {"result": (save_path, True)}


NODE_CLASS_MAPPINGS = {
    "LoadAudioFromUrlNode": LoadAudioFromUrlNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LoadAudioFromUrlNode": "Load Audio From URL"
}