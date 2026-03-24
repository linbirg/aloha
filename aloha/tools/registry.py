"""Tool Registry - 工具注册表"""

from typing import Any

from aloha.tools.base import BaseTool


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
