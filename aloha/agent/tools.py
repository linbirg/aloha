"""Agent Tools - Agent 工具模块

提供 Agent 的工具系统：基类、结果类、注册表。
"""

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


class ToolRegistry:
    """工具注册表管理器"""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """注册工具"""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> bool:
        """注销工具"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def get(self, name: str) -> BaseTool | None:
        """获取工具"""
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        """检查工具是否存在"""
        return name in self._tools

    def list_tools(self) -> list[str]:
        """列出所有工具名称"""
        return list(self._tools.keys())

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """获取所有工具的 OpenAI 格式 schema"""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    async def execute_tool(self, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            return {"success": False, "error": f"Tool '{name}' not found"}
        return await tool.execute(**kwargs)

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools