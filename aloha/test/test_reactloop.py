"""ReActLoop 核心逻辑单元测试

测试模块：
1. PermissionChecker - 权限检查
2. Approver - 审批流程
3. ToolWrapper - 工具包装器
4. ReActLoop - 主循环
"""

import sys
import os

# 获取项目根目录 (aloha/ 的父目录)
_current_file = os.path.abspath(__file__)
_test_dir = os.path.dirname(_current_file)  # aloha/test/
_project_root = os.path.dirname(_test_dir)  # aloha/

# 尝试多种可能的根目录
_possible_roots = [
    _project_root,
    os.getcwd(),
    os.path.join(os.getcwd(), "aloha"),
]

for _root in _possible_roots:
    if _root not in sys.path and os.path.isdir(os.path.join(_root, "aloha")):
        sys.path.insert(0, _root)

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from aloha.agent.tools import ToolRegistry, BaseTool, ToolResult
from aloha.agent.wrapper import ToolWrapper
from aloha.security.checker import PermissionChecker
from aloha.security.approver import Approver
from aloha.security.policy import (
    Permission, RiskLevel, SecurityConfig, ApprovalCallback
)
from aloha.providers.base import Message, Response, ToolCall


# ============================================================================
# 测试辅助类
# ============================================================================

class MockApprovalCallback:
    """模拟审批回调"""

    def __init__(self, should_approve: bool = True, should_timeout: bool = False):
        self.should_approve = should_approve
        self.should_timeout = should_timeout
        self.called = False
        self.received_permission = None

    async def request_approval(self, permission: Permission) -> bool:
        self.called = True
        self.received_permission = permission
        if self.should_timeout:
            await asyncio.sleep(10)  # 超时
        return self.should_approve

    async def request_approval_with_timeout(
        self, permission: Permission, timeout: float
    ) -> bool:
        self.called = True
        self.received_permission = permission
        if self.should_timeout:
            await asyncio.sleep(timeout + 1)
        return self.should_approve

    async def notify(self, message: str) -> None:
        pass


class MockTool(BaseTool):
    """模拟工具用于测试"""

    def __init__(self, name: str = "mock_tool", should_succeed: bool = True):
        super().__init__(name=name, description="Mock tool for testing")
        self.should_succeed = should_succeed
        self.call_count = 0

    async def execute(self, **kwargs) -> ToolResult:
        self.call_count += 1
        if self.should_succeed:
            return ToolResult(
                success=True,
                content=f"Mock executed: {kwargs}",
                metadata={"call_count": self.call_count}
            )
        return ToolResult(
            success=False,
            content="",
            error="Mock tool failure"
        )


class MockLLMProvider:
    """模拟 LLM Provider - 支持工具调用"""

    def __init__(self, responses: list[Response]):
        self.responses = responses
        self.call_count = 0

    async def chat_with_tools(self, messages, tools, model) -> Response:
        if self.call_count >= len(self.responses):
            return Response(content="No more responses", model=model)
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp


# ============================================================================
# Test PermissionChecker - 权限检查
# ============================================================================

