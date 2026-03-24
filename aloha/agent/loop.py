"""AgentLoop - Agent 主循环

核心处理引擎，负责接收消息、构建上下文、调用 LLM、执行工具。
"""

import asyncio
from pathlib import Path

from aloha.agent.base import Agent
from aloha.bus.queue import MessageBus, Envelope
from aloha.providers.base import BaseProvider, Message
from aloha.providers.base import Response
from aloha.lib import logger


class AgentLoop(Agent):
    """Agent 主循环处理器

    基于 nanobot 的 AgentLoop 设计。
    """

    def __init__(
        self,
        bus: MessageBus,
        provider: BaseProvider,
        workspace: Path | str = Path("~/.aloha/workspace").expanduser(),
        model: str = "gpt-4o-mini",
        max_iterations: int = 40,
        context_window_tokens: int = 65536,
        temperature: float = 0.1,
        system_prompt: str | None = None,
    ):
        super().__init__(provider, model, max_iterations, system_prompt)
        self.bus = bus
        self.workspace = Path(workspace)
        self.context_window_tokens = context_window_tokens
        self.temperature = temperature
        self._running = False

    async def process(self, user_input: str) -> str:
        """处理单次用户输入"""
        # 添加用户消息到记忆
        self.session_memory.add_user_message(user_input)

        # 构建消息列表
        messages = self._build_messages()

        # 调用 LLM
        tools_schema = self.get_tools_schema()
        response = await self.provider.chat_with_tools(
            messages=messages,
            tools=tools_schema if tools_schema else None,
            model=self.model,
        )

        # 处理响应
        result = await self._handle_response(response)
        return result

    def _build_messages(self) -> list[Message]:
        """构建消息列表"""
        messages = []

        # 添加系统提示
        if self.system_prompt:
            messages.append(Message(role="system", content=self.system_prompt))

        # 添加会话历史
        messages.extend(self.session_memory.get_messages())

        return messages

    async def _handle_response(self, response: Response) -> str:
        """处理 LLM 响应"""
        # 添加助手消息到记忆
        self.session_memory.add_assistant_message(response.content)

        # 如果有工具调用，执行工具
        if response.tool_calls:
            for tool_call in response.tool_calls:
                await self._execute_tool(tool_call)

        return response.content

    async def _execute_tool(self, tool_call) -> None:
        """执行工具调用"""
        tool_name = tool_call.name
        tool_args = tool_call.arguments

        # 执行工具
        result = await self.tools.execute_tool(tool_name, **tool_args)

        # 添加工具结果到消息
        if isinstance(result, dict):
            content = result.get("content", str(result))
            if not result.get("success", True):
                content = f"Error: {result.get('error', content)}"
        else:
            content = str(result)

        self.session_memory.add_message(
            role="tool",
            content=content,
            metadata={"tool_call_id": tool_call.id, "tool_name": tool_name},
        )

    async def run(self) -> None:
        """运行 agent 主循环"""
        self._running = True
        while self._running:
            # 从消息队列接收消息
            envelope = await self.bus.receive("agent", timeout=1.0)
            if envelope:
                response = await self.process(envelope.content)
                # 发送响应
                await self.bus.send(
                    envelope.sender,
                    Envelope(
                        id=f"resp-{envelope.id}",
                        sender="agent",
                        recipient=envelope.sender,
                        content=response,
                    ),
                )

    def stop(self) -> None:
        """停止 agent"""
        self._running = False
