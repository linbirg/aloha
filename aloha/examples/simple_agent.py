"""简单的 Aloha Agent 使用示例

演示如何创建和使用基本的 agent。
"""

import asyncio
import os
from pathlib import Path

from aloha import ReactAgent, OpenAIProvider
from aloha.bus import MessageBus
from aloha.tools import BaseTool, ToolRegistry
from aloha.tools.base import ToolResult


class CalculatorTool(BaseTool):
    """计算器工具示例"""

    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行简单的数学计算。支持加法、减法、乘法和除法。",
        )

    def _get_parameters_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "要计算的数学表达式，如 '2 + 2' 或 '10 * 5'",
                }
            },
            "required": ["expression"],
        }

    async def execute(self, expression: str) -> ToolResult:
        """执行计算"""
        try:
            # 安全的数学表达式求值
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return ToolResult(
                    success=False,
                    content="",
                    error="表达式包含不允许的字符",
                )

            result = eval(expression)  # 简化实现，生产环境应使用安全的解析器
            return ToolResult(success=True, content=f"结果是: {result}")
        except Exception as e:
            return ToolResult(success=False, content="", error=str(e))


async def main():
    """主函数"""
    # 创建消息总线
    bus = MessageBus()

    # 创建 LLM Provider（使用 OpenRouter 作为示例）
    provider = OpenAIProvider(
        api_key=os.getenv("OPENAI_API_KEY", "sk-your-key-here"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        default_model=os.getenv("MODEL", "gpt-4o-mini"),
    )

    # 创建 Agent
    agent = ReactAgent(
        bus=bus,
        provider=provider,
        workspace=Path("~/.aloha/workspace").expanduser(),
        model=os.getenv("MODEL", "gpt-4o-mini"),
        system_prompt="你是一个有帮助的AI助手。",
    )

    # 注册工具
    agent.add_tool(CalculatorTool())

    # 直接处理用户输入
    user_input = "计算 25 * 4 + 10 的结果"
    print(f"\n用户: {user_input}")

    response = await agent.process(user_input)
    print(f"助手: {response}")


if __name__ == "__main__":
    asyncio.run(main())
