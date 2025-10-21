from .nodes.ApiRequestNode import *
from .nodes.ElasticsearchUpdateNode import *
from .nodes.JsonParserNode import *
from .nodes.JsonBuilderNode import *
from .nodes.EmptyImageNode import *
from .nodes.LoadImageFromUrlNode import *
from .nodes.TextToImageNode import *
from .nodes.SaveVideoRGBA import *
from .nodes.RemoveEmptyLinesNode import *
from .nodes.MultilinePromptNode import *
from .nodes.OSSUploadNode import *

NODE_CONFIG = {
    # Network nodes
    "API Request Node": {"class": APIRequestNode, "name": "API Request Node"},
    "Elasticsearch Update Node": {"class": ElasticsearchUpdateNode, "name": "ES更新节点"},
    
    # Data processing nodes
    "JSON Parser Node": {"class": JSONParserNode, "name": "JSON解析器"},
    "JSON Builder Node": {"class": JsonBuilderNode, "name": "JSON构建器"},
    "RemoveEmptyLinesNode": {"class": RemoveEmptyLinesNode, "name": "Remove Empty Lines 🗑️"},
    
    # Text processing nodes
    "MultilinePromptNode": {"class": MultilinePromptNode, "name": "Multiline Prompt 📝"},
    
    # Cloud storage nodes
    "OSSUploadNode": {"class": OSSUploadNode, "name": "OSS Upload 📤"},
    
    # Image processing nodes
    "LoadImageFromUrlNode": {"class": LoadImageFromUrlNode, "name": "LoadImageFromUrlNode"},
    "TextToImageNode": {"class": TextToImageNode, "name": "Text To Image"},
    
    # Video processing nodes
    "SaveVideoRGBA": {"class": SaveVideoRGBA, "name": "Save Video (RGBA)"},
    
    # Utility nodes
    "Empty Image Node": {"class": EmptyImageNode, "name": "Empty Image Node"},
}

NODE_CLASS_MAPPINGS = {k: v["class"] for k, v in NODE_CONFIG.items()}
NODE_DISPLAY_NAME_MAPPINGS = {k: v["name"] for k, v in NODE_CONFIG.items()}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
