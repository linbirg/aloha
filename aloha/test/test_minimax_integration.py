"""MiniMax Provider 集成测试

使用 MiniMaxProvider 进行端到端测试，验证 tool_call_id 规范化是否正常工作。
"""

import os
import pytest
from pathlib import Path

from aloha import ReActLoop, MiniMaxProvider
from aloha.bus import MessageBus
from aloha.tools import ShellTool
from aloha.config import get_config


def get_minimax_provider() -> MiniMaxProvider:
    """创建测试用的 MiniMaxProvider"""
    config = get_config()
    
    # 直接从环境变量读取，优先级最高
    api_key = os.environ.get("MINI_MAX_API") or os.environ.get("OPENAI_API_KEY")
    
    # 如果环境变量没有，尝试从配置文件读取
    if not api_key and config.providers.openai:
        api_key = config.providers.openai.api_key
    
    base_url = os.environ.get("OPENAI_BASE_URL") or "https://api.minimaxi.com/v1"
    model = os.environ.get("MODEL") or "MiniMax-M2.7"
    
    if not api_key:
        pytest.skip("MINIMAX_API_KEY or OPENAI_API_KEY not configured")
    
    return MiniMaxProvider(
        api_key=api_key,
        base_url=base_url,
        default_model=model,
    )


@pytest.mark.integration
class TestMiniMaxProviderIntegration:
    """使用 MiniMaxProvider 进行端到端集成测试"""
    
    async def test_tool_call_with_minimax_provider(self):
        """测试使用 MiniMaxProvider 进行工具调用"""
        provider = get_minimax_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
            max_iterations=3,
        )
        
        # 添加 ShellTool
        agent.add_tool(ShellTool(allowed_commands=["dir", "ls", "echo", "pwd"]))
        
        # 配置安全审批
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(
            auto_approve_low_risk=True,
            approval_callback=MockApprovalCallback(),
        )
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        # 执行命令
        response = await agent.process("请执行命令 echo hello aloha")
        
        print(f"\n=== Response ===\n{response}")
        print(f"\n=== Thought Logs ===")
        for log in agent.get_thought_logs():
            # 移除 emoji 以避免 Windows 编码问题
            clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
            print(clean_log)
        
        # 验证响应
        assert response, "Response should not be empty"
    
    async def test_full_react_loop_with_minimax(self):
        """测试完整的 ReAct 循环（工具调用后再次调用 LLM）"""
        provider = get_minimax_provider()
        bus = MessageBus()
        
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=Path("."),
            model=provider.default_model,
            enable_security=True,
            max_iterations=5,
        )
        
        agent.add_tool(ShellTool(allowed_commands=["dir", "ls", "echo"]))
        
        from aloha.security import SecurityConfig, MockApprovalCallback
        from aloha.agent.wrapper import ToolWrapper
        security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
        tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        agent.set_tool_wrapper(tool_wrapper)
        
        # 执行需要工具调用且需要 LLM 根据结果进行进一步处理的请求
        response = await agent.process("请列出当前目录的文件，并统计有多少个文件")
        
        print(f"\n=== Response ===\n{response}")
        print(f"\n=== Thought Logs ===")
        for log in agent.get_thought_logs():
            # 移除 emoji 以避免 Windows 编码问题
            clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
            print(clean_log)
        
        # 验证完整的 ReAct 循环被执行
        assert response


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])