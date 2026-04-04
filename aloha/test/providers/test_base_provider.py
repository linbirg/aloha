"""BaseProvider 单元测试"""

import pytest
from aloha.providers.base import BaseProvider, Message


class ConcreteProvider(BaseProvider):
    """Concrete 实现用于测试"""

    def __init__(self):
        super().__init__(
            api_key="test-key",
            default_model="test-model",
            base_url="https://test.com",
            temperature=0.5,
            max_tokens=1024,
        )

    async def chat(
        self, messages, model=None, temperature=None, max_tokens=None, tools=None
    ):
        pass

    async def chat_with_tools(self, messages, tools=None, model=None):
        pass


class TestBaseProviderConvertMessage:
    """测试 BaseProvider.convert_message() 默认实现"""

    @pytest.fixture
    def provider(self):
        return ConcreteProvider()

    def test_convert_user_message(self, provider):
        """测试转换 user 消息"""
        msg = Message(role="user", content="Hello")
        result = provider.convert_message(msg)
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_convert_system_message(self, provider):
        """测试转换 system 消息"""
        msg = Message(role="system", content="You are helpful")
        result = provider.convert_message(msg)
        assert result["role"] == "system"
        assert result["content"] == "You are helpful"

    def test_convert_assistant_message(self, provider):
        """测试转换 assistant 消息"""
        msg = Message(role="assistant", content="I am here")
        result = provider.convert_message(msg)
        assert result["role"] == "assistant"
        assert result["content"] == "I am here"

    def test_convert_tool_message(self, provider):
        """测试转换 tool 消息"""
        msg = Message(role="tool", content="result", tool_call_id="call_123")
        result = provider.convert_message(msg)
        assert result["role"] == "tool"
        assert result["content"] == "result"
        assert result["tool_call_id"] == "call_123"

    def test_convert_with_name(self, provider):
        """测试带 name 字段的转换"""
        msg = Message(role="tool", content="result", name="get_weather")
        result = provider.convert_message(msg)
        assert result["name"] == "get_weather"

    def test_convert_without_name(self, provider):
        """测试不带 name 字段"""
        msg = Message(role="user", content="Hello")
        result = provider.convert_message(msg)
        assert "name" not in result


class TestBaseProviderExtractThinking:
    """测试 BaseProvider.extract_thinking() 默认实现"""

    @pytest.fixture
    def provider(self):
        return ConcreteProvider()

    def test_extract_thinking_returns_none(self, provider):
        """测试默认实现返回 None"""

        class MockRawMsg:
            pass

        result = provider.extract_thinking(MockRawMsg())
        assert result is None

    def test_extract_thinking_ignores_attributes(self, provider):
        """测试默认实现忽略响应对象的 thinking 属性"""

        class MockRawMsg:
            thinking = "some thinking"

        result = provider.extract_thinking(MockRawMsg())
        assert result is None


class TestBaseProviderAttributes:
    """测试 BaseProvider 属性"""

    def test_provider_attributes(self):
        """测试 provider 属性正确设置"""
        provider = ConcreteProvider()
        assert provider.api_key == "test-key"
        assert provider.default_model == "test-model"
        assert provider.base_url == "https://test.com"
        assert provider.temperature == 0.5
        assert provider.max_tokens == 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
