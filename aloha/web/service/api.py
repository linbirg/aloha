"""
Aloha Web API Service
FastAPI backend for Aloha Web UI
"""
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from aloha.lib import logger
from aloha.providers import MiniMaxProvider
from aloha.agent.loop import ReActLoop
from aloha.agent.tools import ToolRegistry
from aloha.agent.wrapper import ToolWrapper
from aloha.security import SecurityConfig, MockApprovalCallback
from aloha.bus import MessageBus
from aloha.config import get_config
from aloha.tools import FileTool, ShellTool, WebTool

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
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


def get_provider() -> MiniMaxProvider:
    """创建 LLM Provider，从配置和 .env 读取"""
    config = get_config()
    
    # 优先使用环境变量，其次使用配置文件
    api_key = config.providers.openai.api_key if config.providers.openai else ""
    if not api_key:
        logger.LOG_WARNING("API key not configured, using placeholder")
    
    base_url = config.providers.openai.base_url if config.providers.openai else None
    model = config.agents.defaults.model
    
    logger.LOG_DEBUG(f"Using api_key: {'***' + api_key[-4:] if len(api_key) > 4 else api_key}")
    logger.LOG_DEBUG(f"Using base_url: {base_url}")
    logger.LOG_DEBUG(f"Using model: {model}")
    
    return MiniMaxProvider(
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
    registry.register(FileTool(allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]))
    registry.register(ShellTool(
        allowed_commands=["ls", "dir", "cat", "echo", "grep", "find", "git", "pwd", "cd", "mkdir", "cp", "mv", "head", "tail", "wc", "python", "pip", "uv"]
    ))
    registry.register(WebTool())
    
    logger.LOG_DEBUG(f"Registered tools: {registry.list_tools()}")
    
    # 启用安全审批
    security_config = SecurityConfig(
        auto_approve_low_risk=True,
        approval_callback=MockApprovalCallback(),
    )
    
    # Create tool wrapper with security
    wrapper = ToolWrapper(
        registry=registry,
        config=security_config,
        enable_security=security_enabled
    )
    
    # Create agent
    agent = ReActLoop(
        bus=bus,
        provider=provider,
        workspace=workspace,
        model=provider.default_model,
        enable_security=security_enabled
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
        "security_enabled": security_enabled
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
    logger.LOG_INFO(f"Message: {request.message[:100]}{'...' if len(request.message) > 100 else ''}")
    
    try:
        agent = get_agent()
        logger.LOG_DEBUG("Agent obtained, processing message...")
        
        response = await agent.process(request.message)
        logger.LOG_INFO(f"=== Chat Response ===")
        logger.LOG_INFO(f"Response (first 200 chars): {response[:200]}{'...' if len(response) > 200 else ''}")
        
        # 获取思考日志
        thought_logs = agent.get_thought_logs()
        thinking_content = "\n".join(thought_logs) if thought_logs else ""
        logger.LOG_DEBUG(f"Thought logs count: {len(thought_logs) if thought_logs else 0}")
        logger.LOG_DEBUG(f"Thinking content: {thinking_content[:200] if thinking_content else 'empty'}...")
        
        # Always include thinking field - if empty, use a placeholder to ensure field appears in JSON
        if not thinking_content:
            thinking_content = "[No thinking logs available]"
        
        result = {
            "content": response,
            "model": current_model,
            "thinking": thinking_content
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
    logger.LOG_INFO(f"Tool execution request: tool_call_id={request.tool_call_id}, approved={request.approved}")
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
    tools = agent.list_tools() if hasattr(agent, 'list_tools') else []
    return {"tools": tools}


if __name__ == "__main__":
    import uvicorn
    logger.LOG_INFO("Starting Aloha Web API Server on http://0.0.0.0:8000")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="debug"
    )