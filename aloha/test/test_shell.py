"""测试 Shell 工具"""

import asyncio
from aloha.tools import ShellTool


async def test_shell():
    tool = ShellTool()
    
    # 测试 ls 命令
    print("Testing 'ls -la'...")
    result = await tool.execute("ls -la")
    print(f"Success: {result.success}")
    print(f"Content: {result.content}")
    print(f"Error: {result.error}")
    print()
    
    # 测试 pwd 命令
    print("Testing 'pwd'...")
    result = await tool.execute("pwd")
    print(f"Success: {result.success}")
    print(f"Content: {result.content}")
    print(f"Error: {result.error}")
    print()
    
    # 测试 echo 命令
    print("Testing 'echo hello'...")
    result = await tool.execute("echo hello")
    print(f"Success: {result.success}")
    print(f"Content: {result.content}")
    print(f"Error: {result.error}")


if __name__ == "__main__":
    asyncio.run(test_shell())
