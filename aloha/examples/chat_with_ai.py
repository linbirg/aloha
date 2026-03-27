"""Gradio Chat UI 示例

使用 Gradio 构建简单的 AI 对话界面。
支持安全控制，需要用户许可时弹出确认对话框。
"""

import os
import asyncio
from pathlib import Path

import gradio as gr

from aloha import ReActLoop
from aloha.agent import ToolWrapper
from aloha.providers import OpenAIProvider
from aloha.bus import MessageBus
from aloha.prompts import PromptLoader
from aloha.config import get_config
from aloha.lib import logger
from aloha.tools import FileTool, ShellTool, WebTool
from aloha.security import SecurityConfig, MockApprovalCallback
from aloha.security.policy import Permission


class GradioApprovalCallback:
    """Gradio 审批回调 - 通过 GUI 获取用户确认"""

    def __init__(self, gradio_queue: asyncio.Queue):
        self.gradio_queue = gradio_queue
        self._response_event = asyncio.Event()
        self._response = None

    async def request_approval(self, permission: Permission) -> bool:
        """请求用户批准"""
        # 发送审批请求到 Gradio 界面
        await self.gradio_queue.put({
            "type": "approval_request",
            "tool": permission.tool,
            "action": permission.action,
            "resource": permission.resource,
            "risk_level": permission.risk_level.value,
        })
        
        logger.LOG_DEBUG(f"[ApprovalCallback] Approval request sent: {permission.tool}, waiting for user response...")

        # 等待用户响应 - 使用轮询方式检测响应
        start_time = asyncio.get_event_loop().time()
        while True:
            # 检查是否已有响应
            if self._response is not None:
                result = self._response
                self._response = None
                self._response_event.clear()
                logger.LOG_DEBUG(f"[ApprovalCallback] Response received: {result}")
                return result is True
            
            # 检查是否超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= 60:
                logger.LOG_WARNING("Approval request timed out")
                return False
            
            logger.LOG_DEBUG(f"Approval request timed {elapsed}...")
            # 短暂等待后再次检查
            await asyncio.sleep(0.5)

    async def request_approval_with_timeout(self, permission: Permission, timeout: float) -> bool:
        """请求用户批准，带超时时间"""
        # 发送审批请求到 Gradio 界面
        await self.gradio_queue.put({
            "type": "approval_request",
            "tool": permission.tool,
            "action": permission.action,
            "resource": permission.resource,
            "risk_level": permission.risk_level.value,
        })
        
        logger.LOG_DEBUG(f"[ApprovalCallback] Approval request sent with timeout={timeout}s")

        # 等待用户响应 - 使用轮询方式检测响应
        start_time = asyncio.get_event_loop().time()
        while True:
            # 检查是否已有响应
            if self._response is not None:
                result = self._response
                self._response = None
                self._response_event.clear()
                logger.LOG_DEBUG(f"[ApprovalCallback] Response received: {result}")
                return result is True
            
            # 检查是否超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.LOG_WARNING(f"Approval request timed out after {timeout}s")
                return False
            
            logger.LOG_DEBUG(f"Approval request timed {elapsed}...")
            # 短暂等待后再次检查
            await asyncio.sleep(0.5)

    async def notify(self, message: str) -> None:
        """通知用户"""
        await self.gradio_queue.put({
            "type": "notification",
            "message": message,
        })

    def set_response(self, approved: bool):
        """设置用户响应（由 Gradio 回调调用）"""
        self._response = approved
        self._response_event.set()


# 全局变量
_approval_queue: asyncio.Queue | None = None
_approval_callback: GradioApprovalCallback | None = None


