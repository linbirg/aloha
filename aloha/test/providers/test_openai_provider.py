"""OpenAIProvider 单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aloha.providers.openai_provider import OpenAIProvider
from aloha.providers.base import Message


class TestOpenAIProviderConvertMessage:
    """测试 OpenAIProvider.convert_message()"""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(
            api_key="test-key",
            default_model="gpt-4o-mini",
        )

    def test_convert_user_message(self, provider):
        """测试转换 user 消息"""
        msg = Message(role="user", content="Hello")
        result = provider.convert_message(msg)
        assert result["role"] == "user"
        assert result["content"] == "Hello"

    def test_convert_preserves_original_tool_call_id(self, provider):
        """测试保留原始 tool_call_id（不规范化）"""
        msg = Message(
            role="tool", content="result", tool_call_id="call_very_long_id_123456789"
        )
        result = provider.convert_message(msg)
        assert result["tool_call_id"] == "call_very_long_id_123456789"

    def test_convert_with_name(self, provider):
        """测试带 name 字段"""
        msg = Message(role="tool", content="result", name="get_weather")
        result = provider.convert_message(msg)
        assert result["name"] == "get_weather"

    def test_convert_does_not_add_reasoning_content(self, provider):
        """测试不添加 reasoning_content"""
        msg = Message(role="user", content="Hello", thinking="I am thinking")
        result = provider.convert_message(msg)
        assert "reasoning_content" not in result

    def test_convert_with_thinking_field(self, provider):
        """测试 thinking 字段不被处理（由 extract_thinking 处理）"""
        msg = Message(role="assistant", content="Response", thinking="My thoughts")
        result = provider.convert_message(msg)
        assert "reasoning_content" not in result


class TestOpenAIProviderExtractThinking:
    """测试 OpenAIProvider.extract_thinking()"""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key")

    def test_extract_standard_thinking(self, provider):
        """测试提取标准 thinking 字段"""

        class MockMsg:
            thinking = "I am thinking"

        result = provider.extract_thinking(MockMsg())
        assert result == "I am thinking"

    def test_extract_no_thinking(self, provider):
        """测试无 thinking 时返回 None"""

        class MockMsg:
            content = "Hello"

        result = provider.extract_thinking(MockMsg())
        assert result is None

    def test_extract_ignores_reasoning_content(self, provider):
        """测试忽略 reasoning_content 字段"""

        class MockMsg:
            reasoning_content = "MiniMax thinking"
            thinking = None

        result = provider.extract_thinking(MockMsg())
        assert result is None

    def test_extract_ignores_reasoning_details(self, provider):
        """测试忽略 reasoning_details 字段"""

        class MockMsg:
            reasoning_details = "details"
            thinking = None

        result = provider.extract_thinking(MockMsg())
        assert result is None


class TestOpenAIProviderSeparation:
    """测试 OpenAIProvider 与 MiniMax 分离"""

    def test_no_reasoning_split_attribute(self):
        """验证 OpenAIProvider 不包含 reasoning_split"""
        provider = OpenAIProvider(api_key="test-key")
        assert not hasattr(provider, "reasoning_split")

    def test_no_id_map_attribute(self):
        """验证 OpenAIProvider 没有 _id_map"""
        provider = OpenAIProvider(api_key="test-key")
        assert not hasattr(provider, "_id_map")

    def test_no_normalize_id_method(self):
        """验证 OpenAIProvider 没有 _normalize_tool_call_id"""
        provider = OpenAIProvider(api_key="test-key")
        assert not hasattr(provider, "_normalize_tool_call_id")

    def test_no_reset_id_map_method(self):
        """验证 OpenAIProvider 没有 reset_id_map"""
        provider = OpenAIProvider(api_key="test-key")
        assert not hasattr(provider, "reset_id_map")


class TestOpenAIProviderChat:
    """测试 OpenAIProvider.chat()"""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_chat_calls_convert_message(self, provider):
        """测试 chat 调用 convert_message"""
        msg = Message(role="user", content="Hello")

        with patch.object(provider, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.model = "gpt-4o-mini"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hi"
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage = MagicMock(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.chat([msg])

            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_without_tools_no_extra_body(self, provider):
        """测试无工具时不发送 extra_body"""
        msg = Message(role="user", content="Hello")

        with patch.object(provider, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.model = "gpt-4o-mini"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hi"
            mock_response.choices[0].message.thinking = None
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage = MagicMock(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.chat([msg])

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert "extra_body" not in call_kwargs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
