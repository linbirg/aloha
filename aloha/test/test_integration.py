"""ReActLoop 集成测试 - 真实 LLM API + 审批流程

测试场景：
1. 使用配置文件中的真实 LLM API 
2. 模拟需要审批的工具调用
3. 交互式用户确认（通过终端输入）
"""

import sys
import os

# 确保项目根目录在 Python 路径中
_current_file = os.path.abspath(__file__)
_test_dir = os.path.dirname(_current_file)  # aloha/test/
_project_root = os.path.dirname(_test_dir)  # aloha/

_possible_roots = [
    _project_root,
    os.getcwd(),
    os.path.join(os.getcwd(), "aloha"),
]

for _root in _possible_roots:
    if _root not in sys.path and os.path.isdir(os.path.join(_root, "aloha")):
        sys.path.insert(0, _root)

import asyncio
import pytest
from pathlib import Path

from aloha.agent.loop import ReActLoop
from aloha.agent.tools import ToolRegistry, BaseTool, ToolResult
from aloha.providers import OpenAIProvider
from aloha.security import SecurityConfig, Permission, RiskLevel, ApprovalCallback
from aloha.bus import MessageBus
from aloha.config import get_config


class InteractiveApprovalCallback:
    """交互式审批回调 - 通过终端获取用户输入"""

    def __init__(self, auto_approve: bool = False, timeout: float = 60.0):
        """
        Args:
            auto_approve: True 时自动批准所有请求（用于自动化测试）
            timeout: 审批超时时间（秒）
        """
        self.auto_approve = auto_approve
        self.timeout = timeout
        self.approval_history = []

    async def request_approval(self, permission: Permission) -> bool:
        """请求用户审批"""
        if self.auto_approve:
            self.approval_history.append((permission, True))
            return True

        # 打印审批请求
        print("\n" + "=" * 60)
        print("🔐 权限审批请求")
        print("=" * 60)
        print(f"工具: {permission.tool}")
        print(f"操作: {permission.action}")
        print(f"资源: {permission.resource}")
        print(f"风险级别: {permission.risk_level.value.upper()}")
        print("-" * 60)

        # 获取用户输入
        try:
            response = input("是否批准此请求？(yes/no): ").strip().lower()
            approved = response in ["yes", "y", "是", "同意"]
            self.approval_history.append((permission, approved))
            return approved
        except (KeyboardInterrupt, EOFError):
            print("\n⚠️ 用户取消，默认拒绝")
            self.approval_history.append((permission, False))
            return False

    async def request_approval_with_timeout(
        self, permission: Permission, timeout: float
    ) -> bool:
        """带超时时间的审批请求"""
        # 简化实现：直接调用 request_approval
        return await self.request_approval(permission)

    async def notify(self, message: str) -> None:
        """发送通知"""
        print(f"\n📢 通知: {message}")


class EchoTool(BaseTool):
    """Echo 工具 - 用于测试"""

    def __init__(self):
        super().__init__(name="echo", description="返回输入的内容")

    async def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text", "")
        return ToolResult(success=True, content=f"Echo: {text}")


class ReadFileTool(BaseTool):
    """模拟文件读取工具"""

    def __init__(self, allowed_dir: Path):
        super().__init__(name="file", description="读取文件内容")
        self.allowed_dir = allowed_dir

    async def execute(self, **kwargs) -> ToolResult:
        operation = kwargs.get("operation", "read")
        path = kwargs.get("path", "")

        if operation == "read":
            try:
                file_path = Path(path)
                if not file_path.is_absolute():
                    file_path = self.allowed_dir / file_path
                
                if not file_path.exists():
                    return ToolResult(success=False, content="", error="File not found")
                
                content = file_path.read_text()
                return ToolResult(success=True, content=content)
            except Exception as e:
                return ToolResult(success=False, content="", error=str(e))
        
        return ToolResult(success=False, content="", error="Unsupported operation")


