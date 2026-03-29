"""Session Memory - 会话记忆

管理单个对话会话中的消息历史。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aloha.providers.base import Message, ToolCall


@dataclass
class SessionMessage:
    """会话消息"""
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionMemory:
    """会话记忆管理器"""

    def __init__(self, max_messages: int = 100, max_tokens: int | None = None):
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self.messages: list[SessionMessage] = []

    def add_user_message(self, content: str) -> None:
        """添加用户消息"""
        self.messages.append(SessionMessage(role="user", content=content))

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加助手消息"""
        self.messages.append(
            SessionMessage(role="assistant", content=content, metadata=metadata or {})
        )

    def add_message(self, role: str, content: str, metadata: dict[str, Any] | None = None) -> None:
        """添加任意消息"""
        self.messages.append(
            SessionMessage(role=role, content=content, metadata=metadata or {})
        )

    def get_messages(self) -> list[Message]:
        """获取消息列表（用于 LLM 调用）"""
        result = []
        for m in self.messages:
            msg = Message(
                role=m.role,
                content=m.content,
                tool_call_id=m.metadata.get("tool_call_id") if m.role == "tool" else None,
            )
            # 对于 tool 消息，需要设置 name 字段（工具名称）
            if m.role == "tool" and m.metadata.get("tool_name"):
                msg.name = m.metadata["tool_name"]
            # 对于 assistant 消息，如果有 tool_calls 元数据，需要恢复 tool_calls
            if m.role == "assistant" and m.metadata.get("tool_calls"):
                tool_calls_data = m.metadata["tool_calls"]
                msg.tool_calls = [
                    ToolCall(
                        id=tc["id"],
                        name=tc["name"],
                        arguments=tc.get("arguments", {})
                    )
                    for tc in tool_calls_data
                ]
            # 恢复 thinking/reasoning_details
            if m.role == "assistant" and m.metadata.get("thinking"):
                msg.thinking = m.metadata["thinking"]
            result.append(msg)
        return result

    def clear(self) -> None:
        """清空会话记忆"""
        self.messages.clear()

    def __len__(self) -> int:
        return len(self.messages)
