"""
ComfyUI类型工具类
用于解决ComfyUI节点间的类型匹配问题
"""


class AlwaysEqualProxy(str):
    """
    类型代理类，用于解决ComfyUI类型匹配问题
    继承自str，重写__eq__和__ne__方法，使其与任何类型都匹配
    
    这个类解决了ComfyUI中严格的类型检查问题，允许节点接受任意类型的输入
    """
    def __eq__(self, _):
        return True

    def __ne__(self, _):
        return False


class TautologyStr(str):
    """
    永真字符串类，用于类型匹配
    """
    def __ne__(self, other):
        return False


class ByPassTypeTuple(tuple):
    """
    绕过类型检查的元组类
    """
    def __getitem__(self, index):
        if index > 0:
            index = 0
        item = super().__getitem__(index)
        if isinstance(item, str):
            return TautologyStr(item)
        return item


# 定义通用类型，用于接受任意类型输入
ANY_TYPE = AlwaysEqualProxy("*")

# 为了兼容性，也提供小写版本
any_type = ANY_TYPE