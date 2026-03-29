"""测试 MiniMax Provider 的 ID 规范化"""

import os
import asyncio

# 设置环境变量
os.environ["MINI_MAX_API"] = "sk-cp-_Qe8NJYog4n9mVCAxjfA6x3LHZ1Ot8hKAiEt732QKxkWga6T-NTRGqNUG9m4xdXqJ1A97rJbSBP8vv3_Df8qZPdO9Z40d3LbALY1U_cIDS7w2kCgE6UtZ_k"
os.environ["OPENAI_BASE_URL"] = "https://api.minimaxi.com/v1"
os.environ["MODEL"] = "MiniMax-M2.7"

from aloha import ReActLoop, MiniMaxProvider
from aloha.bus import MessageBus
from aloha.tools import ShellTool
from aloha.security import SecurityConfig, MockApprovalCallback
from aloha.agent.wrapper import ToolWrapper


async def main():
    print("Testing MiniMaxProvider with ID normalization...")
    
    provider = MiniMaxProvider(
        api_key=os.environ["MINI_MAX_API"],
        base_url=os.environ["OPENAI_BASE_URL"],
        default_model=os.environ["MODEL"],
    )
    
    # 测试 ID 规范化
    print("\n=== Testing ID Normalization ===")
    original_id = "call_function_r9rtgh2k7xne_1"
    normalized = provider._get_normalized_id(original_id)
    print(f"Original: {original_id}")
    print(f"Normalized: {normalized}")
    
    # 再次调用应该返回相同的规范化 ID
    normalized2 = provider._get_normalized_id(original_id)
    print(f"Normalized again: {normalized2}")
    print(f"Consistent: {normalized == normalized2}")
    
    # 测试完整循环
    print("\n=== Testing Full ReAct Loop ===")
    bus = MessageBus()
    
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace=os.path.expanduser("~"),
        model=provider.default_model,
        enable_security=True,
        max_iterations=3,
    )
    
    agent.add_tool(ShellTool(allowed_commands=["echo", "pwd", "ls"]))
    
    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=MockApprovalCallback(),
    )
    tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
    agent.set_tool_wrapper(tool_wrapper)
    
    response = await agent.process("请执行命令 echo hello")
    
    print(f"\n=== Response ===\n{response}")
    print(f"\n=== Thought Logs ===")
    for log in agent.get_thought_logs():
        clean_log = log.replace("🤖", "[AI]").replace("💬", "[MSG]").replace("🛠️", "[TOOL]").replace("📝", "[ARGS]").replace("✅", "[OK]").replace("❌", "[ERR]")
        print(clean_log)


if __name__ == "__main__":
    asyncio.run(main())