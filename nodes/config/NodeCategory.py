"""
ComfyUI-ZMG-Nodes 节点分类配置

定义所有ZMG节点的分类前缀和子分类
"""


class NodeCategory:
    """节点分类配置类"""
    
    # 主分类前缀
    PREFIX = "ZMGNodes"
    
    # 默认分类
    CATEGORY = f"{PREFIX}/utils"
    
    # 子分类定义
    NETWORK = f"{PREFIX}/network"      # 网络相关节点
    DATA = f"{PREFIX}/data"            # 数据处理节点  
    IMAGE = f"{PREFIX}/image"          # 图像处理节点
    UTILS = f"{PREFIX}/utils"          # 工具类节点
    AUDIO = f"{PREFIX}/audio"          # 音频处理节点