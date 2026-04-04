"""MiniMax 专用 Provider 实现

MiniMax 特有逻辑：
- tool_call_id 规范化为固定 9 位字母数字
- reasoning_split 分离思考内容
- reasoning_content 字段提取
"""

import hashlib
import json
from typing import Any

from aloha.providers.base import Message, Response, ToolCall
from aloha.providers.openai_provider import OpenAIProvider
from aloha.lib import logger


class MiniMaxProvider(OpenAIProvider):
    """MiniMax 专用 Provider

    MiniMax 特有逻辑（与 OpenAIProvider 解耦）：
    - ID 规范化：tool_call_id 规范化为 9 位
    - reasoning_split：通过 extra_body 启用
    - reasoning_content：从响应中提取思考内容
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "MiniMax-M2.7",
        base_url: str | None = "https://api.minimaxi.com/v1",
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ):
        super().__init__(
            api_key=api_key,
            default_model=default_model,
            base_url=base_url,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._id_map: dict[str, str] = {}
        logger.LOG_INFO("[MiniMaxProvider] Initialized")

    @staticmethod
    def _normalize_tool_call_id(tool_call_id: str) -> str:
        """规范化 tool_call_id 为固定 9 位字母数字（幂等）

        Args:
            tool_call_id: 原始 tool_call_id

        Returns:
            str: 规范化后的 9 位 ID
        """
        if not tool_call_id:
            return tool_call_id
        if len(tool_call_id) == 9 and tool_call_id.isalnum():
            return tool_call_id
        return hashlib.sha1(tool_call_id.encode()).hexdigest()[:9]

    def _get_normalized_id(self, original_id: str) -> str:
        """获取规范化后的 ID，建立映射确保一致性（幂等）

        Args:
            original_id: 原始 ID

        Returns:
            str: 规范化后的 ID
        """
        if original_id not in self._id_map:
            self._id_map[original_id] = self._normalize_tool_call_id(original_id)
            logger.LOG_DEBUG(
                f"[MiniMaxProvider] ID mapping: {original_id[:20]}... -> {self._id_map[original_id]}"
            )
        return self._id_map[original_id]

    def reset_id_map(self) -> None:
        """重置 ID 映射表（幂等操作）

        在新会话开始时调用。
        """
        self._id_map.clear()
        logger.LOG_DEBUG("[MiniMaxProvider] ID mapping reset")

    def convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 Message 为 API 格式，添加 MiniMax 特有处理

        处理内容：
        1. tool 消息的 tool_call_id 规范化
        2. assistant 消息的 tool_calls 规范化
        3. reasoning_content 字段

        Args:
            msg: 消息对象

        Returns:
            dict: API 请求格式
        """
        result = super().convert_message(msg)

        if msg.role == "tool" and msg.tool_call_id:
            result["tool_call_id"] = self._get_normalized_id(msg.tool_call_id)
            logger.LOG_DEBUG(
                f"[MiniMaxProvider] Tool message normalized ID: {result['tool_call_id']}"
            )

        if msg.role == "assistant" and msg.tool_calls:
            result["tool_calls"] = [
                {
                    "id": self._get_normalized_id(tc.id),
                    "type": "function",
                    "function": {
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments)
                        if isinstance(tc.arguments, dict)
                        else tc.arguments,
                    },
                }
                for tc in msg.tool_calls
            ]
            logger.LOG_DEBUG(
                f"[MiniMaxProvider] Assistant message normalized {len(msg.tool_calls)} tool_calls"
            )

        if msg.thinking:
            result["reasoning_content"] = msg.thinking
            logger.LOG_DEBUG("[MiniMaxProvider] Added reasoning_content to message")

        return result

    def extract_thinking(self, raw_msg) -> str | None:
        """从 API 响应中提取 reasoning_content

        MiniMax 使用 reasoning_content 或 reasoning_details 字段。

        Args:
            raw_msg: API 返回的原始消息对象

        Returns:
            str | None: thinking 内容
        """
        return (
            getattr(raw_msg, "reasoning_content", None)
            or getattr(raw_msg, "reasoning_details", None)
            or getattr(raw_msg, "thinking", None)
        )

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Response:
        """发送聊天请求（MiniMax 特有实现）

        MiniMax 特有：
        - 无工具调用时启用 reasoning_split

        Args:
            messages: 消息列表
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大 token 数
            tools: 工具定义列表

        Returns:
            Response: LLM 响应
        """
        model = model or self.default_model

        api_messages = [self.convert_message(m) for m in messages]

        params: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }

        if not tools:
            params["extra_body"] = {"reasoning_split": True}
            logger.LOG_DEBUG("[MiniMaxProvider] Using reasoning_split=True")

        if tools:
            params["tools"] = tools

        resp = await self.client.chat.completions.create(**params)

        logger.LOG_DEBUG(
            f"[chat] Raw response (first 500): {resp.model_dump_json(exclude={'usage'})[:500]}"
        )

        choice = resp.choices[0]
        msg = choice.message

        thinking = self.extract_thinking(msg)

        tool_calls: list[ToolCall] | None = None
        if msg.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),
                )
                for tc in msg.tool_calls
            ]

        return Response(
            content=msg.content or "",
            tool_calls=tool_calls,
            model=resp.model,
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
            finish_reason=choice.finish_reason,
            thinking=thinking,
        )
