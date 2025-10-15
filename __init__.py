from .nodes.ApiRequestNode import *
from .nodes.JsonParserNode import *
from .nodes.EmptyImageNode import *
from .nodes.LoadImageFromUrlNode import *
from .nodes.TextToImageNode import *

NODE_CONFIG = {
    # Network nodes
    "API Request Node": {"class": APIRequestNode, "name": "API Request Node"},
    
    # Data processing nodes
    "JSON Parser Node": {"class": JsonParserNode, "name": "JSON Parser Node"},
    
    # Image processing nodes
    "LoadImageFromUrlNode": {"class": LoadImageFromUrlNode, "name": "LoadImageFromUrlNode"},
    "TextToImageNode": {"class": TextToImageNode, "name": "Text To Image"},
    
    # Utility nodes
    "Empty Image Node": {"class": EmptyImageNode, "name": "Empty Image Node"},
}

NODE_CLASS_MAPPINGS = {k: v["class"] for k, v in NODE_CONFIG.items()}
NODE_DISPLAY_NAME_MAPPINGS = {k: v["name"] for k, v in NODE_CONFIG.items()}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