def create_agent(enable_security: bool = True, approval_callback: GradioApprovalCallback | None = None):
    """创建 Agent 实例

    Args:
        enable_security: 是否启用安全控制
        approval_callback: 审批回调实例（优先使用）
    """
    # 优先从 config.toml 读取配置，环境变量会覆盖配置文件
    config = get_config()

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

    if not api_key:
        logger.LOG_WARNING("API key not set, using placeholder")

    # 创建 provider
    logger.LOG_INFO("Creating OpenAIProvider...")
    provider = OpenAIProvider(
        api_key=api_key or "sk-placeholder",
        base_url=base_url,
        default_model=model,
    )

    # 创建消息总线
    logger.LOG_DEBUG("Creating MessageBus...")
    bus = MessageBus()

    # 加载 prompts
    prompt_loader = PromptLoader([workspace / "prompts"])

    # 创建 agent，启用安全控制
    logger.LOG_INFO(f"Creating ReActLoop with model={model}, security={enable_security}...")

    if enable_security:
        # 创建安全配置
        security_config = SecurityConfig(
            auto_approve_low_risk=False,  # 所有操作都需要确认（或使用回调）
        )

        # 设置审批回调
        if approval_callback:
            security_config.approval_callback = approval_callback

        # 创建 agent（启用安全）
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=workspace,
            model=model,
            prompts_dir=str(workspace / "prompts"),
            enable_security=True,
        )

        # 创建 ToolWrapper 并注册系统工具
        wrapper = ToolWrapper(agent.tools, security_config, enable_security=True)
        wrapper.register(FileTool(allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]))
        wrapper.register(ShellTool())
        wrapper.register(WebTool())

        # 设置到 agent
        agent.set_tool_wrapper(wrapper)
    else:
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            workspace=workspace,
            model=model,
            prompts_dir=str(workspace / "prompts"),
            enable_security=False,
        )
        # 添加系统工具
        agent.add_tool(FileTool(allowed_read_dirs=[workspace], allowed_write_dirs=[workspace / "output"]))
        agent.add_tool(ShellTool())
        agent.add_tool(WebTool())

    logger.LOG_INFO("Agent created successfully")

    return agent


# 全局 Agent 实例
_agent: ReActLoop | None = None


def get_agent():
    """获取或创建 Agent 实例（单例）
    
    首次调用创建 Agent，之后复用。
    队列和回调在首次创建时初始化，保持与 Agent 的引用一致。
    """
    global _agent, _approval_queue, _approval_callback
    
    # 首次创建
    if _agent is None:
        _approval_queue = asyncio.Queue()
        _approval_callback = GradioApprovalCallback(_approval_queue)
        _agent = create_agent(approval_callback=_approval_callback)
        logger.LOG_INFO("Agent created for the first time")
    
    return _agent


def format_thinking_with_details(thought_logs: list[str], ai_thinking: str = "") -> str:
    """使用 <details> 标签格式化思考内容"""
    parts = []

    if thought_logs:
        tool_logs = "\n".join(f"- {log}" for log in thought_logs)
        parts.append(f"**🛠️ 工具调用:**\n{tool_logs}")

    if ai_thinking:
        parts.append(f"**🤔 AI 思考:**\n{ai_thinking}")

    if not parts:
        return ""

    thinking_text = "\n\n".join(parts)
    return f"<details>\n<summary>🧠 点击查看思考过程</summary>\n\n{thinking_text}\n\n</details>"


def parse_thinking_content(response: str) -> tuple[str, str]:
    """解析 AI 回复中的思考内容和正式反馈"""
    import re

    patterns = [
        r'<thinking>(.*?)</thinking>',
        r'<thought>(.*?)</thought>',
        r'<think>(.*?)',
    ]

    thinking_content = ""
    final_content = response

    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            thinking_content = match.group(1).strip()
            final_content = re.sub(pattern, '', response, flags=re.DOTALL | re.IGNORECASE).strip()
            break

    return thinking_content, final_content


# 用于存储待审批请求
pending_approvals: dict = {}
approval_counter = 0
_current_user_message: str = ""  # 保存当前正在处理的用户消息


async def process_approval_queue():
    """处理审批队列"""
    global _approval_queue, pending_approvals, approval_counter

    if _approval_queue is None:
        return

    while not _approval_queue.empty():
        try:
            logger.LOG_WARNING(f"not _approval_queue not empty...")
            msg = await asyncio.wait_for(_approval_queue.get(), timeout=0.1)

            if msg.get("type") == "approval_request":
                approval_id = f"approval_{approval_counter}"
                approval_counter += 1

                pending_approvals[approval_id] = {
                    "tool": msg["tool"],
                    "action": msg["action"],
                    "resource": msg["resource"],
                    "risk_level": msg["risk_level"],
                }

                # 更新 UI（通过返回特殊消息）
                logger.LOG_INFO(f"Approval requested: {msg['tool']} {msg['action']} {msg['resource']}")

        except asyncio.TimeoutError as toe:
            logger.LOG_WARNING(f"Error processing approval queue: {toe}")
            break
        except Exception as e:
            logger.LOG_WARNING(f"Error processing approval queue: {e}")


