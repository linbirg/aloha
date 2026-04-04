"""MiniMaxProvider 单元测试"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aloha.providers.minimax_provider import MiniMaxProvider
from aloha.providers.base import Message, ToolCall


class TestMiniMaxProviderIdNormalization:
    """测试 MiniMax ID 规范化"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    def test_normalize_short_id(self, provider):
        """测试短 ID 保持不变"""
        result = provider._normalize_tool_call_id("call12345")
        assert result == "call12345"

    def test_normalize_already_9_chars(self, provider):
        """测试已经是 9 位字母数字的 ID 保持不变"""
        result = provider._normalize_tool_call_id("abc123xyz")
        assert result == "abc123xyz"

    def test_normalize_long_id(self, provider):
        """测试长 ID hash 为 9 位"""
        result = provider._normalize_tool_call_id("call_very_long_id_123456789")
        assert len(result) == 9
        assert result.isalnum()

    def test_normalize_idempotent(self, provider):
        """测试幂等性：相同输入 → 相同输出"""
        id1 = provider._normalize_tool_call_id("call_test_id")
        id2 = provider._normalize_tool_call_id("call_test_id")
        assert id1 == id2

    def test_normalize_empty_id(self, provider):
        """测试空 ID 返回空"""
        result = provider._normalize_tool_call_id("")
        assert result == ""

    def test_normalize_preserves_alphanumeric(self, provider):
        """测试保留字母数字"""
        result = provider._normalize_tool_call_id("abc123XYZ")
        assert result == "abc123XYZ"


class TestMiniMaxProviderIdMapping:
    """测试 MiniMax ID 映射"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    def test_mapping_consistency(self, provider):
        """测试同一 ID 映射的一致性"""
        id1 = provider._get_normalized_id("call_abc")
        id2 = provider._get_normalized_id("call_abc")
        assert id1 == id2

    def test_different_ids_map_differently(self, provider):
        """测试不同 ID 映射不同"""
        id1 = provider._get_normalized_id("call_abc")
        id2 = provider._get_normalized_id("call_xyz")
        assert id1 != id2

    def test_reset_id_map(self, provider):
        """测试重置 ID 映射"""
        provider._get_normalized_id("call_test")
        assert len(provider._id_map) > 0

        provider.reset_id_map()
        assert len(provider._id_map) == 0

    def test_reset_id_map_idempotent(self, provider):
        """测试 reset_id_map 幂等性"""
        provider._get_normalized_id("call_test")
        provider.reset_id_map()
        provider.reset_id_map()  # 再次调用
        assert len(provider._id_map) == 0


class TestMiniMaxProviderConvertMessage:
    """测试 MiniMaxProvider.convert_message()"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    def test_convert_adds_reasoning_content(self, provider):
        """测试添加 reasoning_content"""
        msg = Message(role="user", content="Hello", thinking="I am thinking")
        result = provider.convert_message(msg)
        assert result["reasoning_content"] == "I am thinking"

    def test_convert_normalizes_tool_call_id(self, provider):
        """测试规范化 tool 消息的 tool_call_id"""
        msg = Message(
            role="tool",
            content="24℃",
            tool_call_id="call_very_long_id_123456789",
        )
        result = provider.convert_message(msg)
        assert len(result["tool_call_id"]) == 9

    def test_convert_normalizes_assistant_tool_calls(self, provider):
        """测试规范化 assistant 消息的 tool_calls"""
        msg = Message(
            role="assistant",
            content="我来查天气",
            tool_calls=[
                ToolCall(
                    id="call_very_long_id_123456789",
                    name="get_weather",
                    arguments={"location": "北京"},
                )
            ],
        )
        result = provider.convert_message(msg)
        assert len(result["tool_calls"]) == 1
        assert len(result["tool_calls"][0]["id"]) == 9

    def test_convert_does_not_affect_user_message(self, provider):
        """测试不影响 user 消息"""
        msg = Message(role="user", content="Hello")
        result = provider.convert_message(msg)
        assert result["role"] == "user"
        assert result["content"] == "Hello"
        assert "tool_call_id" not in result

    def test_convert_preserves_short_id(self, provider):
        """测试保留已经是 9 位的 ID"""
        msg = Message(
            role="tool",
            content="result",
            tool_call_id="call12345",  # 9位
        )
        result = provider.convert_message(msg)
        assert result["tool_call_id"] == "call12345"

    def test_convert_multiple_tool_calls(self, provider):
        """测试多个 tool_calls 都规范化"""
        msg = Message(
            role="assistant",
            content="我来查天气",
            tool_calls=[
                ToolCall(
                    id="call_abc123", name="get_weather", arguments={"location": "北京"}
                ),
                ToolCall(id="call_xyz789", name="get_time", arguments={"tz": "UTC"}),
            ],
        )
        result = provider.convert_message(msg)
        assert len(result["tool_calls"]) == 2
        for tc in result["tool_calls"]:
            assert len(tc["id"]) == 9


