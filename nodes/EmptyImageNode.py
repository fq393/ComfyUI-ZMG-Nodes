from typing import Tuple, Optional, Any, Dict
from .config.NodeCategory import NodeCategory


class EmptyImageNode:
    """
    ComfyUI节点：空图像节点
    
    返回None作为IMAGE类型的实用工具节点。
    适用于条件工作流或作为占位符使用。
    
    使用场景：
    - 条件分支中的空图像占位符
    - 工作流中的默认空值
    - 测试和调试时的空输入
    """

    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        定义节点的输入类型
        
        Returns:
            Dict[str, Any]: 输入类型配置（无需输入）
        """
        return {
            "required": {},
            "optional": {
                "description": ("STRING", {
                    "default": "空图像占位符",
                    "placeholder": "节点描述（可选）"
                })
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("empty_image",)
    FUNCTION = "get_empty_image"
    CATEGORY = NodeCategory.UTILS
    
    DESCRIPTION = """
返回空图像(None)的实用工具节点，用于条件工作流或占位符。
适用于条件分支中的空图像占位符、工作流中的默认空值、测试和调试时的空输入。
"""

    def get_empty_image(self, description: str = "空图像占位符") -> Tuple[Optional[Any]]:
        """
        返回空图像
        
        Args:
            description (str): 节点描述（仅用于文档目的）
            
        Returns:
            Tuple[Optional[Any]]: 包含None的元组，表示空图像
        """
        # 返回None作为IMAGE类型
        # 这在条件工作流中很有用，可以作为空分支的占位符
        return (None,)


NODE_CLASS_MAPPINGS = {
    "😋Empty Image Node": EmptyImageNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "😋Empty Image Node": "😋空图像节点"
}