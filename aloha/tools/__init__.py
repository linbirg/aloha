"""Aloha Tools 模块

存放系统自带工具（文件读写、命令执行、Web访问等）。
从 agent.tools 导入以保持向后兼容。
"""

from aloha.agent.tools import BaseTool, ToolResult, ToolMetadata, ToolRegistry

__all__ = ["BaseTool", "ToolResult", "ToolMetadata", "ToolRegistry"]
