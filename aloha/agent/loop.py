"""ReActLoop - ReAct Agent 主循环

核心处理引擎，负责接收消息、构建上下文、调用 LLM、执行工具。
基于 ReAct (Reasoning + Acting) 设计模式。
"""

import asyncio
from pathlib import Path

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
            self._tool_wrapper = ToolWrapper(self.tools, SecurityConfig(), enable_security=True)

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
            logger.LOG_DEBUG(f"[process] Iteration {iteration}/{self.max_iterations}, tool_calls: {[tc.id for tc in response.tool_calls]}")
            await self._execute_all_tools(response.tool_calls)
            
            # 继续循环，再次调用 LLM（处理工具结果）
            # MiniMaxProvider 已经处理了 tool_call_id 规范化问题
        
        if iteration >= self.max_iterations:
            logger.LOG_DEBUG(f"[process] Max iterations ({self.max_iterations}) reached")
        
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

    async def _execute_all_tools(self, tool_calls) -> None:
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
                metadata={"tool_call_id": tool_call.id, "tool_name": tool_call.name, "error": error} if error else {"tool_call_id": tool_call.id, "tool_name": tool_call.name},
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
        # 保存 thinking/reasoning_details（M2.7 特性）
        if response.thinking:
            metadata["thinking"] = response.thinking
            logger.LOG_DEBUG(f"[_call_llm] Saved thinking: {response.thinking[:100]}...")
        self.session_memory.add_assistant_message(response.content, metadata if metadata else None)
        
        # 记录日志
        self.thought_logs.append(f"🤖 调用 LLM (model: {self.model})...")
        self.thought_logs.append(f"💬 LLM 回复: {response.content[:100]}...")
        
        logger.LOG_DEBUG(f"[_call_llm] Response content: {response.content}, tool_calls: {len(response.tool_calls) if response.tool_calls else 0}")
        
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
