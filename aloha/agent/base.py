"""Agent 基类定义"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from aloha.providers.base import BaseProvider
from aloha.memory import SessionMemory, LongTermMemory
from aloha.agent.tools import ToolRegistry


class Agent(ABC):
    """Agent 抽象基类"""

    def __init__(
        self,
        provider: BaseProvider,
        model: str = "gpt-4o-mini",
        max_iterations: int = 40,
        system_prompt: str | None = None,
    ):
        self.provider = provider
        self.model = model
        self.max_iterations = max_iterations
        self.system_prompt = system_prompt
        self.session_memory = SessionMemory()
        self.longterm_memory = LongTermMemory()
        self.tools = ToolRegistry()

    @abstractmethod
    async def process(self, user_input: str) -> str:
        """处理用户输入"""
        pass

    @abstractmethod
    async def run(self) -> None:
        """运行 agent"""
        pass

    def reset(self) -> None:
        """重置 agent 状态"""
        self.session_memory.clear()

    def add_tool(self, tool) -> None:
        """添加工具"""
        self.tools.register(tool)

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """获取工具 schema"""
        return self.tools.get_tools_schema()
    
    def list_tools(self) -> list[str]:
        """列出所有已注册的工具名称"""
        return self.tools.list_tools()