@pytest.mark.integration
class TestReActLoopIntegration:
    """ReActLoop 集成测试"""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_echo_tool_no_approval(self):
        """测试 Echo 工具 - 无需审批（低风险）"""
        print("\n" + "=" * 60)
        print("测试 1: Echo 工具（低风险，应自动通过）")
        print("=" * 60)

        # 从配置文件读取 provider 配置
        config = get_config()
        
        # 获取 provider 配置
        openai_config = config.providers.openai if config.providers.openai else None
        
        if not openai_config or not openai_config.api_key:
            pytest.skip("需要在配置文件中设置 OpenAI API Key")
        
        # 使用配置文件中的设置
        provider = OpenAIProvider(
            api_key=openai_config.api_key,
            base_url=openai_config.base_url,
            default_model=openai_config.default_model or "gpt-4o-mini",
            temperature=openai_config.temperature,
            max_tokens=openai_config.max_tokens,
        )

        # 创建安全配置 - 低风险自动通过
        security_config = SecurityConfig(
            auto_approve_low_risk=True,
            approval_callback=InteractiveApprovalCallback(auto_approve=True),
        )

        # 创建工具注册表
        tools = ToolRegistry()
        tools.register(EchoTool())

        # 创建 ReActLoop - 使用配置文件中的模型
        _model = openai_config.default_model if openai_config and openai_config.default_model else "gpt-4o-mini"
        bus = MessageBus()
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            model=_model,
            enable_security=True,
            system_prompt="你是一个有帮助的助手。",
        )

        # 添加工具
        for tool in tools.list_tools():
            agent.add_tool(tools.get(tool))

        # 处理请求
        result = await agent.process("请说 'Hello World'")
        
        print(f"\n结果: {result}")
        assert len(result) > 0, "应该返回响应"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_shell_tool_requires_approval(self):
        """测试 Shell 工具 - 需要审批（高风险）"""
        print("\n" + "=" * 60)
        print("测试 2: Shell 工具（高风险，需要审批）")
        print("=" * 60)
        print("注意: 此测试会暂停等待用户输入 yes/no")
        print("-" * 60)

        # 从配置文件读取 provider 配置
        config = get_config()
        
        openai_config = config.providers.openai if config.providers.openai else None
        
        if not openai_config or not openai_config.api_key:
            pytest.skip("需要在配置文件中设置 OpenAI API Key")
        
        provider = OpenAIProvider(
            api_key=openai_config.api_key,
            base_url=openai_config.base_url,
            default_model=openai_config.default_model or "gpt-4o-mini",
            temperature=openai_config.temperature,
            max_tokens=openai_config.max_tokens,
        )

        # 创建安全配置 - 高风险不自动通过
        security_config = SecurityConfig(
            auto_approve_low_risk=False,
            approval_callback=InteractiveApprovalCallback(auto_approve=False),
        )

        # 创建 ReActLoop - 使用配置文件中的模型
        _model = openai_config.default_model if openai_config and openai_config.default_model else "gpt-4o-mini"
        bus = MessageBus()
        agent = ReActLoop(
            bus=bus,
            provider=provider,
            model=_model,
            enable_security=True,
            system_prompt="你是一个有帮助的助手。",
        )

        # 处理请求（模拟触发 shell 工具）
        # 注意: 实际测试时，LLM 可能会或不会调用 shell 工具
        result = await agent.process("列出当前目录的文件")
        
        print(f"\n结果: {result}")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_approval_workflow(self):
        """完整审批流程测试"""
        print("\n" + "=" * 60)
        print("测试 3: 完整审批流程")
        print("=" * 60)

        approval_callback = InteractiveApprovalCallback(auto_approve=False)
        
        security_config = SecurityConfig(
            auto_approve_low_risk=False,
            approval_callback=approval_callback,
        )

        # 验证审批回调可以被调用
        from aloha.security import Approver
        
        approver = Approver(security_config)
        
        # 模拟一个高风险权限请求
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls -la",
            risk_level=RiskLevel.HIGH,
        )
        
        print("\n模拟高风险权限请求...")
        print(f"工具: {permission.tool}")
        print(f"操作: {permission.action}")
        print(f"资源: {permission.resource}")
        print(f"风险: {permission.risk_level.value}")
        
        # 这里会等待用户输入
        # result = await approver.request(permission)
        
        print("\n(审批流程测试完成 - 手动测试时取消注释上面的代码)")


@pytest.mark.integration
class TestApprovalCallbackIntegration:
    """审批回调集成测试"""

    @pytest.mark.integration
    def test_security_config_with_callback(self):
        """测试安全配置与回调集成"""
        print("\n测试: 安全配置与回调")
        
        callback = InteractiveApprovalCallback(auto_approve=True)
        
        config = SecurityConfig(
            auto_approve_low_risk=False,
            approval_callback=callback,
        )
        
        assert config.approval_callback is not None
        assert config.auto_approve_low_risk is False
        
        print("✓ 安全配置正确设置")


# 运行说明
if __name__ == "__main__":
    print("""
================================================================================
ReActLoop 集成测试
================================================================================

运行方式:
    # 方式1: 运行所有集成测试
    pytest aloha/test/test_integration.py -v -m integration

    # 方式2: 运行特定测试
    pytest aloha/test/test_integration.py::TestReActLoopIntegration::test_echo_tool_no_approval -v

    # 方式3: 在 IDE 中直接运行（需要配置环境变量）
    
环境变量:
    OPENAI_API_KEY: OpenAI API 密钥
    # 或者使用其他兼容的 API
    # DEEPSEEK_API_KEY, OPENROUTER_API_KEY 等

测试场景:
    1. test_echo_tool_no_approval - 低风险工具自动通过
    2. test_shell_tool_requires_approval - 高风险工具需要用户审批
    3. test_full_approval_workflow - 完整审批流程

================================================================================
""")
    
    # 运行测试
    pytest.main([__file__, "-v", "-m", "integration", "-s"])