"""Aloha 命令行入口

提供交互式 chat 命令。
"""

import asyncio
import os
import sys
from pathlib import Path

import click

from aloha import ReactAgent, OpenAIProvider
from aloha.bus import MessageBus
from aloha.config import get_config
from aloha.lib import logger


def get_provider() -> OpenAIProvider:
    """创建 LLM Provider，从配置和 .env 读取"""
    config = get_config()

    # 优先使用环境变量，其次使用配置文件
    api_key = os.getenv("OPENAI_API_KEY") or config.providers.openai.api_key if config.providers.openai else ""
    if not api_key:
        logger.LOG_WARNING("OPENAI_API_KEY not set, using placeholder")

    base_url = os.getenv("OPENAI_BASE_URL") or config.providers.openai.base_url if config.providers.openai else None
    model = os.getenv("MODEL") or config.agents.defaults.model

    logger.LOG_DEBUG(f"Using api_key: {'***' + api_key[-4:] if len(api_key) > 4 else api_key}")
    logger.LOG_DEBUG(f"Using base_url: {base_url}")
    logger.LOG_DEBUG(f"Using model: {model}")

    return OpenAIProvider(
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
    agent = ReactAgent(
        bus=bus,
        provider=provider,
        workspace=Path("~/.aloha/workspace").expanduser(),
        model=model or provider.default_model,
        system_prompt=system,  # 如果为 None，将自动从 prompt 文件加载
        prompts_dir=prompts_dir,
    )

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
    agent = ReactAgent(
        bus=bus,
        provider=provider,
        workspace=Path("~/.aloha/workspace").expanduser(),
        model=model or provider.default_model,
        prompts_dir=prompts_dir,
    )

    async def run_once():
        response = await agent.process(message)
        print(f"\nAloha: {response}")

    asyncio.run(run_once())


if __name__ == "__main__":
    cli()
