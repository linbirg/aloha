"""
Aloha Web API Service
FastAPI backend for Aloha Web UI
"""

import asyncio
import os
import traceback
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aloha.lib import logger
from aloha.providers import MiniMaxProvider
from aloha.agent.loop import ReActLoop
from aloha.agent.tools import ToolRegistry
from aloha.agent.wrapper import ToolWrapper
from aloha.security import SecurityConfig
from aloha.bus import MessageBus
from aloha.config import get_config, set_config, AlohaConfig, ProviderConfig
from aloha.tools import FileTool, ShellTool, WebTool


def _init_config_from_aloha_dir() -> AlohaConfig:
    """从 .aloha 目录加载配置和 .env 文件"""
    aloha_dir = Path.home() / ".aloha"

    # 加载 .env 文件
    env_path = aloha_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        logger.LOG_INFO(f"Loaded .env from: {env_path}")
    else:
        # 尝试从项目目录加载
        project_env = Path(__file__).parent.parent.parent / ".env"
        if project_env.exists():
            load_dotenv(project_env)
            logger.LOG_INFO(f"Loaded .env from: {project_env}")

    # 加载配置文件
    config_path = aloha_dir / "config.toml"
    if not config_path.exists():
        config_path = aloha_dir / "config.json"

    if config_path.exists():
        try:
            config = AlohaConfig.from_file(config_path)
            logger.LOG_INFO(f"Loaded config from: {config_path}")
            return config
        except Exception as e:
            logger.LOG_WARNING(f"Failed to load {config_path}: {e}")

    # 返回默认配置
    logger.LOG_INFO("Using default config")
    return AlohaConfig()


# Global state
connected = False
current_model = "MiniMax-M2.7"
security_enabled = True


class ChatRequest(BaseModel):
    message: str
    stream: bool = True


class ToolApprovalRequest(BaseModel):
    tool_call_id: str
    approved: bool


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global connected
    connected = True
    logger.LOG_INFO("Aloha Web API Server started")
    yield
    connected = False
    logger.LOG_INFO("Aloha Web API Server stopped")


app = FastAPI(
    title="Aloha Web API",
    description="Backend API for Aloha Web UI",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_provider_config(config: AlohaConfig):
    """根据配置选择合适的 provider"""
    provider_name = config.agents.defaults.provider
    model = config.agents.defaults.model

    if provider_name == "minimax" and config.providers.minimax:
        return config.providers.minimax, "minimax"
    elif provider_name == "openai" and config.providers.openai:
        return config.providers.openai, "openai"
    elif provider_name == "deepseek" and config.providers.deepseek:
        return config.providers.deepseek, "deepseek"
    elif provider_name == "anthropic" and config.providers.anthropic:
        return config.providers.anthropic, "anthropic"
    elif provider_name == "openrouter" and config.providers.openrouter:
        return config.providers.openrouter, "openrouter"
    else:
        # fallback: 根据 model 名称推断 provider
        if "minimax" in model.lower() and config.providers.minimax:
            return config.providers.minimax, "minimax"
        elif config.providers.openai:
            return config.providers.openai, "openai"
        elif config.providers.minimax:
            return config.providers.minimax, "minimax"
        else:
            logger.LOG_WARNING("No valid provider found, using defaults")
            return ProviderConfig(), "unknown"


def get_provider():
    """创建 LLM Provider，从配置和 .env 读取"""
    config = get_config()

    provider_config, provider_name = _get_provider_config(config)

    api_key = provider_config.api_key
    base_url = provider_config.base_url
    model = config.agents.defaults.model

    logger.LOG_DEBUG(f"Using provider: {provider_name}")
    logger.LOG_DEBUG(
        f"Using api_key: {'***' + api_key[-4:] if len(api_key) > 4 else api_key}"
    )
    logger.LOG_DEBUG(f"Using base_url: {base_url}")
    logger.LOG_DEBUG(f"Using model: {model}")

    if provider_name == "minimax":
        from aloha.providers import MiniMaxProvider

        return MiniMaxProvider(
            api_key=api_key or "sk-placeholder",
            base_url=base_url,
            default_model=model,
        )
    else:
        from aloha.providers import OpenAIProvider

        return OpenAIProvider(
            api_key=api_key or "sk-placeholder",
            base_url=base_url,
            default_model=model,
        )


def get_agent():
    """Get or create ReAct agent."""
    logger.LOG_DEBUG("Creating ReAct agent...")

    # 获取 provider
    provider = get_provider()

    # Create bus
    bus = MessageBus()

    # Create tool registry
    registry = ToolRegistry()

    # 从配置读取 workspace
    from pathlib import Path

    workspace = Path("~/.aloha/workspace").expanduser()

    # 添加系统工具（与 __main__.py 一致）
    registry.register(
        FileTool(
            allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]
        )
    )
    registry.register(
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
    registry.register(WebTool())

    logger.LOG_DEBUG(f"Registered tools: {registry.list_tools()}")

    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=None,
    )

    # Create tool wrapper with security
    wrapper = ToolWrapper(
        registry=registry, config=security_config, enable_security=security_enabled
    )

    # Create agent
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace=workspace,
        model=provider.default_model,
        enable_security=security_enabled,
    )

    # 注册工具到 agent（同时支持直接调用和通过 wrapper 调用）
    for name in registry.list_tools():
        tool = registry.get(name)
        if tool:
            agent.add_tool(tool)

    # 设置 tool wrapper（用于安全审批）
    agent.set_tool_wrapper(wrapper)

    logger.LOG_DEBUG("ReAct agent created successfully")
    logger.LOG_DEBUG(f"Agent tools: {agent.list_tools()}")

    return agent