async def chat_fn(message: str, history: list, approval_list_state):
    """ChatInterface 使用的聊天函数

    支持安全控制，需要许可时显示确认按钮。
    返回格式: list[dict] - 符合 Gradio 5.x chatbot 格式
    """
    import time

    logger.LOG_DEBUG(f"ChatInterface called with message: {message[:50]}...")

    global _current_user_message
    
    # 处理审批队列
    await process_approval_queue()

    # 检查是否有待审批的请求
    if pending_approvals:
        # 保存当前消息，以便审批后重新处理
        _current_user_message = message
        
        # 显示待审批的请求，并返回当前审批列表状态
        approval_info = ""
        for approval_id, info in pending_approvals.items():
            approval_info += f"**{approval_id}**:\n- 工具: {info['tool']}\n- 操作: {info['action']}\n- 资源: {info['resource']}\n- 风险: {info['risk_level']}\n\n"
        
        return [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"⚠️ **需要权限确认**\n\n{approval_info}请在右侧点击确认或拒绝按钮。"},
        ], pending_approvals

    agent = get_agent()

    try:
        # 获取实际回复
        response = await agent.process(message)
        logger.LOG_INFO(f"Response received, length: {len(response)}")

        # 获取思考日志
        thought_logs = agent.get_thought_logs()

        # 解析 AI 回复中的思考标签
        ai_thinking, final_response = parse_thinking_content(response)

        # 构建思考内容
        thinking_details = format_thinking_with_details(thought_logs, ai_thinking)

        # 拼接最终回复
        if thinking_details:
            full_content = f"{thinking_details}\n\n---\n\n{final_response}"
        else:
            full_content = final_response

        # 返回符合 Gradio 5.x 格式的消息列表
        # 确保返回的是有效的消息格式
        if not full_content:
            full_content = "无回复"
        
        return [
            {"role": "user", "content": message},
            {"role": "assistant", "content": full_content},
        ], pending_approvals

    except Exception as e:
        logger.LOG_WARNING(f"Chat error: {str(e)}")
        import traceback
        logger.LOG_WARNING(f"Traceback: {traceback.format_exc()}")
        return [
            {"role": "user", "content": message},
            {"role": "assistant", "content": f"Error: {str(e)}"},
        ], pending_approvals


def handle_approval(approval_id: str, approved: bool):
    """处理用户审批

    Args:
        approval_id: 审批请求 ID
        approved: 是否批准
    
    Returns:
        tuple: (状态消息, 审批列表, 触发重处理标志)
    """
    global pending_approvals, _approval_callback, _current_user_message
    
    logger.LOG_DEBUG(f"[handle_approval] called with approval_id={approval_id}, approved={approved}")

    if approval_id in pending_approvals:
        del pending_approvals[approval_id]
        logger.LOG_DEBUG(f"[handle_approval] Removed {approval_id} from pending_approvals")

    if _approval_callback:
        logger.LOG_DEBUG(f"[handle_approval] Setting approval response: {approved}")
        _approval_callback.set_response(approved)
        logger.LOG_INFO(f"User response: {'approved' if approved else 'rejected'} {approval_id}")
    else:
        logger.LOG_WARNING("[handle_approval] _approval_callback is None!")

    # 返回触发重处理：需要重新调用 chat_fn 来继续处理
    should_rerun = len(_current_user_message) > 0 and approved
    return "已处理", pending_approvals, should_rerun


