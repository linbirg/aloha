"""测试 MiniMax Provider 列出目录文件 - 使用配置文件"""

import asyncio
from aloha.config import get_config
from aloha.providers import MiniMaxProvider
from aloha import ReActLoop
from aloha.bus import MessageBus
from aloha.tools import ShellTool
from aloha.security import SecurityConfig, MockApprovalCallback
from aloha.agent.wrapper import ToolWrapper


async def main():
    print("Testing with config...")
    
    # 加载配置
    config = get_config()
    provider_config = config.providers.openai
    
    print(f"Model: {provider_config.default_model}")
    print(f"Base URL: {provider_config.base_url}")
    
    # 创建 Provider
    provider = MiniMaxProvider(
        api_key=provider_config.api_key,
        base_url=provider_config.base_url,
        default_model=provider_config.default_model,
    )
    
    bus = MessageBus()
    
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace="d:/work/linbirg/aloha-agent",  # 使用实际工作目录
        model=provider.default_model,
        enable_security=True,
        max_iterations=3,
    )
    
    # 允许 ls, dir 命令列出文件
    agent.add_tool(ShellTool(allowed_commands=["ls", "dir", "echo", "pwd"]))
    
    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=MockApprovalCallback(),
    )
    tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
    agent.set_tool_wrapper(tool_wrapper)
    
    # 测试列出当前目录文件
    response = await agent.process("列出当前目录下的文件")
    
    print(f"\n=== Response ===\n{response}")
    print(f"\n=== Thought Logs ===")
    for log in agent.get_thought_logs():
        clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
        print(clean_log)


if __name__ == "__main__":
    asyncio.run(main())