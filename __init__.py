import importlib

node_list = [
    "ApiRequestNode",
    "JsonParserNode",
    "OldPhotoColorizationNode",
    "SaveImageUnifiedOutput",
    "EmptyImageNode",
    "LoadImageFromUrlNode",
]

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for module_name in node_list:
    imported_module = importlib.import_module(".nodes.{}".format(module_name), __name__)
    NODE_CLASS_MAPPINGS = {**NODE_CLASS_MAPPINGS, **imported_module.NODE_CLASS_MAPPINGS}
    NODE_DISPLAY_NAME_MAPPINGS = {**NODE_DISPLAY_NAME_MAPPINGS, **imported_module.NODE_DISPLAY_NAME_MAPPINGS}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