@app.get("/api/status")
async def get_status():
    """Get current system status."""
    return {
        "connected": connected,
        "model": current_model,
        "security_enabled": security_enabled,
    }


@app.get("/api/history")
async def get_history():
    """Get chat history."""
    return {"messages": []}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint.
    For now, returns a simple response. Streaming will be implemented later.
    """
    logger.LOG_INFO(f"=== Chat Request ===")
    logger.LOG_INFO(
        f"Message: {request.message[:100]}{'...' if len(request.message) > 100 else ''}"
    )

    try:
        agent = get_agent()
        logger.LOG_DEBUG("Agent obtained, processing message...")

        response = await agent.process(request.message)
        logger.LOG_INFO(f"=== Chat Response ===")
        logger.LOG_INFO(
            f"Response (first 200 chars): {response[:200]}{'...' if len(response) > 200 else ''}"
        )

        # 获取思考日志
        thought_logs = agent.get_thought_logs()
        thinking_content = "\n".join(thought_logs) if thought_logs else ""
        logger.LOG_DEBUG(
            f"Thought logs count: {len(thought_logs) if thought_logs else 0}"
        )
        logger.LOG_DEBUG(
            f"Thinking content: {thinking_content[:200] if thinking_content else 'empty'}..."
        )

        # Always include thinking field - if empty, use a placeholder to ensure field appears in JSON
        if not thinking_content:
            thinking_content = "[No thinking logs available]"

        result = {
            "content": response,
            "model": current_model,
            "thinking": thinking_content,
        }
        logger.LOG_DEBUG(f"Returning JSON keys: {list(result.keys())}")
        return result
    except Exception as e:
        logger.LOG_FATAL(f"=== Chat Error ===")
        logger.LOG_FATAL(f"Exception type: {type(e).__name__}")
        logger.LOG_FATAL(f"Exception message: {str(e)}")
        logger.LOG_FATAL(f"Traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}")


@app.post("/api/tool/execute")
async def execute_tool(request: ToolApprovalRequest):
    """Execute or reject a tool call."""
    logger.LOG_INFO(
        f"Tool execution request: tool_call_id={request.tool_call_id}, approved={request.approved}"
    )
    # This would be connected to the approval system
    return {"status": "ok"}


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/tools")
async def get_tools():
    """获取可用的工具列表"""
    agent = get_agent()
    tools = agent.list_tools() if hasattr(agent, "list_tools") else []
    return {"tools": tools}


from fastapi.responses import StreamingResponse
from aloha.web.service.events import get_event_manager
from aloha.agent.approval_manager import ApprovalManager
import time
import json
import uuid

_event_manager = get_event_manager()
_approval_manager: ApprovalManager | None = None
_active_sessions: dict[str, dict] = {}


def get_approval_manager() -> ApprovalManager:
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager(default_timeout=300)
    return _approval_manager


@app.get("/api/events")
async def sse_events(session_id: str):
    async def event_generator():
        queue: asyncio.Queue[str] = asyncio.Queue()
        _event_manager.add_client(session_id, queue)

        last_heartbeat = time.time()

        try:
            _active_sessions[session_id] = {"queue": queue, "connected": True}
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=2)
                    yield message
                    last_heartbeat = time.time()
                except asyncio.TimeoutError:
                    if time.time() - last_heartbeat >= 2:
                        yield f"event: heartbeat\ndata: {json.dumps({'timestamp': int(time.time() * 1000)})}\n\n"
                        last_heartbeat = time.time()
        except asyncio.CancelledError:
            pass
        finally:
            _event_manager.remove_client(session_id, queue)
            _active_sessions.pop(session_id, None)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


class ApprovalSubmitRequest(BaseModel):
    decision: str
    reason: str | None = None


@app.post("/api/approvals/{approval_id}")
async def submit_approval(approval_id: str, body: ApprovalSubmitRequest):
    manager = get_approval_manager()
    event_manager = get_event_manager()

    resolved = manager.resolve(approval_id, body.decision, body.reason)

    session_id = _find_session_for_approval(approval_id)
    if session_id:
        await event_manager.publish(
            session_id,
            "approval_completed",
            {
                "approval_id": approval_id,
                "decision": body.decision,
                "reason": body.reason,
                "approved_at": int(time.time() * 1000),
            },
        )
        if body.decision == "rejected":
            await event_manager.publish(session_id, "error", {"message": "工具被拒绝"})

    return {"success": True, "already_resolved": resolved}


def _find_session_for_approval(approval_id: str) -> str | None:
    for session_id, session_data in _active_sessions.items():
        if session_data.get("connected"):
            return session_id
    return None


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, session_id: str = ""):
    sid = session_id or str(uuid.uuid4())
    manager = get_approval_manager()

    from aloha.agent.loop import StreamingReActLoop
    from pathlib import Path

    provider = get_provider()
    workspace = Path("~/.aloha/workspace").expanduser()

    registry = ToolRegistry()
    registry.register(
        FileTool(
            allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]
        )
    )
    registry.register(
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
    registry.register(WebTool())

    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=None,
    )
    wrapper = ToolWrapper(
        registry=registry, config=security_config, enable_security=security_enabled
    )
    wrapper.approver.set_approval_manager(manager)

    bus = MessageBus()
    loop = StreamingReActLoop(
        event_manager=_event_manager,
        approval_manager=manager,
        session_id=sid,
        bus=bus,
        provider=provider,
        workspace=workspace,
        model=provider.default_model,
        enable_security=security_enabled,
    )
    for name in registry.list_tools():
        tool = registry.get(name)
        if tool:
            loop.add_tool(tool)
    loop.set_tool_wrapper(wrapper)

    result = await loop.process_streaming(request.message)
    return {
        "session_id": sid,
        "content": result["content"],
        "approved": result["approved"],
    }


if __name__ == "__main__":
    import uvicorn

    logger.LOG_INFO("Starting Aloha Web API Server on http://0.0.0.0:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")
