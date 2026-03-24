"""Base Tool - 工具基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    content: str
    error: str | None = None
    metadata: dict[str, Any] | None = None


class BaseTool(ABC):
    """工具抽象基类"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, *args, **kwargs) -> ToolResult:
        """执行工具"""
        pass

    def to_openai_schema(self) -> dict[str, Any]:
        """转换为 OpenAI 工具格式"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._get_parameters_schema(),
            },
        }

    def _get_parameters_schema(self) -> dict[str, Any]:
        """获取参数 schema（子类可重写）"""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }


class ToolMetadata:
    """工具元数据"""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }
