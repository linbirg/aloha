"""ReActLoop - ReAct Agent 主循环

核心处理引擎，负责接收消息、构建上下文、调用 LLM、执行工具。
基于 ReAct (Reasoning + Acting) 设计模式。
"""

import asyncio
import time
from pathlib import Path
from typing import Any

from aloha.agent.base import Agent
from aloha.agent.tools import ToolResult
from aloha.agent.wrapper import ToolWrapper
from aloha.bus.queue import MessageBus, Envelope
from aloha.providers.base import BaseProvider, Message
from aloha.providers.base import Response
from aloha.lib import logger
from aloha.prompts import PromptLoader


class ReActLoop(Agent):
    """ReAct Agent 主循环处理器

    基于 ReAct (Reasoning + Acting) 设计模式。
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
        prompts_dir: Path | str | None = None,
        enable_security: bool = True,
    ):
        # 构建 system prompt：优先使用传入的值，其次尝试从 prompt 文件加载
        final_system_prompt = system_prompt
        # 使用 PromptLoader 加载 prompt 文件
        if prompts_dir:
            prompt_loader = PromptLoader([Path(prompts_dir)])
        else:
            prompt_loader = PromptLoader()

        if final_system_prompt is None:
            final_system_prompt = prompt_loader.build_system_prompt()

        super().__init__(provider, model, max_iterations, final_system_prompt)
        self.bus = bus
        self.workspace = Path(workspace)
        self.context_window_tokens = context_window_tokens
        self.temperature = temperature
        self.thought_logs: list[str] = []  # 思考日志
        self._running = False
        self._prompt_loader = prompt_loader

        # 初始化 ToolWrapper（可选的安全包装器）
        self._tool_wrapper: ToolWrapper | None = None
        if enable_security:
            from aloha.security import SecurityConfig

            self._tool_wrapper = ToolWrapper(
                self.tools, SecurityConfig(), enable_security=True
            )

    async def process(self, user_input: str) -> str:
        """处理单次用户输入

        主循环：
        1. 添加用户消息到 session
        2. 调用 LLM
        3. 如果有工具调用，执行工具并添加工具结果
        4. 重复步骤 2-3 直到没有工具调用或达到最大迭代次数
        """
        # 清空上次的思考日志
        self.thought_logs = []

        # 添加用户消息到记忆
        self.session_memory.add_user_message(user_input)

        # 主循环：直到没有工具调用或达到最大迭代次数
        iteration = 0
        response = None

        while iteration < self.max_iterations:
            iteration += 1

            # 调用 LLM
            response = await self._call_llm()

            # 检查是否有工具调用
            if not response.tool_calls:
                # 没有工具调用，直接返回结果
                break

            # 有工具调用，执行工具
            logger.LOG_DEBUG(
                f"[process] Iteration {iteration}/{self.max_iterations}, tool_calls: {[tc.id for tc in response.tool_calls]}"
            )
            await self._execute_tools(response.tool_calls)

            # 继续循环，再次调用 LLM（处理工具结果）
            # MiniMaxProvider 已经处理了 tool_call_id 规范化问题

        if iteration >= self.max_iterations:
            logger.LOG_DEBUG(
                f"[process] Max iterations ({self.max_iterations}) reached"
            )

        return response.content if response else ""

    def get_thought_logs(self) -> list[str]:
        """获取思考日志"""
        return self.thought_logs.copy()

    def _build_messages(self) -> list[Message]:
        """构建消息列表"""
        messages = []

        # 添加系统提示
        if self.system_prompt:
            messages.append(Message(role="system", content=self.system_prompt))

        # 添加会话历史
        messages.extend(self.session_memory.get_messages())

        return messages

    async def _execute_tools(self, tool_calls) -> None:
        """执行所有工具调用

        依次执行每个工具调用，将结果添加工具消息到 session。
        工具执行异常会作为错误消息添加到 session，然后让 LLM 继续处理。
        """
        for tool_call in tool_calls:
            self.thought_logs.append(f"🛠️ 调用工具: {tool_call.name}")
            self.thought_logs.append(f"📝 参数: {tool_call.arguments}")

            try:
                # 调用纯函数获取结果
                result = await self._execute_tool(tool_call)

                # 统一处理成功和失败情况
                if result.success:
                    self.thought_logs.append(f"✅ 工具结果: {result.content[:200]}...")
                    content = result.content
                    error = False
                else:
                    self.thought_logs.append(f"❌ 工具执行失败: {result.error}")
                    content = f"Error: {result.error}"
                    error = True
            except Exception as e:
                # 工具执行异常
                self.thought_logs.append(f"❌ 工具执行异常: {str(e)}")
                content = f"Error: {str(e)}"
                error = True
                # 工具执行异常，停止执行后续工具
                break

            # 统一添加工具消息到 session
            self.session_memory.add_message(
                role="tool",
                content=content,
                metadata={
                    "tool_call_id": tool_call.id,
                    "tool_name": tool_call.name,
                    "error": error,
                }
                if error
                else {"tool_call_id": tool_call.id, "tool_name": tool_call.name},
            )

    async def _call_llm(self, messages: list[Message] | None = None) -> Response:
        """调用 LLM

        Args:
            messages: 可选的预构建消息列表。如果为 None，则从 session 构建。

        Returns:
            Response: LLM 的响应对象
        """
        # 如果没有提供消息，则从 session 构建
        if messages is None:
            messages = self._build_messages()

        logger.LOG_DEBUG(f"[_call_llm] Sending [{messages}] messages to LLM")

        tools_schema = self.get_tools_schema()

        response = await self.provider.chat_with_tools(
            messages=messages,
            tools=tools_schema if tools_schema else None,
            model=self.model,
        )

        # 添加助手消息到 session（包含 tool_calls 和 thinking 元数据）
        metadata = {}
        if response.tool_calls:
            metadata["tool_calls"] = [
                {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                for tc in response.tool_calls
            ]

        # 处理 thinking：优先使用 response.thinking，否则从 content 中提取
        thinking = response.thinking
        if not thinking and response.content:
            # 从 content 中提取 <think>...</think> 标签中的内容
            import re

            think_match = re.search(
                r"<think>(.*?)</think>", response.content, re.DOTALL
            )
            if think_match:
                thinking = think_match.group(1).strip()
                # 从 content 中移除 thinking 标签，只保留实际回复
                response.content = re.sub(
                    r"<think>.*?</think>", "", response.content, flags=re.DOTALL
                ).strip()

        # 保存 thinking/reasoning_details（M2.7 特性）
        if thinking:
            metadata["thinking"] = thinking
            logger.LOG_DEBUG(f"[_call_llm] Saved thinking: {thinking[:100]}...")
        self.session_memory.add_assistant_message(
            response.content, metadata if metadata else None
        )

        # 记录日志
        self.thought_logs.append(f"🤖 调用 LLM (model: {self.model})...")
        if thinking:
            self.thought_logs.append(f"💬 LLM 思考: {thinking[:100]}...")

        logger.LOG_DEBUG(
            f"[_call_llm] Response content: {response.content}, tool_calls: {len(response.tool_calls) if response.tool_calls else 0}"
        )

        return response

    async def _execute_tool(self, tool_call) -> ToolResult:
        """执行工具调用（纯函数，返回 ToolResult）

        只负责执行工具并返回结果，不修改任何状态，不处理异常。
        异常由上层函数 _handle_response 处理。
        """
        tool_name = tool_call.name
        tool_args = tool_call.arguments

        executor = self.tools
        # 执行工具（优先使用 ToolWrapper）
        if self._tool_wrapper:
            executor = self._tool_wrapper

        result = await executor.execute(tool_name, **tool_args)

        # 直接返回 ToolResult，不做类型转换
        return result

    def set_tool_wrapper(self, wrapper: ToolWrapper) -> None:
        """设置工具包装器

        Args:
            wrapper: ToolWrapper 实例
        """
        self._tool_wrapper = wrapper

    def get_tool_wrapper(self) -> ToolWrapper | None:
        """获取工具包装器

        Returns:
            ToolWrapper 实例或 None
        """
        return self._tool_wrapper

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


class StreamingReActLoop(ReActLoop):
    def __init__(
        self,
        event_manager: Any,
        approval_manager: Any,
        session_id: str,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self._event_manager = event_manager
        self._approval_manager = approval_manager
        self._session_id = session_id

    async def process_streaming(self, user_input: str) -> dict:
        self.thought_logs = []
        self.session_memory.add_user_message(user_input)

        result_messages: list[dict] = []
        final_content = ""
        response = None
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            response = await self._call_llm()

            if response.tool_calls:
                groups = self._group_by_risk(response.tool_calls)
                for batch in groups:
                    approval = self._build_approval(batch)
                    await self._approval_manager.enqueue(approval)

                    queue_size = self._approval_manager._queue.qsize()
                    await self._event_manager.publish(
                        self._session_id,
                        "approval_required",
                        {
                            "approval": self._format_approval(approval),
                            "queue_position": queue_size,
                            "queue_total": queue_size,
                        },
                    )

                    approved = await self._approval_manager.wait(approval.id)
                    if not approved:
                        await self._event_manager.publish(
                            self._session_id,
                            "error",
                            {"message": "工具被拒绝"},
                        )
                        return {"content": final_content, "approved": False}

                    for tc in batch:
                        tc_result = await self._execute_tool(tc)
                        await self._event_manager.publish(
                            self._session_id,
                            "tool_result",
                            {
                                "tool_call_id": tc.id,
                                "success": tc_result.success,
                                "content": tc_result.content,
                            },
                        )

            if not response.tool_calls:
                final_content = response.content
                break

        if response and response.thinking:
            await self._event_manager.publish(
                self._session_id, "thinking", {"content": response.thinking}
            )

        await self._event_manager.publish(
            self._session_id,
            "message",
            {
                "message": {
                    "id": f"msg-assistant-{int(time.time() * 1000)}",
                    "role": "assistant",
                    "content": final_content,
                    "timestamp": int(time.time() * 1000),
                }
            },
        )

        return {"content": final_content, "approved": True}

    def _group_by_risk(self, tool_calls) -> list[list]:
        from aloha.security.policy import RiskLevel

        high, medium, low = [], [], []
        for tc in tool_calls:
            perm = self._build_permission(tc.name, tc.arguments)
            risk = (
                self._tool_wrapper.checker.assess_risk(perm)
                if self._tool_wrapper
                else RiskLevel.MEDIUM
            )
            if risk == RiskLevel.HIGH:
                high.append(tc)
            elif risk == RiskLevel.MEDIUM:
                medium.append(tc)
            else:
                low.append(tc)

        groups = []
        if high:
            groups.append(high)
        if medium:
            groups.append(medium)
        if low:
            groups.append(low)
        return groups

    def _build_permission(self, tool_name: str, kwargs: dict):
        from aloha.security import Permission

        action = kwargs.get("operation", "execute")
        resource = ""
        if tool_name == "file":
            resource = kwargs.get("path", "")
        elif tool_name == "shell":
            resource = kwargs.get("command", "")
        elif tool_name == "web":
            resource = kwargs.get("url", "")

        return Permission(
            tool=tool_name,
            action=action,
            resource=str(resource),
            metadata=kwargs,
        )

    def _build_approval(self, batch: list) -> "ApprovalRequest":
        from aloha.agent.events import ApprovalRequest
        from aloha.security.policy import RiskLevel

        risk_level = RiskLevel.MEDIUM
        resources = []
        descriptions = []
        for tc in batch:
            perm = self._build_permission(tc.name, tc.arguments)
            r = (
                self._tool_wrapper.checker.assess_risk(perm)
                if self._tool_wrapper
                else RiskLevel.MEDIUM
            )
            if r.value > risk_level.value:
                risk_level = r
            args_copy = dict(tc.arguments) if tc.arguments else {}
            args_copy["tool_call_id"] = tc.id
            resources.append(str(perm.resource))
            descriptions.append(f"{tc.name}: {perm.resource}")

        description = "; ".join(descriptions[:3])
        if len(descriptions) > 3:
            description += f" ... 等 {len(descriptions)} 个"

        return ApprovalRequest(
            id=f"appr-{batch[0].id}",
            tool_name=batch[0].name,
            action="batch",
            arguments={"tool_calls": [tc.name for tc in batch]},
            risk_level=risk_level,
            description=description,
            resource=", ".join(resources[:3]),
        )

    def _format_approval(self, approval: "ApprovalRequest") -> dict:
        return approval.to_dict()
