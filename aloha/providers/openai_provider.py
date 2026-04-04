"""OpenAI 兼容 Provider 实现

支持 OpenAI、Anthropic、DeepSeek、OpenRouter 等兼容 OpenAI API 的模型。
纯 OpenAI 兼容实现，不包含任何其他 provider 的特定逻辑。
"""

import json
from typing import Any

from openai import AsyncOpenAI

from aloha.providers.base import BaseProvider, Message, Response, ToolCall
from aloha.lib import logger


class OpenAIProvider(BaseProvider):
    """OpenAI 兼容的 LLM Provider

    纯 OpenAI 兼容实现：
    - 不包含 reasoning_split
    - 不包含 reasoning_content 处理
    - 不包含 tool_call_id 规范化
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-4o-mini",
        base_url: str | None = None,
        temperature: float = 0.1,
        max_tokens: int = 8192,
    ):
        super().__init__(api_key, default_model, base_url, temperature, max_tokens)
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def extract_thinking(self, raw_msg) -> str | None:
        """提取标准 thinking 字段

        Args:
            raw_msg: API 返回的原始消息对象

        Returns:
            str | None: thinking 内容
        """
        return getattr(raw_msg, "thinking", None)

    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Response:
        """发送聊天请求

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
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        api_messages = [self.convert_message(m) for m in messages]

        params: dict[str, Any] = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

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

    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> Response:
        """使用工具调用发送聊天请求

        Args:
            messages: 消息列表
            tools: 工具定义列表
            model: 模型名称

        Returns:
            Response: LLM 响应
        """
        return await self.chat(messages, model=model, tools=tools)
