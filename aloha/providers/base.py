"""Aloha LLM Provider 基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """聊天消息"""

    role: str  # "system", "user", "assistant", "tool"
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list["ToolCall"] | None = None  # assistant 消息中的工具调用
    thinking: str | None = None  # 思考内容


@dataclass
class ToolCall:
    """工具调用"""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Response:
    """LLM 响应"""

    content: str
    tool_calls: list[ToolCall] | None = None
    model: str | None = None
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    thinking: str | None = None


class BaseProvider(ABC):
    """LLM Provider 基类

    提供通用的消息转换和 thinking 提取钩子方法。
    子类通过覆盖这些方法实现特定 provider 的行为。
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        base_url: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ):
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens

    def convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 Message 为 API 请求格式（子类可覆盖）

        Args:
            msg: 消息对象

        Returns:
            dict: API 请求格式的消息
        """
        result: dict[str, Any] = {
            "role": msg.role,
            "content": msg.content,
        }
        if msg.name:
            result["name"] = msg.name
        if msg.tool_call_id:
            result["tool_call_id"] = msg.tool_call_id
        return result

    def extract_thinking(self, raw_msg) -> str | None:
        """从 API 响应中提取 thinking（子类可覆盖）

        默认实现返回 None，子类覆盖以提取特定格式的 thinking。

        Args:
            raw_msg: API 返回的原始消息对象

        Returns:
            str | None: thinking 内容
        """
        return None

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Response:
        """发送聊天请求"""
        pass

    @abstractmethod
    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """使用工具调用发送聊天请求"""
        pass