class TestPermissionChecker:
    """测试 PermissionChecker 权限检查"""

    @pytest.fixture
    def security_config(self, tmp_path):
        """创建测试用安全配置"""
        return SecurityConfig(
            file_read_allowed_dirs=[tmp_path / "read"],
            file_write_allowed_dirs=[tmp_path / "write"],
            shell_allowed_commands=["ls", "cat", "echo"],
            shell_blocked_patterns=[r"rm\s+-rf", r"del\s+/[sq]"],
            web_allowed_domains=["example.com", "test.com"],
        )

    @pytest.fixture
    def checker(self, security_config):
        """创建权限检查器"""
        return PermissionChecker(security_config)

    # ----- 文件权限测试 -----

    @pytest.mark.unit
    def test_file_read_allowed_in_whitelist(self, checker, tmp_path):
        """FILE-001: 允许目录内的文件-read"""
        allowed_dir = tmp_path / "read"
        allowed_dir.mkdir()
        test_file = allowed_dir / "test.txt"
        test_file.write_text("test")

        permission = Permission(
            tool="file",
            action="read",
            resource=str(test_file),
        )

        allowed, reason = checker.check(permission)
        assert allowed is True
        assert "Allowed" in reason

    @pytest.mark.unit
    def test_file_read_outside_allowed_dirs(self, checker, tmp_path):
        """FILE-002: 允许目录外的文件-read"""
        # 不在 allowed_dirs 且不在 cwd
        permission = Permission(
            tool="file",
            action="read",
            resource="/usr/bin/important.txt",
        )

        allowed, reason = checker.check(permission)
        assert allowed is False

    @pytest.mark.unit
    def test_file_read_in_cwd(self, checker):
        """FILE-003: CWD内的文件-read"""
        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_file_write_allowed_in_whitelist(self, checker, tmp_path):
        """FILE-004: 允许目录内的文件-write"""
        write_dir = tmp_path / "write"
        write_dir.mkdir()

        permission = Permission(
            tool="file",
            action="write",
            resource=str(write_dir / "output.txt"),
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_file_write_blocked_extension(self, checker, tmp_path):
        """FILE-005: 阻塞扩展名-write"""
        write_dir = tmp_path / "write"
        write_dir.mkdir()

        permission = Permission(
            tool="file",
            action="write",
            resource=str(write_dir / "malware.exe"),
        )

        allowed, reason = checker.check(permission)
        assert allowed is False
        assert "blocked" in reason.lower()

    # ----- Shell 权限测试 -----

    @pytest.mark.unit
    def test_shell_allowed_command(self, checker):
        """SHELL-001: 允许的命令"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls -la",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_shell_disallowed_command(self, checker):
        """SHELL-002: 不允许的命令"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="rm -rf /",
        )

        allowed, reason = checker.check(permission)
        assert allowed is False
        assert "not in allowed" in reason.lower()

    @pytest.mark.unit
    def test_shell_empty_command(self, checker):
        """SHELL-003: 空命令"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="",
        )

        allowed, reason = checker.check(permission)
        assert allowed is False

    @pytest.mark.unit
    def test_shell_blocked_pattern(self, checker):
        """SHELL-004: 匹配黑名单模式"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="rm -rf /home/user",
        )

        allowed, reason = checker.check(permission)
        assert allowed is False

    @pytest.mark.unit
    def test_shell_case_insensitive(self, checker):
        """SHELL-005: 大小写不敏感"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="LS -la",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    # ----- Web 权限测试 -----

    @pytest.mark.unit
    def test_web_all_domains_allowed(self, checker):
        """WEB-001: 允许所有域名"""
        config = SecurityConfig(web_allowed_domains=["*"])
        checker = PermissionChecker(config)

        permission = Permission(
            tool="web",
            action="fetch",
            resource="https://any-domain.com/page",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_web_whitelisted_domain(self, checker):
        """WEB-002: 白名单域名"""
        permission = Permission(
            tool="web",
            action="fetch",
            resource="https://example.com/page",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_web_subdomain_allowed(self, checker):
        """WEB-003: 白名单子域名"""
        permission = Permission(
            tool="web",
            action="fetch",
            resource="https://api.example.com/page",
        )

        allowed, reason = checker.check(permission)
        assert allowed is True

    @pytest.mark.unit
    def test_web_not_whitelisted_domain(self, checker):
        """WEB-004: 不允许的域名"""
        permission = Permission(
            tool="web",
            action="fetch",
            resource="https://malicious.com/page",
        )

        allowed, reason = checker.check(permission)
        assert allowed is False

    # ----- 风险评估测试 -----

    @pytest.mark.unit
    def test_risk_shell_high(self, checker):
        """RISK-001: Shell工具高风险"""
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls",
        )

        risk = checker.assess_risk(permission)
        assert risk == RiskLevel.HIGH

    @pytest.mark.unit
    def test_risk_file_write_high(self, checker):
        """RISK-002: 文件写高风险"""
        permission = Permission(
            tool="file",
            action="write",
            resource="test.txt",
        )

        risk = checker.assess_risk(permission)
        assert risk == RiskLevel.HIGH

    @pytest.mark.unit
    def test_risk_file_read_medium(self, checker):
        """RISK-003: 文件读中风险"""
        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
        )

        risk = checker.assess_risk(permission)
        assert risk == RiskLevel.MEDIUM

    @pytest.mark.unit
    def test_risk_web_medium(self, checker):
        """RISK-004: Web操作中风险"""
        permission = Permission(
            tool="web",
            action="fetch",
            resource="https://example.com",
        )

        risk = checker.assess_risk(permission)
        assert risk == RiskLevel.MEDIUM


# ============================================================================
# Test Approver - 审批流程
# ============================================================================

class TestApprover:
    """测试 Approver 审批流程"""

    @pytest.fixture
    def security_config(self):
        """创建测试用安全配置"""
        return SecurityConfig()

    @pytest.mark.unit
    async def test_low_risk_auto_approve(self, security_config):
        """APRV-001: 低风险自动通过"""
        security_config.auto_approve_low_risk = True
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.LOW,
        )

        result = await approver.request(permission)
        assert result is True

    @pytest.mark.unit
    async def test_low_risk_no_auto_approve(self, security_config):
        """APRV-002: 低风险关闭自动通过"""
        security_config.auto_approve_low_risk = False
        security_config.approval_callback = MockApprovalCallback(should_approve=True)
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.LOW,
        )

        result = await approver.request(permission)
        assert result is True

    @pytest.mark.unit
    async def test_medium_risk_requires_approval(self, security_config):
        """APRV-003: 中风险需要审批"""
        callback = MockApprovalCallback(should_approve=True)
        security_config.approval_callback = callback
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        result = await approver.request(permission)
        assert result is True
        assert callback.called is True

    @pytest.mark.unit
    async def test_high_risk_requires_approval(self, security_config):
        """APRV-004: 高风险需要审批"""
        callback = MockApprovalCallback(should_approve=True)
        security_config.approval_callback = callback
        approver = Approver(security_config)

        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls",
            risk_level=RiskLevel.HIGH,
        )

        result = await approver.request(permission)
        assert result is True
        assert callback.called is True

    @pytest.mark.unit
    async def test_callback_exception_denies(self, security_config):
        """APRV-005: 回调异常时拒绝"""
        async def raise_error(permission):
            raise Exception("Test error")
        
        callback = MagicMock()
        callback.request_approval = raise_error
        security_config.approval_callback = callback
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        result = await approver.request(permission)
        assert result is False

    @pytest.mark.unit
    async def test_no_callback_denies(self, security_config):
        """APRV-006: 无回调默认拒绝"""
        security_config.approval_callback = None
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        result = await approver.request(permission)
        assert result is False

    # ----- 阻塞审批测试 -----

    @pytest.mark.unit
    async def test_blocking_approval_timeout(self, security_config):
        """BLOCK-001: 超时测试 - 模拟不支持超时回调时使用 asyncio.wait_for"""
        # 创建一个不支持 request_approval_with_timeout 的回调
        # 使用 wait_for 会超时
        async def slow_approval(permission):
            await asyncio.sleep(10)  # 永远不返回
            return True
        
        callback = MagicMock()
        callback.request_approval = slow_approval
        callback.request_approval_with_timeout = None  # 不支持
        security_config.approval_callback = callback
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        result = await approver.request_with_blocking(permission, timeout=0.1)
        assert result is False

    @pytest.mark.unit
    async def test_blocking_with_timeout_callback(self, security_config):
        """BLOCK-002: 带超时的回调"""
        callback = MockApprovalCallback(should_approve=True)
        security_config.approval_callback = callback
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        result = await approver.request_with_blocking(permission, timeout=1.0)
        assert result is True

    # ----- 审批提示测试 -----

    @pytest.mark.unit
    def test_approval_prompt_low_risk(self, security_config):
        """PROMPT-001: 低风险提示"""
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.LOW,
        )

        prompt = approver.create_approval_prompt(permission)
        assert "🟢" in prompt

    @pytest.mark.unit
    def test_approval_prompt_medium_risk(self, security_config):
        """PROMPT-002: 中风险提示"""
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        prompt = approver.create_approval_prompt(permission)
        assert "🟡" in prompt

    @pytest.mark.unit
    def test_approval_prompt_high_risk(self, security_config):
        """PROMPT-003: 高风险提示"""
        approver = Approver(security_config)

        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls",
            risk_level=RiskLevel.HIGH,
        )

        prompt = approver.create_approval_prompt(permission)
        assert "🔴" in prompt

    @pytest.mark.unit
    def test_approval_prompt_content(self, security_config):
        """PROMPT-004: 提示内容完整性"""
        approver = Approver(security_config)

        permission = Permission(
            tool="file",
            action="read",
            resource="/path/to/file.txt",
            risk_level=RiskLevel.HIGH,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        prompt = approver.create_approval_prompt(permission)
        assert "file" in prompt
        assert "read" in prompt
        assert "file.txt" in prompt
        assert "HIGH" in prompt


# ============================================================================
# Test ToolWrapper - 工具包装器
# ============================================================================

class TestToolWrapper:
    """测试 ToolWrapper 工具包装器"""

    @pytest.fixture
    def registry(self):
        """创建工具注册表"""
        reg = ToolRegistry()
        reg.register(MockTool(name="file"))
        reg.register(MockTool(name="shell"))
        return reg

    @pytest.fixture
    def security_config(self):
        """创建安全配置"""
        config = SecurityConfig()
        config.approval_callback = MockApprovalCallback(should_approve=True)
        return config

    @pytest.mark.unit
    async def test_security_disabled_executes_directly(self, registry, security_config):
        """WRAP-001: 安全禁用时直接执行"""
        wrapper = ToolWrapper(registry, security_config, enable_security=False)

        result = await wrapper.execute("file", path="test.txt")

        assert result.success is True

    @pytest.mark.unit
    async def test_tool_not_found(self, registry, security_config):
        """WRAP-002: 工具不存在"""
        wrapper = ToolWrapper(registry, security_config, enable_security=True)

        result = await wrapper.execute("nonexistent")

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.unit
    async def test_permission_denied(self, registry, security_config):
        """WRAP-003: 权限检查拒绝"""
        # 配置拒绝所有 shell 命令
        security_config.shell_allowed_commands = []
        wrapper = ToolWrapper(registry, security_config, enable_security=True)

        result = await wrapper.execute("shell", command="ls")

        assert result.success is False
        assert "Permission denied" in result.error

    @pytest.mark.unit
    async def test_approval_rejected(self, registry, security_config):
        """WRAP-004: 审批被拒绝"""
        # 设置 auto_approve_low_risk=False 确保需要审批
        security_config.auto_approve_low_risk = False
        security_config.approval_callback = MockApprovalCallback(should_approve=False)
        wrapper = ToolWrapper(registry, security_config, enable_security=True)

        result = await wrapper.execute("file", path="test.txt")

        assert result.success is False
        assert "rejected" in result.error.lower()

    @pytest.mark.unit
    async def test_approval_success_executes_tool(self, registry, security_config):
        """WRAP-005: 审批通过-执行成功"""
        security_config.approval_callback = MockApprovalCallback(should_approve=True)
        wrapper = ToolWrapper(registry, security_config, enable_security=True)

        result = await wrapper.execute("file", path="test.txt")

        assert result.success is True

    @pytest.mark.unit
    async def test_approval_success_tool_fails(self, registry, security_config):
        """WRAP-006: 审批通过-执行失败"""
        reg = ToolRegistry()
        reg.register(MockTool(name="fail_tool", should_succeed=False))
        security_config.approval_callback = MockApprovalCallback(should_approve=True)
        wrapper = ToolWrapper(reg, security_config, enable_security=True)

        result = await wrapper.execute("fail_tool")

        assert result.success is False
        assert "failure" in result.error.lower()

    @pytest.mark.unit
    async def test_audit_log_records(self, registry, security_config):
        """WRAP-007: 审计日志记录"""
        security_config.approval_callback = MockApprovalCallback(should_approve=True)
        wrapper = ToolWrapper(registry, security_config, enable_security=True)

        await wrapper.execute("file", path="test.txt")

        logs = wrapper.get_audit_logs()
        assert len(logs) > 0

    # ----- 权限构建测试 -----

    @pytest.mark.unit
    def test_build_permission_file(self, registry, security_config):
        """PERM-001: 构建文件工具权限"""
        wrapper = ToolWrapper(registry, security_config)

        permission = wrapper._build_permission("file", {"path": "/test/file.txt"})

        assert permission.tool == "file"
        assert permission.resource == "/test/file.txt"

    @pytest.mark.unit
    def test_build_permission_shell(self, registry, security_config):
        """PERM-002: 构建shell工具权限"""
        wrapper = ToolWrapper(registry, security_config)

        permission = wrapper._build_permission("shell", {"command": "ls -la"})

        assert permission.tool == "shell"
        assert permission.resource == "ls -la"

    @pytest.mark.unit
    def test_build_permission_web(self, registry, security_config):
        """PERM-003: 构建web工具权限"""
        wrapper = ToolWrapper(registry, security_config)

        permission = wrapper._build_permission("web", {"url": "https://example.com"})

        assert permission.tool == "web"
        assert permission.resource == "https://example.com"


# ============================================================================
# Test ReActLoop - 主循环
# ============================================================================

class TestReActLoop:
    """测试 ReActLoop 主循环"""

    @pytest.fixture
    def mock_provider(self):
        """创建模拟 LLM Provider"""
        return MagicMock()

    @pytest.fixture
    def mock_bus(self):
        """创建模拟消息总线"""
        return MagicMock()

    # ----- 工具调用循环测试 -----

    @pytest.mark.unit
    async def test_no_tool_calls_simple_response(self, mock_provider, mock_bus):
        """REACT-001: 无工具调用的简单响应"""
        from aloha.agent.loop import ReActLoop

        # 设置 mock 返回无工具调用的响应
        mock_provider.chat_with_tools = AsyncMock(
            return_value=Response(
                content="Hello, I am a helpful assistant.",
                tool_calls=None,
                model="test"
            )
        )

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            enable_security=False,
        )

        result = await agent.process("Hello")

        assert result == "Hello, I am a helpful assistant."
        # 验证工具没有被调用
        assert len(agent.session_memory.get_messages()) > 0

    @pytest.mark.unit
    async def test_single_tool_call(self, mock_provider, mock_bus):
        """REACT-002: 单次工具调用"""
        from aloha.agent.loop import ReActLoop

        # 第一次调用返回工具调用，第二次返回最终响应
        tool_call = ToolCall(
            id="call_1",
            name="file",
            arguments={"path": "test.txt", "operation": "read"}
        )

        mock_provider.chat_with_tools = AsyncMock(
            side_effect=[
                Response(content="I'll read the file", tool_calls=[tool_call], model="test"),
                Response(content="File content: hello", tool_calls=None, model="test"),
            ]
        )

        # 创建并配置 mock 工具
        mock_tool = MockTool(name="file", should_succeed=True)

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            enable_security=False,
        )
        agent.add_tool(mock_tool)

        result = await agent.process("Read the file")

        assert "File content" in result
        assert mock_tool.call_count == 1

    @pytest.mark.unit
    async def test_multiple_tool_calls(self, mock_provider, mock_bus):
        """REACT-003: 多次工具调用"""
        from aloha.agent.loop import ReActLoop

        tool_calls = [
            ToolCall(id="call_1", name="shell", arguments={"command": "ls"}),
            ToolCall(id="call_2", name="shell", arguments={"command": "pwd"}),
        ]

        mock_provider.chat_with_tools = AsyncMock(
            side_effect=[
                Response(content="Executing commands", tool_calls=tool_calls, model="test"),
                Response(content="Done", tool_calls=None, model="test"),
            ]
        )

        mock_tool = MockTool(name="shell", should_succeed=True)

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            enable_security=False,
        )
        agent.add_tool(mock_tool)

        result = await agent.process("Run commands")

        assert "Done" in result
        assert mock_tool.call_count == 2

    @pytest.mark.unit
    async def test_tool_execution_failure(self, mock_provider, mock_bus):
        """REACT-006: 工具执行失败处理"""
        from aloha.agent.loop import ReActLoop

        tool_call = ToolCall(
            id="call_1",
            name="file",
            arguments={"path": "test.txt", "operation": "read"}
        )

        mock_provider.chat_with_tools = AsyncMock(
            side_effect=[
                Response(content="Trying to read", tool_calls=[tool_call], model="test"),
                Response(content="Tool failed, please try again", tool_calls=None, model="test"),
            ]
        )

        # 工具返回失败
        mock_tool = MockTool(name="file", should_succeed=False)

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            enable_security=False,
        )
        agent.add_tool(mock_tool)

        result = await agent.process("Read the file")

        # 应该返回最终的响应
        assert "failed" in result.lower() or "tool" in result.lower()

    # ----- 消息构建测试 -----

    @pytest.mark.unit
    async def test_message_building_with_system_prompt(self, mock_provider, mock_bus):
        """MSG-001: 构建带系统提示的消息"""
        from aloha.agent.loop import ReActLoop

        mock_provider.chat_with_tools = AsyncMock(
            return_value=Response(content="Response", model="test")
        )

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            system_prompt="You are a coding assistant.",
            enable_security=False,
        )

        await agent.process("Hello")

        messages = agent._build_messages()
        assert any(m.role == "system" for m in messages)

    @pytest.mark.unit
    async def test_message_building_with_history(self, mock_provider, mock_bus):
        """MSG-002: 构建带会话历史的消息"""
        from aloha.agent.loop import ReActLoop

        mock_provider.chat_with_tools = AsyncMock(
            return_value=Response(content="Response 1", model="test")
        )

        agent = ReActLoop(
            bus=mock_bus,
            provider=mock_provider,
            model="test",
            enable_security=False,
        )

        await agent.process("First message")
        messages = agent._build_messages()

        # 应该有用户消息和助手消息
        assert len(messages) >= 2


# ============================================================================
# 集成测试（可选）
# ============================================================================

@pytest.mark.integration
class TestReActLoopIntegration:
    """集成测试 - 使用真实或半真实环境"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.environ.get("ALOHA_TEST_INTEGRATION"),
        reason="Integration tests disabled"
    )
    async def test_with_real_provider(self):
        """使用真实 Provider 的集成测试"""
        # 这个测试需要在环境变量中设置 ALOHA_TEST_INTEGRATION=1
        # 并且需要配置有效的 API 密钥
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])