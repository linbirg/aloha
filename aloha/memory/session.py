"""Session Memory - 会话记忆

管理单个对话会话中的消息历史。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from aloha.providers.base import Message


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
        return [
            Message(
                role=m.role,
                content=m.content,
                tool_call_id=m.metadata.get("tool_call_id") if m.role == "tool" else None,
            )
            for m in self.messages
        ]

    def clear(self) -> None:
        """清空会话记忆"""
        self.messages.clear()

    def __len__(self) -> int:
        return len(self.messages)
