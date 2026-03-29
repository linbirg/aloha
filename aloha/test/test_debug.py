#!/usr/bin/env python
"""Debug script for ReActLoop"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "aloha"))

from aloha import ReActLoop, OpenAIProvider
from aloha.bus import MessageBus
from aloha.config import get_config
from aloha.tools import FileTool, ShellTool, WebTool
from aloha.security import SecurityConfig, MockApprovalCallback
from aloha.agent.wrapper import ToolWrapper


async def main():
    config = get_config()
    print(f"Config loaded: {config.providers.openai.default_model}")
    
    provider = OpenAIProvider(
        api_key=config.providers.openai.api_key,
        base_url=config.providers.openai.base_url,
        default_model=config.providers.openai.default_model,
    )
    print(f"Provider created with model: {provider.default_model}")
    
    workspace = Path("~/.aloha/workspace").expanduser()
    agent = ReActLoop(
        bus=MessageBus(),
        provider=provider,
        workspace=workspace,
        model=provider.default_model,
    )
    print(f"Agent created")
    
    # Add tools
    agent.add_tool(ShellTool(allowed_commands=['ls', 'dir', 'cat', 'echo', 'grep', 'find', 'git', 'pwd', 'cd', 'mkdir', 'cp', 'mv', 'head', 'tail', 'wc', 'python', 'pip', 'uv']))
    print(f"ShellTool registered. Tools: {agent.tools.list_tools()}")
    
    # Add wrapper
    security_config = SecurityConfig(auto_approve_low_risk=True, approval_callback=MockApprovalCallback())
    tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
    agent.set_tool_wrapper(tool_wrapper)
    print(f"ToolWrapper set")
    
    # Get tools schema
    schema = agent.get_tools_schema()
    print(f"Tools schema: {schema}")
    
    # Process request
    print("\n=== Processing request ===")
    response = await agent.process("列出当前目录的文件")
    print(f"\n=== Response ===")
    print(response)
    
    print("\n=== Thought logs ===")
    for log in agent.get_thought_logs():
        print(log)


if __name__ == "__main__":
    asyncio.run(main())
