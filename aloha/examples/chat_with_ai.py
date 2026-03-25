"""Gradio Chat UI 示例

使用 Gradio 构建简单的 AI 对话界面。
"""

import os
from pathlib import Path

import gradio as gr
from gradio import ChatMessage

from aloha import AgentLoop
from aloha.providers import OpenAIProvider
from aloha.bus import MessageBus
from aloha.prompts import PromptLoader
from aloha.config import get_config
from aloha.lib import logger


def create_agent():
    """创建 Agent 实例"""
    # 优先从 config.toml 读取配置，环境变量会覆盖配置文件
    config = get_config()
    logger.LOG_DEBUG(f"Config loaded: {config}")

    # 获取 Provider 配置 - 先取默认值，再用 provider_config 覆盖
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "")
    model = os.getenv("MODEL", "gpt-4o-mini")

    if provider_config := config.providers.openai:
        if provider_config.api_key:
            api_key = provider_config.api_key
        if provider_config.base_url:
            base_url = provider_config.base_url
        if provider_config.default_model:
            model = provider_config.default_model

    # 获取 Agent 默认配置
    agent_config = config.agents.defaults
    workspace = Path(os.getenv("WORKSPACE", agent_config.workspace)).expanduser()

    logger.LOG_DEBUG(f"Creating agent with config:")
    logger.LOG_DEBUG(f"  api_key: {api_key[:10] + '...' if len(api_key) > 10 else api_key}")
    logger.LOG_DEBUG(f"  base_url: {base_url}")
    logger.LOG_DEBUG(f"  model: {model}")
    logger.LOG_DEBUG(f"  workspace: {workspace}")

    if not api_key:
        logger.LOG_WARNING("API key not set, using placeholder")

    # 创建 provider
    logger.LOG_INFO("Creating OpenAIProvider...")
    provider = OpenAIProvider(
        api_key=api_key or "sk-placeholder",
        base_url=base_url,
        default_model=model,
    )
    logger.LOG_DEBUG(f"Provider created: {provider}")

    # 创建消息总线
    logger.LOG_DEBUG("Creating MessageBus...")
    bus = MessageBus()

    # 加载 prompts
    logger.LOG_DEBUG(f"Workspace: {workspace}")
    prompt_loader = PromptLoader([workspace / "prompts"])
    logger.LOG_DEBUG(f"PromptLoader created with {len(prompt_loader.list_available())} prompt files")

    # 创建 agent
    logger.LOG_INFO(f"Creating AgentLoop with model={model}...")
    agent = AgentLoop(
        bus=bus,
        provider=provider,
        workspace=workspace,
        model=model,
        prompts_dir=str(workspace / "prompts"),
    )
    logger.LOG_INFO("Agent created successfully")

    return agent


# 全局 Agent 实例
_agent = None


def get_agent():
    """获取或创建 Agent 实例（单例）"""
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


async def chat(message: str, history: list) -> tuple[str, list]:
    """处理聊天消息
    
    返回:
        tuple: (更新 Textbox 的值, 更新 Chatbot 的历史记录)
    """
    logger.LOG_DEBUG(f"Chat called with message: {message[:50]}...")
    logger.LOG_DEBUG(f"History length: {len(history) if history else 0}")

    agent = get_agent()

    try:
        # 处理用户输入
        logger.LOG_INFO(f"Processing message: {message[:30]}...")
        response = await agent.process(message)
        logger.LOG_INFO(f"Response received, length: {len(response)}")
        
        # Gradio 5.x 需要字典格式的消息历史
        new_history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ]
        return "", new_history
    except Exception as e:
        logger.LOG_WARNING(f"Chat error: {str(e)}")
        import traceback
        logger.LOG_WARNING(f"Traceback: {traceback.format_exc()}")
        new_history = (history or []) + [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"Error: {str(e)}"}
        ]
        return "", new_history


def format_history(history: list) -> list:
    """格式化历史记录为 Gradio Chatbot 格式"""
    return history


import time


async def chat_fn(message: str, history: list):
    """ChatInterface 使用的聊天函数（支持流式输出和思考过程展示）
    
    Args:
        message: 用户输入的消息
        history: 对话历史
    
    Yields:
        ChatMessage: 思考消息（折叠面板）和最终回复
    """
    logger.LOG_DEBUG(f"ChatInterface called with message: {message[:50]}...")
    
    agent = get_agent()
    
    try:
        # 显示思考中的消息
        thinking_msg = ChatMessage(
            role="assistant",
            content="",  # 主消息内容为空
            metadata={
                "title": "🧠 思考中...", 
                "status": "pending",
                "log": "正在处理..."
            }
        )
        yield thinking_msg
        
        # 获取实际回复（Agent 会自动记录思考日志）
        response = await agent.process(message)
        logger.LOG_INFO(f"Response received, length: {len(response)}")
        
        # 获取真实的思考日志
        thought_logs = agent.get_thought_logs()
        
        # 如果有思考日志，逐步显示
        if thought_logs:
            for i, log in enumerate(thought_logs):
                thinking_msg.metadata["log"] = log
                yield thinking_msg
                time.sleep(0.2)  # 短暂延迟让用户看到过程
        else:
            thinking_msg.metadata["log"] = "完成思考"
        
        # 标记思考完成
        thinking_msg.metadata["status"] = "done"
        yield thinking_msg
        
        # 返回最终回复（包含思考日志）
        logs_text = "\n".join(f"- {log}" for log in thought_logs)
        yield ChatMessage(
            role="assistant", 
            content=response,
            metadata={"title": "🧠 思考过程", "log": logs_text}
        )
        
    except Exception as e:
        logger.LOG_WARNING(f"Chat error: {str(e)}")
        import traceback
        logger.LOG_WARNING(f"Traceback: {traceback.format_exc()}")
        yield ChatMessage(role="assistant", content=f"Error: {str(e)}")


def main():
    """启动 Gradio 界面"""
    logger.LOG_INFO("=" * 50)
    logger.LOG_INFO("Starting Gradio Chat UI...")
    logger.LOG_INFO("=" * 50)

    # 预热 Agent
    logger.LOG_INFO("Warming up agent...")
    get_agent()
    logger.LOG_INFO("Agent ready")

    # 使用 ChatInterface 组件
    demo = gr.ChatInterface(
        fn=chat_fn,
        title="🤖 Aloha AI Assistant",
        description="基于 Gradio 的轻量级 AI 对话界面 | 按 Enter 发送，Shift+Enter 换行",
        chatbot=gr.Chatbot(height=500, render_markdown=True),
        textbox=gr.Textbox(
            placeholder="有问题，尽管问...",
            show_label=False,
            scale=5,
        ),
        examples=[
            "你好，请介绍一下你自己",
            "Python 是什么？",
            "如何学习编程？",
        ],
    )

    # 启动界面
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        theme="soft",  
    )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) if False else main()
