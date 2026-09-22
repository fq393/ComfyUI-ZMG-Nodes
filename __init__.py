from .nodes.ApiRequestNode import *
from .nodes.JsonParserNode import *
from .nodes.JsonBuilderNode import *
from .nodes.EmptyImageNode import *
from .nodes.LoadImageFromUrlNode import *
from .nodes.TextToImageNode import *
from .nodes.SaveVideoRGBA import *
from .nodes.RemoveEmptyLinesNode import *
from .nodes.MultilinePromptNode import *
from .nodes.OSSUploadNode import *
from .nodes.LoadAudioFromUrlNode import *
from .nodes.CombineImageAudioToVideoNode import *
from .nodes.QwenImage21PromptEnhancerNode import QwenImage21PromptEnhancerNode
from .nodes.QwenImage21EditPromptEnhancerNode import QwenImage21EditPromptEnhancerNode

NODE_CONFIG = {
    # Network nodes
    "API Request Node": {"class": APIRequestNode, "name": "API Request Node"},
    
    # Data processing nodes
    "JSON Parser Node": {"class": JsonParserNode, "name": "JSON解析器"},
    "JSON Builder Node": {"class": JsonBuilderNode, "name": "JSON构建器"},
    "RemoveEmptyLinesNode": {"class": RemoveEmptyLinesNode, "name": "Remove Empty Lines 🗑️"},
    
    # Text processing nodes
    "MultilinePromptNode": {"class": MultilinePromptNode, "name": "Multiline Prompt 📝"},
    "QwenImage21PromptEnhancerNode": {"class": QwenImage21PromptEnhancerNode, "name": "Qwen Image 2.1 Prompt Enhancer (GPUStack)"},
    "QwenImage21EditPromptEnhancerNode": {"class": QwenImage21EditPromptEnhancerNode, "name": "Qwen Image 2.1 Edit Prompt Enhancer (GPUStack Vision)"},
    
    # Cloud storage nodes
    "OSSUploadNode": {"class": OSSUploadNode, "name": "OSS Upload 📤"},
    
    # Image processing nodes
    "LoadImageFromUrlNode": {"class": LoadImageFromUrlNode, "name": "LoadImageFromUrlNode"},
    "TextToImageNode": {"class": TextToImageNode, "name": "Text To Image"},
    
    # Video processing nodes
    "SaveVideoRGBA": {"class": SaveVideoRGBA, "name": "Save Video (RGBA)"},
    "CombineImageAudioToVideoNode": {"class": CombineImageAudioToVideoNode, "name": "Combine Image+Audio → Video"},

    # Utility nodes
    "Empty Image Node": {"class": EmptyImageNode, "name": "Empty Image Node"},

    # Audio processing nodes
    "LoadAudioFromUrlNode": {"class": LoadAudioFromUrlNode, "name": "Load Audio From URL"},
}

NODE_CLASS_MAPPINGS = {k: v["class"] for k, v in NODE_CONFIG.items()}
NODE_DISPLAY_NAME_MAPPINGS = {k: v["name"] for k, v in NODE_CONFIG.items()}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