def main():
    """启动 Gradio 界面"""
    logger.LOG_INFO("=" * 50)
    logger.LOG_INFO("Starting Gradio Chat UI with Security...")
    logger.LOG_INFO("=" * 50)

    # 预热 Agent
    logger.LOG_INFO("Warming up agent...")
    get_agent()
    logger.LOG_INFO("Agent ready")

    # 使用 ChatInterface 组件
    with gr.Blocks(title="Aloha AI Assistant - 安全模式") as demo:
        gr.Markdown("## 🤖 Aloha AI Assistant\n\n**安全模式已启用** - 需要权限时将显示确认对话框")

        # 审批状态显示 - 使用 State 组件来跟踪待审批列表
        approval_list_state = gr.State(value={})

        with gr.Row():
            with gr.Column(scale=4):
                # 主聊天界面
                chatbot = gr.Chatbot(
                    min_height=400,
                    max_height=800,
                    render_markdown=True,
                )
                msg_input = gr.Textbox(
                    placeholder="有问题，尽管问...",
                    show_label=False,
                    scale=5,
                )
                submit_btn = gr.Button("发送", variant="primary")

            with gr.Column(scale=1):
                # 审批控制面板
                gr.Markdown("### 🔐 权限审批")
                approval_list = gr.JSON(label="待审批请求", value={})
                status_text = gr.Textbox(label="状态", value="等待中...")

                def update_approval_list():
                    global pending_approvals
                    return pending_approvals

                # 按钮点击时更新审批列表和处理审批
                def on_approve():
                    global pending_approvals, _current_user_message
                    logger.LOG_DEBUG("[on_approve] button clicked")
                    
                    if not pending_approvals:
                        logger.LOG_DEBUG("[on_approve] no pending approvals")
                        return "没有待审批的请求", None, ""
                    
                    first_id = list(pending_approvals.keys())[0]
                    logger.LOG_DEBUG(f"[on_approve] found pending approval {first_id}")
                    
                    # 先处理审批
                    handle_approval(first_id, True)
                    
                    # 检查是否有待处理的消息
                    msg = _current_user_message
                    _current_user_message = ""  # 清空
                    
                    if not msg:
                        return "已批准", None, ""
                    
                    # 直接重新处理消息
                    try:
                        agent = get_agent()
                        import asyncio
                        response = asyncio.run(agent.process(msg))
                        thought_logs = agent.get_thought_logs()
                        ai_thinking, final_response = parse_thinking_content(response)
                        thinking_details = format_thinking_with_details(thought_logs, ai_thinking)
                        full_content = f"{thinking_details}\n\n---\n\n{final_response}" if thinking_details else final_response
                        
                        return "已批准", [
                            {"role": "user", "content": msg},
                            {"role": "assistant", "content": full_content},
                        ], ""
                    except Exception as e:
                        logger.LOG_WARNING(f"Error re-processing after approval: {e}")
                        import traceback
                        logger.LOG_WARNING(f"Traceback: {traceback.format_exc()}")
                        return "已批准（处理失败）", [
                            {"role": "user", "content": msg},
                            {"role": "assistant", "content": f"Error: {str(e)}"},
                        ], ""

                def on_reject():
                    global pending_approvals, _current_user_message
                    logger.LOG_DEBUG("[on_reject] button clicked")
                    
                    if pending_approvals:
                        first_id = list(pending_approvals.keys())[0]
                        handle_approval(first_id, False)
                    
                    # 清空保存的消息
                    _current_user_message = ""
                    
                    return f"{'已拒绝' if pending_approvals else '没有待审批的请求'}", None, ""

                # 刷新按钮
                refresh_btn = gr.Button("🔄 刷新列表", size="sm")
                refresh_btn.click(update_approval_list, outputs=[approval_list])

                with gr.Row():
                    approve_btn = gr.Button("✅ 批准", variant="primary")
                    reject_btn = gr.Button("❌ 拒绝", variant="stop")

                # 批准按钮：返回新的聊天消息 + 审批列表
                approve_btn.click(
                    on_approve,
                    outputs=[status_text, chatbot, approval_list],
                )
                # 拒绝按钮：只更新状态
                reject_btn.click(
                    on_reject,
                    outputs=[status_text, chatbot, approval_list],
                )

        # 定时刷新审批列表（每2秒）
        demo.load(lambda: pending_approvals, outputs=[approval_list])

        # 示例问题
        gr.Examples(
            examples=[
                ["你好，请介绍一下你自己"],
                ["列出当前目录的文件"],
                ["查看 README.md 的内容"],
            ],
            inputs=msg_input,
        )

        # 绑定提交按钮 - 使用 async 函数
        submit_btn.click(
            chat_fn,
            inputs=[msg_input, chatbot, approval_list_state],
            outputs=[chatbot, approval_list],
        )
        msg_input.submit(
            chat_fn,
            inputs=[msg_input, chatbot, approval_list_state],
            outputs=[chatbot, approval_list],
        )

    # 启动界面
    demo.launch(
        server_name="0.0.0.0",
        server_port=7862,
        share=False,
        theme="soft",
    )


if __name__ == "__main__":
    main()