class TestMiniMaxProviderExtractThinking:
    """测试 MiniMaxProvider.extract_thinking()"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    def test_extract_reasoning_content(self, provider):
        """测试提取 reasoning_content"""

        class MockMsg:
            reasoning_content = "MiniMax reasoning"

        result = provider.extract_thinking(MockMsg())
        assert result == "MiniMax reasoning"

    def test_extract_reasoning_details(self, provider):
        """测试提取 reasoning_details"""

        class MockMsg:
            reasoning_details = "details here"

        result = provider.extract_thinking(MockMsg())
        assert result == "details here"

    def test_extract_standard_thinking_fallback(self, provider):
        """测试回退到标准 thinking"""

        class MockMsg:
            thinking = "standard thinking"

        result = provider.extract_thinking(MockMsg())
        assert result == "standard thinking"

    def test_extract_priority_reasoning_content(self, provider):
        """测试 reasoning_content 优先于 reasoning_details"""

        class MockMsg:
            reasoning_content = "content"
            reasoning_details = "details"

        result = provider.extract_thinking(MockMsg())
        assert result == "content"

    def test_extract_priority_details_over_thinking(self, provider):
        """测试 reasoning_details 优先于 thinking"""

        class MockMsg:
            reasoning_details = "details"
            thinking = "thinking"

        result = provider.extract_thinking(MockMsg())
        assert result == "details"

    def test_extract_no_thinking(self, provider):
        """测试无 thinking 时返回 None"""

        class MockMsg:
            content = "Hello"

        result = provider.extract_thinking(MockMsg())
        assert result is None


class TestMiniMaxProviderChat:
    """测试 MiniMaxProvider.chat()"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    @pytest.mark.asyncio
    async def test_chat_without_tools_sends_reasoning_split(self, provider):
        """测试无工具调用时发送 reasoning_split"""
        msg = Message(role="user", content="Hello")

        with patch.object(provider, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.model = "MiniMax-M2.7"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hi"
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage = MagicMock(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.chat([msg])

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert "extra_body" in call_kwargs
            assert call_kwargs["extra_body"]["reasoning_split"] is True

    @pytest.mark.asyncio
    async def test_chat_with_tools_no_reasoning_split(self, provider):
        """测试有工具时不发送 reasoning_split"""
        msg = Message(role="user", content="Hello")
        tools = [{"type": "function", "function": {"name": "test", "parameters": {}}}]

        with patch.object(provider, "client") as mock_client:
            mock_response = MagicMock()
            mock_response.model = "MiniMax-M2.7"
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hi"
            mock_response.choices[0].message.tool_calls = None
            mock_response.choices[0].finish_reason = "stop"
            mock_response.usage = MagicMock(
                prompt_tokens=10, completion_tokens=5, total_tokens=15
            )
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            await provider.chat([msg], tools=tools)

            call_kwargs = mock_client.chat.completions.create.call_args[1]
            assert "extra_body" not in call_kwargs


class TestMiniMaxProviderSeparation:
    """测试 MiniMaxProvider 特有属性"""

    def test_has_id_map(self):
        """验证 MiniMaxProvider 有 _id_map"""
        provider = MiniMaxProvider(api_key="test-key")
        assert hasattr(provider, "_id_map")
        assert isinstance(provider._id_map, dict)

    def test_has_normalize_id_method(self):
        """验证 MiniMaxProvider 有 _normalize_tool_call_id"""
        provider = MiniMaxProvider(api_key="test-key")
        assert hasattr(provider, "_normalize_tool_call_id")

    def test_has_reset_id_map_method(self):
        """验证 MiniMaxProvider 有 reset_id_map"""
        provider = MiniMaxProvider(api_key="test-key")
        assert hasattr(provider, "reset_id_map")

    def test_inherits_from_openai_provider(self):
        """验证继承自 OpenAIProvider"""
        provider = MiniMaxProvider(api_key="test-key")
        from aloha.providers.openai_provider import OpenAIProvider

        assert isinstance(provider, OpenAIProvider)


class TestMiniMaxProviderIdempotency:
    """测试 MiniMaxProvider 幂等性"""

    @pytest.fixture
    def provider(self):
        return MiniMaxProvider(api_key="test-key")

    def test_convert_message_idempotent(self, provider):
        """测试 convert_message 幂等性"""
        msg = Message(
            role="tool",
            content="result",
            tool_call_id="call_test_id",
        )

        result1 = provider.convert_message(msg)
        result2 = provider.convert_message(msg)
        assert result1["tool_call_id"] == result2["tool_call_id"]

    def test_reset_id_map_idempotent(self, provider):
        """测试 reset_id_map 多次调用安全"""
        provider._get_normalized_id("call_test")
        provider.reset_id_map()
        provider.reset_id_map()  # 再次调用
        assert len(provider._id_map) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
