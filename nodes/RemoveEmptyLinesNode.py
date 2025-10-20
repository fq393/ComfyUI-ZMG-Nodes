"""
RemoveEmptyLinesNode - 去除空行节点
处理文本内容，去除空行和仅包含空白字符的行
支持多种处理模式和自定义配置
"""

import re
from typing import Dict, Any, Tuple
from .config.NodeCategory import NodeCategory


class RemoveEmptyLinesNode:
    """
    ComfyUI节点：去除空行
    
    处理输入的文本内容，去除空行和仅包含空白字符的行。
    支持多种处理模式，包括严格模式和宽松模式。
    """

    def __init__(self):
        """初始化去除空行节点"""
        pass
        
    @classmethod
    def INPUT_TYPES(cls) -> Dict[str, Any]:
        """
        定义节点的输入类型
        
        Returns:
            Dict[str, Any]: 输入类型配置
        """
        return {
            "required": {
                "text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入要处理的文本内容"
                }),
                "mode": (["strict", "loose", "trim_only"], {
                    "default": "strict",
                    "tooltip": "strict: 去除完全空行; loose: 去除空行和仅空白字符行; trim_only: 仅去除行首尾空白"
                }),
                "preserve_single_empty": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否保留单个空行（用于段落分隔）"
                }),
                "trim_lines": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否去除每行的首尾空白字符"
                })
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("processed_text", "statistics", "removed_lines_count")
    FUNCTION = "remove_empty_lines"
    CATEGORY = NodeCategory.DATA
    
    DESCRIPTION = """
去除空行节点 - 处理文本内容，去除不需要的空行

功能特性：
• 支持多种处理模式（严格/宽松/仅修剪）
• 可选择保留单个空行用于段落分隔
• 自动去除行首尾空白字符
• 提供详细的处理统计信息
• 支持大文本处理

处理模式：
• strict: 仅去除完全空行（不包含任何字符）
• loose: 去除空行和仅包含空白字符的行
• trim_only: 仅去除每行的首尾空白，保留所有行

输入参数：
• text: 要处理的文本内容
• mode: 处理模式选择
• preserve_single_empty: 是否保留单个空行
• trim_lines: 是否去除行首尾空白

输出：
• processed_text: 处理后的文本
• statistics: 处理统计信息
• removed_lines_count: 被移除的行数
"""

    def remove_empty_lines(self, text: str, mode: str = "strict", 
                          preserve_single_empty: bool = False, 
                          trim_lines: bool = True) -> Tuple[str, str, int]:
        """
        去除文本中的空行
        
        Args:
            text (str): 输入文本
            mode (str): 处理模式 ("strict", "loose", "trim_only")
            preserve_single_empty (bool): 是否保留单个空行
            trim_lines (bool): 是否去除行首尾空白
            
        Returns:
            Tuple[str, str, int]: (处理后的文本, 统计信息, 移除的行数)
        """
        if not text:
            return "", "输入文本为空", 0
        
        # 分割文本为行
        lines = text.split('\n')
        original_line_count = len(lines)
        processed_lines = []
        removed_count = 0
        empty_line_groups = 0
        consecutive_empty = 0
        
        for i, line in enumerate(lines):
            # 根据trim_lines设置决定是否去除行首尾空白
            if trim_lines:
                processed_line = line.strip()
            else:
                processed_line = line
            
            # 判断是否为空行
            is_empty = False
            if mode == "strict":
                # 严格模式：只有完全空行才算空行
                is_empty = (processed_line == "" and line == "")
            elif mode == "loose":
                # 宽松模式：空行或仅包含空白字符的行都算空行
                is_empty = (processed_line == "")
            elif mode == "trim_only":
                # 仅修剪模式：不移除任何行，只处理空白
                is_empty = False
            
            if is_empty:
                consecutive_empty += 1
                removed_count += 1
                
                # 如果启用保留单个空行，且这是连续空行中的第一个
                if preserve_single_empty and consecutive_empty == 1:
                    processed_lines.append("")
                    removed_count -= 1  # 不算作移除
            else:
                # 非空行
                if consecutive_empty > 0:
                    empty_line_groups += 1
                    consecutive_empty = 0
                
                processed_lines.append(processed_line if trim_lines else line)
        
        # 处理最后的连续空行组
        if consecutive_empty > 0:
            empty_line_groups += 1
        
        # 生成结果
        result_text = '\n'.join(processed_lines)
        
        # 生成统计信息
        final_line_count = len(processed_lines)
        statistics = f"""处理统计：
原始行数: {original_line_count}
处理后行数: {final_line_count}
移除行数: {removed_count}
空行组数: {empty_line_groups}
处理模式: {mode}
保留单空行: {'是' if preserve_single_empty else '否'}
修剪空白: {'是' if trim_lines else '否'}"""
        
        return result_text, statistics, removed_count

    def _is_whitespace_only(self, line: str) -> bool:
        """
        检查行是否仅包含空白字符
        
        Args:
            line (str): 要检查的行
            
        Returns:
            bool: 是否仅包含空白字符
        """
        return len(line.strip()) == 0


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "RemoveEmptyLinesNode": RemoveEmptyLinesNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "RemoveEmptyLinesNode": "Remove Empty Lines 🗑️"
}

__all__ = ['RemoveEmptyLinesNode', 'NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']