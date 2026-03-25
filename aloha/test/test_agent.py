"""Aloha Agent 测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from aloha import ReactAgent, OpenAIProvider
from aloha.bus import MessageBus, Envelope
from aloha.providers.base import Message, Response, ToolCall
from aloha.memory import SessionMemory, LongTermMemory
from aloha.tools import ToolRegistry
from aloha.tools.base import BaseTool, ToolResult


class MockProvider(OpenAIProvider):
    """Mock Provider 用于测试"""

    def __init__(self):
        # 不调用父类初始化，避免网络请求
        self.api_key = "test-key"
        self.default_model = "gpt-4o-mini"
        self.base_url = None
        self.temperature = 0.1
        self.max_tokens = 8192
        self.client = MagicMock()

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list | None = None,
    ) -> Response:
        """Mock chat 返回简单的响应"""
        return Response(
            content="Mock response",
            model=model or self.default_model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
        )

    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list | None = None,
        model: str | None = None,
    ) -> Response:
        """Mock chat with tools"""
        return await self.chat(messages, model=model, tools=tools)


class EchoTool(BaseTool):
    """Echo 工具用于测试"""

    def __init__(self):
        super().__init__(name="echo", description="返回输入的内容")

    async def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        return ToolResult(success=True, content=f"Echo: {text}")


class TestMemory:
    """测试记忆模块"""

    def test_session_memory_add_message(self):
        """测试添加消息"""
        memory = SessionMemory()
        memory.add_user_message("Hello")
        memory.add_assistant_message("Hi there")

        messages = memory.get_messages()
        assert len(messages) == 2
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"

    def test_session_memory_clear(self):
        """测试清空记忆"""
        memory = SessionMemory()
        memory.add_user_message("Hello")
        memory.clear()

        assert len(memory) == 0

    def test_longterm_memory_add_get(self):
        """测试长期记忆添加和获取"""
        memory = LongTermMemory()
        memory.add("key1", "content1")
        item = memory.get("key1")

        assert item is not None
        assert item.content == "content1"

    def test_longterm_memory_search(self):
        """测试长期记忆搜索"""
        memory = LongTermMemory()
        memory.add("key1", "Python is great")
        memory.add("key2", "JavaScript is fast")

        results = memory.search("Python")
        assert len(results) == 1
        assert "Python" in results[0].content


class TestTools:
    """测试工具模块"""

    def test_tool_registry_register(self):
        """测试工具注册"""
        registry = ToolRegistry()
        tool = EchoTool()
        registry.register(tool)

        assert len(registry) == 1
        assert registry.has("echo")

    def test_tool_registry_execute(self):
        """测试工具执行"""
        registry = ToolRegistry()
        tool = EchoTool()
        registry.register(tool)

        import asyncio
        result = asyncio.run(registry.execute_tool("echo", text="Hello"))

        assert result.success is True
        assert "Hello" in result.content


class TestProvider:
    """测试 Provider"""

    @pytest.mark.asyncio
    async def test_mock_provider_chat(self):
        """测试 Mock Provider"""
        provider = MockProvider()
        messages = [Message(role="user", content="Hello")]

        response = await provider.chat(messages)

        assert response.content == "Mock response"
        assert response.model == "gpt-4o-mini"
        assert response.usage is not None


class TestReactAgent:
    """测试 ReactAgent"""

    @pytest.mark.asyncio
    async def test_agent_process(self):
        """测试 Agent 处理"""
        bus = MessageBus()
        provider = MockProvider()

        agent = ReactAgent(
            bus=bus,
            provider=provider,
            model="gpt-4o-mini",
            system_prompt="You are a helpful assistant.",
        )

        response = await agent.process("Hello")

        assert response == "Mock response"
        assert len(agent.session_memory) > 0

    @pytest.mark.asyncio
    async def test_agent_with_tools(self):
        """测试带工具的 Agent"""
        bus = MessageBus()
        provider = MockProvider()

        agent = ReactAgent(
            bus=bus,
            provider=provider,
            model="gpt-4o-mini",
        )

        # 添加工具
        agent.add_tool(EchoTool())

        tools_schema = agent.get_tools_schema()
        assert len(tools_schema) == 1
        assert tools_schema[0]["function"]["name"] == "echo"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
