"""MiniMaxProvider 单元测试"""

import pytest
from aloha.providers.minimax_provider import MiniMaxProvider
from aloha.providers.base import Message


class TestMiniMaxProvider:
    """MiniMaxProvider 测试"""

    @pytest.fixture
    def provider(self):
        """创建测试用的 MiniMaxProvider"""
        return MiniMaxProvider(
            api_key="test-key",
            default_model="MiniMax-M2.7",
            base_url="https://api.minimaxi.com/v1",
        )

    def test_normalize_tool_call_id_short(self, provider):
        """测试短 ID 保持不变"""
        result = provider._normalize_tool_call_id("call12345")
        assert result == "call12345"

    def test_normalize_tool_call_id_long(self, provider):
        """测试长 ID 被 hash 为 9 位"""
        result = provider._normalize_tool_call_id("call_very_long_id_123456789")
        assert len(result) == 9
        assert result.isalnum()

    def test_normalize_tool_call_id_empty(self, provider):
        """测试空 ID"""
        result = provider._normalize_tool_call_id("")
        assert result == ""

    def test_id_mapping_consistency(self, provider):
        """测试同一 ID 映射的一致性"""
        id1 = provider._get_normalized_id("call_abc123")
        id2 = provider._get_normalized_id("call_abc123")
        assert id1 == id2

    def test_id_mapping_different_ids(self, provider):
        """测试不同 ID 映射到不同值"""
        id1 = provider._get_normalized_id("call_abc123")
        id2 = provider._get_normalized_id("call_xyz789")
        assert id1 != id2

    def test_reset_id_map(self, provider):
        """测试重置 ID 映射"""
        provider._get_normalized_id("call_test")
        assert len(provider._id_map) > 0

        provider.reset_id_map()
        assert len(provider._id_map) == 0

    def test_convert_message_tool_role(self, provider):
        """测试转换 tool 角色的消息"""
        msg = Message(
            role="tool",
            content="24℃, sunny",
            tool_call_id="call_very_long_id_123456789",
            name="get_weather",
        )

        result = provider.convert_message(msg)

        assert result["role"] == "tool"
        assert result["content"] == "24℃, sunny"
        assert result["name"] == "get_weather"
        # tool_call_id 应该是规范化的 9 位
        assert len(result["tool_call_id"]) == 9

    def test_convert_message_user_role(self, provider):
        """测试转换 user 角色的消息（不应规范化）"""
        msg = Message(
            role="user",
            content="查询北京天气",
            tool_call_id=None,
        )

        result = provider.convert_message(msg)

        assert result["role"] == "user"
        assert result["content"] == "查询北京天气"
        assert "tool_call_id" not in result

    def test_convert_message_assistant_role(self, provider):
        """测试转换 assistant 角色的消息"""
        msg = Message(
            role="assistant",
            content="我来查询天气",
            tool_call_id="call_123456",  # 已经是 9 位
        )

        result = provider.convert_message(msg)

        assert result["role"] == "assistant"
        # assistant 消息的 tool_call_id 不需要规范化
        assert result.get("tool_call_id") == "call_123456"


class TestMiniMaxProviderIntegration:
    """MiniMaxProvider 集成测试（需要真实 API）"""

    @pytest.mark.integration
    async def test_chat_with_tools(self):
        """测试 chat_with_tools 方法"""
        import os

        api_key = os.getenv("MINIMAX_API_KEY")
        if not api_key:
            pytest.skip("MINIMAX_API_KEY not set")

        provider = MiniMaxProvider(
            api_key=api_key,
            base_url="https://api.minimaxi.com/v1",
            default_model="MiniMax-M2.7",
        )

        # 发送一个简单的请求
        messages = [
            Message(role="user", content="你好"),
        ]

        response = await provider.chat(messages)

        assert response.content is not None
        assert len(response.content) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
