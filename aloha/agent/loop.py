"""ReActLoop - ReAct Agent 主循环

核心处理引擎，负责接收消息、构建上下文、调用 LLM、执行工具。
基于 ReAct (Reasoning + Acting) 设计模式。
"""

import asyncio
from pathlib import Path

from aloha.agent.base import Agent
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
            self._tool_wrapper = ToolWrapper(self.tools, SecurityConfig(), enable_security=True)

    async def process(self, user_input: str) -> str:
        """处理单次用户输入"""
        # 清空上次的思考日志
        self.thought_logs = []
        
        # 添加用户消息到记忆
        self.session_memory.add_user_message(user_input)

        # 构建消息列表
        messages = self._build_messages()

        # 记录 LLM 调用
        self.thought_logs.append(f"🤖 调用 LLM (model: {self.model})...")
        
        # 调用 LLM
        tools_schema = self.get_tools_schema()
        response = await self.provider.chat_with_tools(
            messages=messages,
            tools=tools_schema if tools_schema else None,
            model=self.model,
        )

        # 记录 LLM 回复
        self.thought_logs.append(f"💬 LLM 回复: {response.content[:100]}...")

        # 处理响应
        result = await self._handle_response(response)
        
        return result
    
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

    async def _handle_response(self, response: Response) -> str:
        """处理 LLM 响应"""
        # 添加助手消息到记忆
        self.session_memory.add_assistant_message(response.content)

        # 如果有工具调用，执行工具并循环处理直到没有更多调用
        max_iterations = 5  # 最多执行5次工具调用
        iteration = 0
        
        while response.tool_calls and iteration < max_iterations:
            iteration += 1
            logger.LOG_DEBUG(f"[_handle_response] Iteration {iteration}, tool_calls: {[tc.id for tc in response.tool_calls]}")
            
            # 执行所有工具调用
            tool_execution_failed = False
            for tool_call in response.tool_calls:
                logger.LOG_DEBUG(f"[_handle_response] Executing tool: {tool_call.name}")
                await self._execute_tool(tool_call)
            
            # 检查是否有工具执行失败（通过检查最后一条消息是否为 tool 类型）
            messages = self._build_messages()
            has_tool_result = any(m.role == "tool" for m in messages)
            
            # 如果没有工具结果（执行失败），则停止循环
            if not has_tool_result:
                logger.LOG_DEBUG("[_handle_response] No tool results, stopping loop")
                return "⚠️ 工具执行失败：需要权限审批，但审批超时或被拒绝。请重新发送请求并及时批准。"
            
            # 获取更新后的消息并再次调用 LLM
            logger.LOG_DEBUG(f"[_handle_response] Sending {len(messages)} messages to LLM")
            
            tools_schema = self.get_tools_schema()
            
            response = await self.provider.chat_with_tools(
                messages=messages,
                tools=tools_schema if tools_schema else None,
                model=self.model,
            )
            
            # 添加新的助手消息
            self.session_memory.add_assistant_message(response.content)

        return response.content

    async def _execute_tool(self, tool_call) -> None:
        """执行工具调用"""
        tool_name = tool_call.name
        tool_args = tool_call.arguments
        tool_call_id = tool_call.id  # 记录原始的 tool_call_id

        # 记录工具调用
        self.thought_logs.append(f"🛠️ 调用工具: {tool_name}")
        self.thought_logs.append(f"📝 参数: {tool_args}")
        
        from aloha.lib import logger
        logger.LOG_DEBUG(f"[_execute_tool] tool={tool_name}, tool_call_id={tool_call_id}")

        # 执行工具（优先使用 ToolWrapper）
        if self._tool_wrapper:
            result = await self._tool_wrapper.execute(tool_name, **tool_args)
        else:
            result = await self.tools.execute_tool(tool_name, **tool_args)

        logger.LOG_DEBUG(f"[_execute_tool] Tool result: success={getattr(result, 'success', 'N/A')}")

        # 检查工具是否执行成功
        tool_execution_success = True
        if hasattr(result, "success"):
            if not result.success:
                tool_execution_success = False
        elif isinstance(result, dict):
            if not result.get("success", True):
                tool_execution_success = False

        # 构建工具结果内容
        if hasattr(result, "success"):
            content = result.content if result.success else f"Error: {result.error}"
        elif isinstance(result, dict):
            content = result.get("content", str(result))
            if not result.get("success", True):
                content = f"Error: {result.get('error', content)}"
        else:
            content = str(result)

        # 记录工具结果（包括成功和失败）
        if not tool_execution_success:
            self.thought_logs.append(f"❌ 工具执行失败: {content}")
            logger.LOG_DEBUG("[_execute_tool] Tool execution failed, not adding tool message")
            # 不添加工具消息，避免 MiniMax API 报错
            return
        else:
            self.thought_logs.append(f"✅ 工具结果: {content[:200]}...")

        logger.LOG_DEBUG(f"[_execute_tool] Adding tool message with tool_call_id={tool_call_id}")

        # 添加工具结果到消息（只有成功时才添加）
        self.session_memory.add_message(
            role="tool",
            content=content,
            metadata={"tool_call_id": tool_call_id, "tool_name": tool_name},
        )
        
        # 记录当前消息状态
        logger.LOG_DEBUG(f"[_execute_tool] Tool executed, message added to session")

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
