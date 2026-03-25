"""OpenAI 兼容 Provider 实现

支持 OpenAI、Anthropic、DeepSeek、OpenRouter、MiniMax 等兼容 OpenAI API 的模型。
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

        # 调试：打印 API 配置信息
        # print(f"[Debug] OpenAIProvider initialized:")
        # print(f"  api_key: {api_key[:20]}..." if len(api_key) > 20 else f"  api_key: {api_key}")
        # print(f"  base_url: {base_url}")
        # print(f"  default_model: {default_model}")

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
            result["tool_call_id"] = msg.tool_call_id
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
        )

    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """使用工具调用发送聊天请求"""
        return await self.chat(messages, model=model, tools=tools)
