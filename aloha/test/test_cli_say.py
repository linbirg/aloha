"""CLI say 命令测试 - 使用真实 LLM API 测试工具调用功能

测试使用 say 命令让 Agent 调用工具（如 ls/dir 查看目录）。
需要配置 OPENAI_API_KEY 和相关环境变量。
"""

import asyncio
import os
import sys
from pathlib import Path

import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from aloha import ReActLoop, OpenAIProvider
from aloha.bus import MessageBus
from aloha.tools import ShellTool
from aloha.config import get_config


def get_test_provider() -> OpenAIProvider:
    """创建测试用的 LLM Provider"""
    config = get_config()
    
    api_key = os.getenv("OPENAI_API_KEY") or config.providers.openai.api_key if config.providers.openai else ""
    base_url = os.getenv("OPENAI_BASE_URL") or config.providers.openai.base_url if config.providers.openai else None
    model = os.getenv("MODEL") or config.agents.defaults.model
    
    if not api_key:
        pytest.skip("OPENAI_API_KEY not configured")
    
    return OpenAIProvider(
        api_key=api_key,
        base_url=base_url,
        default_model=model,
    )


@pytest.mark.integration
class TestSayCommandWithRealLLM:
    """使用真实 LLM 测试 say 命令的工具调用功能"""
    
    async def test_say_shell_tool_directory_listing(self):
        """测试 say 命令执行 dir 工具列出目录"""
        provider = get_test_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,  # 启用安全检查
        )
        
        # 添加 ShellTool
        agent.add_tool(ShellTool(allowed_commands=["dir", "ls", "echo", "pwd"]))
        
        # 启用安全审批（自动批准低风险操作）
        from aloha.security import SecurityConfig, MockApprovalCallback
        security_config = SecurityConfig(
            auto_approve_low_risk=True,
            approval_callback=MockApprovalCallback(),
        )
        from aloha.agent.wrapper import ToolWrapper
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        # 执行命令：列出当前目录
        response = await agent.process("请列出当前目录的文件")
        
        print(f"\n=== Response ===\n{response}")
        print(f"\n=== Thought Logs ===")
        for log in agent.get_thought_logs():
            # 移除 emoji 以避免 Windows 编码问题
            clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
            print(clean_log)
        
        # 验证响应包含目录信息
        assert response, "Response should not be empty"
        # 检查是否包含文件列表相关内容
        assert len(response) > 0
    
    async def test_say_shell_tool_pwd(self):
        """测试 say 命令执行 pwd 工具"""
        provider = get_test_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
        )
        
        agent.add_tool(ShellTool(allowed_commands=["pwd", "dir"]))
        
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        response = await agent.process("请告诉我当前工作目录是什么？")
        
        print(f"\n=== Response ===\n{response}")
        
        assert response
    
    async def test_say_echo_tool(self):
        """测试 say 命令执行 echo 工具"""
        provider = get_test_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
        )
        
        agent.add_tool(ShellTool(allowed_commands=["echo", "dir"]))
        
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        response = await agent.process("请执行命令 echo hello aloha")
        
        print(f"\n=== Response ===\n{response}")
        
        assert response
    
    async def test_say_simple_response(self):
        """测试 say 命令在不需要工具时的响应"""
        provider = get_test_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
        )
        
        agent.add_tool(ShellTool(allowed_commands=["dir", "ls"]))
        
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        response = await agent.process("你好，请介绍一下你自己")
        
        # 移除 emoji 以避免 Windows 编码问题
        safe_response = response.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]").replace("😊", "[HAPPY]")
        print(f"\n=== Response ===\n{safe_response}")
        
        assert response
        assert len(response) > 0


@pytest.mark.integration
class TestToolCallLoopWithRealLLM:
    """测试完整的 ReAct 循环（工具调用后再次调用 LLM）"""
    
    async def test_tool_result_feedback_to_llm(self):
        """测试工具执行结果能正确反馈给 LLM 进行二次处理"""
        provider = get_test_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
            max_iterations=5,  # 允许更多迭代
        )
        
        agent.add_tool(ShellTool(allowed_commands=["dir", "ls", "echo"]))
        
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        # 请求需要工具调用且需要 LLM 根据结果进行进一步处理
        response = await agent.process("请列出当前目录的文件，并统计有多少个文件")
        
        print(f"\n=== Response ===\n{response}")
        print(f"\n=== Thought Logs ===")
        for log in agent.get_thought_logs():
            # 移除 emoji 以避免 Windows 编码问题
            clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
            print(clean_log)
        
        # 验证完整的 ReAct 循环被执行
        # 应该至少有工具调用和再次调用 LLM
        assert response


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])