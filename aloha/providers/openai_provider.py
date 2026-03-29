"""OpenAI 兼容 Provider 实现

支持 OpenAI、Anthropic、DeepSeek、OpenRouter、MiniMax 等兼容 OpenAI API 的模型。

注意：MiniMax API 对 tool_call_id 有特殊要求，不应在此处进行规范化。
保持原始 ID 以确保兼容性。
"""

import json
from typing import Any

from openai import AsyncOpenAI

from aloha.providers.base import BaseProvider, Message, Response, ToolCall
from aloha.lib import logger


class OpenAIProvider(BaseProvider):
    """OpenAI 兼容的 LLM Provider"""

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        base_url: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ):
        super().__init__(api_key, default_model, base_url, temperature, max_tokens)

        # 构建默认请求头，支持 MiniMax 等需要 Bearer Token 的 API
        default_headers = {
            "Authorization": f"Bearer {api_key}"
        }

        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers=default_headers,
        )

    def _convert_message(self, msg: Message) -> dict[str, Any]:
        """转换 Message 为 API 格式"""
        result: dict[str, Any] = {
            "role": msg.role,
            "content": msg.content,
        }
        if msg.name:
            result["name"] = msg.name
        if msg.tool_call_id:
            # 不对 tool_call_id 进行规范化，保持原始值
            # MiniMax API 需要原始的 tool_call_id
            result["tool_call_id"] = msg.tool_call_id
        # 添加 thinking/reasoning_details
        if msg.thinking:
            result["reasoning_content"] = msg.thinking
        return result

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Response:
        """发送聊天请求"""
        model = model or self.default_model
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        api_messages = [self._convert_message(m) for m in messages]

        params: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if tools:
            params["tools"] = tools

        resp = await self.client.chat.completions.create(**params)

        choice = resp.choices[0]
        msg = choice.message

        # 提取 thinking (MiniMax 使用 reasoning_details 字段)
        # 注意：OpenAI 兼容 API 可能返回 thinking 字段
        thinking = getattr(msg, "reasoning_details", None) or getattr(msg, "thinking", None)

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

    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """使用工具调用发送聊天请求"""
        return await self.chat(messages, model=model, tools=tools)
