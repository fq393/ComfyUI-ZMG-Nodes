"""
MultilinePromptNode - 多行提示词节点
输出多行提示词文本，并统计总行数
支持自定义分隔符和格式化选项
"""

from typing import Dict, Any, Tuple
from .config.NodeCategory import NodeCategory


class MultilinePromptNode:
    """
    ComfyUI节点：多行提示词输出
    
    将输入的多行文本作为提示词输出，同时统计并输出总行数。
    支持多种格式化选项和自定义分隔符。
    """

    def __init__(self):
        """初始化多行提示词节点"""
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
                "prompt_text": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入多行提示词内容\n每行一个提示词或描述"
                }),
                "line_separator": (["换行符", "逗号", "分号", "空格", "自定义"], {
                    "default": "换行符",
                    "tooltip": "选择输出时的行分隔符"
                }),
                "custom_separator": ("STRING", {
                    "default": ", ",
                    "placeholder": "自定义分隔符",
                    "tooltip": "当选择'自定义'分隔符时使用"
                }),
                "remove_empty_lines": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否移除空行"
                }),
                "trim_lines": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "是否去除每行的首尾空白字符"
                }),
                "add_line_numbers": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否在每行前添加行号"
                }),
                "line_number_format": (["1. ", "(1) ", "[1] ", "1: ", "1 - "], {
                    "default": "1. ",
                    "tooltip": "行号格式"
                }),
                "enable_index": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "是否启用索引功能，获取指定行的数据"
                }),
                "line_index": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 9999,
                    "step": 1,
                    "tooltip": "要获取的行索引（从0开始）"
                })
            },
        }

    RETURN_TYPES = ("STRING", "INT", "STRING", "STRING", "STRING", "STRING", "COMBO")
    RETURN_NAMES = ("formatted_prompt", "total_lines", "line_count_info", "original_prompt", "indexed_line", "index_info", "lines_combo")
    FUNCTION = "process_multiline_prompt"
    CATEGORY = NodeCategory.TEXT
    
    DESCRIPTION = """
多行提示词节点 - 处理和格式化多行提示词文本

功能特性：
• 支持多行提示词输入和输出
• 自动统计并输出总行数
• 多种分隔符选择（换行符、逗号、分号等）
• 可选的行号添加功能
• 自动去除空行和首尾空白
• 提供原始文本和格式化文本输出
• 🆕 索引功能：可直接获取指定行的单条数据

分隔符选项：
• 换行符: 保持原有的多行格式
• 逗号: 用逗号连接所有行
• 分号: 用分号连接所有行  
• 空格: 用空格连接所有行
• 自定义: 使用自定义分隔符

索引功能：
• enable_index: 启用后可获取指定行的数据
• line_index: 指定要获取的行号（从0开始）
• 支持索引范围检查和错误提示
• 可与其他格式化功能组合使用

输入参数：
• prompt_text: 多行提示词文本
• line_separator: 输出分隔符类型
• custom_separator: 自定义分隔符内容
• remove_empty_lines: 是否移除空行
• trim_lines: 是否去除行首尾空白
• add_line_numbers: 是否添加行号
• line_number_format: 行号格式
• enable_index: 是否启用索引功能
• line_index: 要获取的行索引（从0开始）

输出：
• formatted_prompt: 格式化后的提示词文本
• total_lines: 总行数（整数）
• line_count_info: 行数统计信息（文本）
• original_prompt: 原始提示词文本
• indexed_line: 指定索引的行内容
• index_info: 索引操作的详细信息
• lines_combo: 所有行的列表（COMBO类型，可用于下拉选择）
"""

    def process_multiline_prompt(self, prompt_text: str, line_separator: str, custom_separator: str,
                                remove_empty_lines: bool, trim_lines: bool, add_line_numbers: bool,
                                line_number_format: str, enable_index: bool, line_index: int) -> Tuple[str, int, str, str, str, str, list]:
        """
        处理多行提示词
        
        Args:
            prompt_text: 输入的多行提示词文本
            line_separator: 分隔符类型
            custom_separator: 自定义分隔符
            remove_empty_lines: 是否移除空行
            trim_lines: 是否去除行首尾空白
            add_line_numbers: 是否添加行号
            line_number_format: 行号格式
            enable_index: 是否启用索引功能
            line_index: 要获取的行索引（从0开始）
            
        Returns:
            Tuple[str, int, str, str, str, str, list]: (格式化提示词, 总行数, 行数信息, 原始提示词, 索引行内容, 索引信息, 行列表)
        """
        
        # 保存原始文本
        original_prompt = prompt_text
        
        # 如果输入为空，返回默认值
        if not prompt_text or not prompt_text.strip():
            return "", 0, "总行数: 0行（空文本）", "", "", "索引功能未启用（文本为空）", []
        
        # 按行分割文本
        lines = prompt_text.split('\n')
        
        # 处理每行
        processed_lines = []
        for line in lines:
            # 去除首尾空白（如果启用）
            if trim_lines:
                line = line.strip()
            
            # 移除空行（如果启用）
            if remove_empty_lines and not line:
                continue
                
            processed_lines.append(line)
        
        # 统计行数
        total_lines = len(processed_lines)
        
        # 添加行号（如果启用）
        if add_line_numbers and processed_lines:
            numbered_lines = []
            for i, line in enumerate(processed_lines, 1):
                # 根据格式添加行号
                if line_number_format == "1. ":
                    numbered_line = f"{i}. {line}"
                elif line_number_format == "(1) ":
                    numbered_line = f"({i}) {line}"
                elif line_number_format == "[1] ":
                    numbered_line = f"[{i}] {line}"
                elif line_number_format == "1: ":
                    numbered_line = f"{i}: {line}"
                elif line_number_format == "1 - ":
                    numbered_line = f"{i} - {line}"
                else:
                    numbered_line = f"{i}. {line}"  # 默认格式
                
                numbered_lines.append(numbered_line)
            processed_lines = numbered_lines
        
        # 根据分隔符类型连接行
        if line_separator == "换行符":
            separator = "\n"
        elif line_separator == "逗号":
            separator = ", "
        elif line_separator == "分号":
            separator = "; "
        elif line_separator == "空格":
            separator = " "
        elif line_separator == "自定义":
            separator = custom_separator if custom_separator else ", "
        else:
            separator = "\n"  # 默认使用换行符
        
        # 连接所有行
        formatted_prompt = separator.join(processed_lines)
        
        # 生成行数统计信息
        if total_lines == 0:
            line_count_info = "总行数: 0行（处理后为空）"
        elif total_lines == 1:
            line_count_info = f"总行数: {total_lines}行（单行文本）"
        else:
            line_count_info = f"总行数: {total_lines}行（多行文本）"
        
        # 添加处理信息
        processing_info = []
        if remove_empty_lines:
            processing_info.append("已移除空行")
        if trim_lines:
            processing_info.append("已去除首尾空白")
        if add_line_numbers:
            processing_info.append("已添加行号")
        
        if processing_info:
            line_count_info += f" | 处理: {', '.join(processing_info)}"
        
        # 处理索引功能
        indexed_line = ""
        index_info = ""
        
        if enable_index:
            if total_lines == 0:
                indexed_line = ""
                index_info = f"索引 {line_index}: 无可用行（文本为空）"
            elif line_index < 0:
                indexed_line = ""
                index_info = f"索引 {line_index}: 无效索引（索引必须从0开始）"
            elif line_index >= total_lines:
                indexed_line = ""
                index_info = f"索引 {line_index}: 超出范围（总共 {total_lines} 行，有效索引: 0-{total_lines-1}）"
            else:
                # 获取指定索引的行（索引从0开始）
                indexed_line = processed_lines[line_index]
                index_info = f"索引 {line_index}: 成功获取内容（共 {total_lines} 行，索引范围: 0-{total_lines-1}）"
        else:
            index_info = "索引功能未启用"
        
        return formatted_prompt, total_lines, line_count_info, original_prompt, indexed_line, index_info, processed_lines


# 节点映射配置
NODE_CLASS_MAPPINGS = {
    "MultilinePromptNode": MultilinePromptNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "MultilinePromptNode": "Multiline Prompt 📝"
}

__all__ = ['MultilinePromptNode', 'NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']