"""Aloha 命令行入口

提供交互式 chat 命令。
"""

import asyncio
import os
import sys
from pathlib import Path

import click

from aloha import ReActLoop
from aloha.providers import MiniMaxProvider
from aloha.bus import MessageBus
from aloha.config import get_config
from aloha.lib import logger
from aloha.tools import FileTool, ShellTool, WebTool
from aloha.security import SecurityConfig, MockApprovalCallback


def get_provider() -> MiniMaxProvider:
    """创建 LLM Provider，从配置和 .env 读取"""
    config = get_config()

    # 优先使用 MINI_MAX_API 环境变量，其次使用配置文件
    api_key = (
        os.getenv("MINI_MAX_API") or config.providers.openai.api_key
        if config.providers.openai
        else ""
    )
    if not api_key:
        logger.LOG_WARNING("MINI_MAX_API not set, using placeholder")

    base_url = (
        os.getenv("MINI_MAX_BASE_URL") or config.providers.openai.base_url
        if config.providers.openai
        else None
    )
    model = os.getenv("MODEL") or config.agents.defaults.model

    logger.LOG_DEBUG(
        f"Using api_key: {'***' + api_key[-4:] if len(api_key) > 4 else api_key}"
    )
    logger.LOG_DEBUG(f"Using base_url: {base_url}")
    logger.LOG_DEBUG(f"Using model: {model}")

    return MiniMaxProvider(
        api_key=api_key or "sk-placeholder",
        base_url=base_url,
        default_model=model,
    )


@click.group()
def cli():
    """Aloha - 轻量级 AI Agent 框架"""
    pass


@cli.command()
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--system", "-s", default=None, help="System prompt")
@click.option("--prompts", "-p", "prompts_dir", default=None, help="Prompts directory")
def chat(model: str | None, system: str | None, prompts_dir: str | None):
    """启动交互式 chat 会话"""
    logger.LOG_INFO("Starting Aloha chat session...")

    # 创建 provider
    provider = get_provider()
    if model:
        provider.default_model = model

    # 创建 agent
    bus = MessageBus()
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace=Path("~/.aloha/workspace").expanduser(),
        model=model or provider.default_model,
        system_prompt=system,  # 如果为 None，将自动从 prompt 文件加载
        prompts_dir=prompts_dir,
    )

    # 添加系统工具
    workspace = Path("~/.aloha/workspace").expanduser()
    agent.add_tool(
        FileTool(
            allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]
        )
    )
    # 添加 ShellTool，允许 Windows 和 Linux 命令
    agent.add_tool(
        ShellTool(
            allowed_commands=[
                "ls",
                "dir",
                "cat",
                "echo",
                "grep",
                "find",
                "git",
                "pwd",
                "cd",
                "mkdir",
                "cp",
                "mv",
                "rm",
                "head",
                "tail",
                "wc",
                "python",
                "pip",
                "uv",
            ]
        )
    )
    agent.add_tool(WebTool())

    # 启用安全审批（开发模式：自动批准所有请求）
    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=MockApprovalCallback(),
    )
    from aloha.agent.wrapper import ToolWrapper

    tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
    agent.set_tool_wrapper(tool_wrapper)

    logger.LOG_INFO(f"Agent ready. Type 'quit' or 'exit' to end session.")
    logger.LOG_INFO(f"Model: {provider.default_model}")

    async def chat_loop():
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    logger.LOG_INFO("Goodbye!")
                    break

                response = await agent.process(user_input)
                print(f"\nAloha: {response}")

            except KeyboardInterrupt:
                logger.LOG_INFO("Goodbye!")
                break
            except Exception as e:
                logger.LOG_WARNING(f"Error: {str(e)}")

    asyncio.run(chat_loop())


@cli.command()
@click.argument("message")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--prompts", "-p", "prompts_dir", default=None, help="Prompts directory")
def say(message: str, model: str | None, prompts_dir: str | None):
    """发送单条消息并退出"""
    logger.LOG_INFO("Sending message to Aloha...")

    provider = get_provider()
    if model:
        provider.default_model = model

    bus = MessageBus()
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace=Path("~/.aloha/workspace").expanduser(),
        model=model or provider.default_model,
        prompts_dir=prompts_dir,
    )

    # 添加系统工具（与 chat 命令一致）
    workspace = Path("~/.aloha/workspace").expanduser()
    agent.add_tool(
        FileTool(
            allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]
        )
    )
    agent.add_tool(
        ShellTool(
            allowed_commands=[
                "ls",
                "dir",
                "cat",
                "echo",
                "grep",
                "find",
                "git",
                "pwd",
                "cd",
                "mkdir",
                "cp",
                "mv",
                "rm",
                "head",
                "tail",
                "wc",
                "python",
                "pip",
                "uv",
            ]
        )
    )
    agent.add_tool(WebTool())

    # 启用安全审批
    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=MockApprovalCallback(),
    )
    from aloha.agent.wrapper import ToolWrapper

    tool_wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
    agent.set_tool_wrapper(tool_wrapper)

    async def run_once():
        response = await agent.process(message)
        print(f"\nAloha: {response}")

    asyncio.run(run_once())


if __name__ == "__main__":
    cli()
