"""Gradio UI 审批流程测试

测试 chat_with_ai.py 中的审批流程逻辑：
1. GradioApprovalCallback 是否正确发送审批请求到队列
2. process_approval_queue 是否正确处理审批请求
3. 审批请求是否能正确显示在 UI 上
"""

import sys
import os

# 确保项目根目录在 Python 路径中
_current_file = os.path.abspath(__file__)
_test_dir = os.path.dirname(_current_file)
_project_root = os.path.dirname(_test_dir)

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
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

# 导入被测试的模块
from aloha.security.policy import Permission, RiskLevel
from aloha.security.approver import Approver
from aloha.security import SecurityConfig


# 模拟 GradioApprovalCallback（从 chat_with_ai.py 复制）
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
        
        # 等待用户响应 - 使用轮询方式检测响应
        start_time = asyncio.get_event_loop().time()
        while True:
            # 检查是否已有响应
            if self._response is not None:
                result = self._response
                self._response = None
                self._response_event.clear()
                return result is True
            
            # 检查是否超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= 60:
                return False
            
            # 短暂等待后再次检查
            await asyncio.sleep(0.1)

    async def request_approval_with_timeout(self, permission: Permission, timeout: float) -> bool:
        """请求用户批准，带超时时间"""
        await self.gradio_queue.put({
            "type": "approval_request",
            "tool": permission.tool,
            "action": permission.action,
            "resource": permission.resource,
            "risk_level": permission.risk_level.value,
        })
        
        start_time = asyncio.get_event_loop().time()
        while True:
            if self._response is not None:
                result = self._response
                self._response = None
                self._response_event.clear()
                return result is True
            
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                return False
            
            await asyncio.sleep(0.1)

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


# 全局变量（模拟 chat_with_ai.py）
pending_approvals = {}
approval_counter = 0


async def process_approval_queue(approval_queue: asyncio.Queue):
    """处理审批队列 - 模拟 chat_with_ai.py 中的函数"""
    global pending_approvals, approval_counter

    while not approval_queue.empty():
        try:
            msg = await asyncio.wait_for(approval_queue.get(), timeout=0.1)

            if msg.get("type") == "approval_request":
                approval_id = f"approval_{approval_counter}"
                approval_counter += 1

                pending_approvals[approval_id] = {
                    "tool": msg["tool"],
                    "action": msg["action"],
                    "resource": msg["resource"],
                    "risk_level": msg["risk_level"],
                }

        except asyncio.TimeoutError:
            break
        except Exception as e:
            print(f"Error processing approval queue: {e}")
            break


class TestGradioApprovalCallback:
    """测试 GradioApprovalCallback"""

    @pytest.mark.unit
    async def test_approval_request_sent_to_queue(self):
        """测试 1: 审批请求是否被发送到队列"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)

        # 创建一个高风险的权限请求
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls -la",
            risk_level=RiskLevel.HIGH,
        )

        # 启动审批请求（不等待完成，因为会阻塞等待响应）
        approval_task = asyncio.create_task(callback.request_approval(permission))
        
        # 等待一小段时间，让请求进入队列
        await asyncio.sleep(0.2)
        
        # 检查队列中是否有审批请求
        assert not queue.empty(), "队列应该包含审批请求"
        
        # 取出请求
        msg = await queue.get()
        
        assert msg["type"] == "approval_request", "消息类型应该是 approval_request"
        assert msg["tool"] == "shell", "工具应该是 shell"
        assert msg["action"] == "execute", "动作应该是 execute"
        assert msg["risk_level"] == "high", "风险级别应该是 high"
        
        # 清理：设置响应以结束等待
        callback.set_response(True)
        await approval_task

    @pytest.mark.unit
    async def test_approval_response_received(self):
        """测试 2: 审批响应是否能被正确接收"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)

        # 创建一个高风险的权限请求
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls",
            risk_level=RiskLevel.HIGH,
        )

        # 启动审批请求
        approval_task = asyncio.create_task(callback.request_approval(permission))
        
        # 等待请求被处理
        await asyncio.sleep(0.2)
        
        # 模拟用户批准
        callback.set_response(True)
        
        # 等待审批完成
        result = await approval_task
        
        assert result is True, "审批应该被批准"

    @pytest.mark.unit
    async def test_approval_rejected(self):
        """测试 3: 审批被拒绝"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)

        permission = Permission(
            tool="shell",
            action="execute",
            resource="rm -rf",
            risk_level=RiskLevel.HIGH,
        )

        approval_task = asyncio.create_task(callback.request_approval(permission))
        await asyncio.sleep(0.2)
        
        # 模拟用户拒绝
        callback.set_response(False)
        
        result = await approval_task
        
        assert result is False, "审批应该被拒绝"

    @pytest.mark.unit
    async def test_set_response_before_request(self):
        """测试 4: 在请求之前设置响应"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)

        # 先设置响应
        callback.set_response(True)
        
        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.MEDIUM,
        )

        # 由于响应已设置，应该立即返回
        result = await callback.request_approval(permission)
        
        assert result is True, "应该立即返回 True"


class TestProcessApprovalQueue:
    """测试 process_approval_queue 函数"""

    @pytest.mark.unit
    async def test_process_single_approval_request(self):
        """测试 5: 处理单个审批请求"""
        global pending_approvals, approval_counter
        pending_approvals = {}
        approval_counter = 0
        
        queue = asyncio.Queue()
        
        # 放入一个审批请求
        await queue.put({
            "type": "approval_request",
            "tool": "shell",
            "action": "execute",
            "resource": "ls",
            "risk_level": "high",
        })
        
        # 处理队列
        await process_approval_queue(queue)
        
        # 检查 pending_approvals
        assert len(pending_approvals) == 1, "应该有1个待审批请求"
        
        approval_id = list(pending_approvals.keys())[0]
        assert pending_approvals[approval_id]["tool"] == "shell"
        assert pending_approvals[approval_id]["action"] == "execute"

    @pytest.mark.unit
    async def test_process_multiple_approval_requests(self):
        """测试 6: 处理多个审批请求"""
        global pending_approvals, approval_counter
        pending_approvals = {}
        approval_counter = 0
        
        queue = asyncio.Queue()
        
        # 放入多个审批请求
        for i in range(3):
            await queue.put({
                "type": "approval_request",
                "tool": "file",
                "action": "read",
                "resource": f"file{i}.txt",
                "risk_level": "medium",
            })
        
        # 处理队列
        await process_approval_queue(queue)
        
        # 检查 pending_approvals
        assert len(pending_approvals) == 3, "应该有3个待审批请求"

    @pytest.mark.unit
    async def test_process_empty_queue(self):
        """测试 7: 处理空队列"""
        global pending_approvals
        pending_approvals = {}
        
        queue = asyncio.Queue()
        
        # 处理空队列
        await process_approval_queue(queue)
        
        # 检查 pending_approvals
        assert len(pending_approvals) == 0, "不应该有待审批请求"


class TestApprovalWorkflow:
    """测试完整的审批工作流程"""

    @pytest.mark.unit
    async def test_full_approval_workflow(self):
        """测试 8: 完整的审批流程（模拟真实场景）"""
        global pending_approvals, approval_counter
        pending_approvals = {}
        approval_counter = 0
        
        # 1. 创建队列和回调
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)
        
        # 2. 创建安全配置和审批器
        security_config = SecurityConfig(
            auto_approve_low_risk=False,
            approval_callback=callback,
        )
        approver = Approver(security_config)
        
        # 3. 创建一个高风险权限请求
        permission = Permission(
            tool="shell",
            action="execute",
            resource="ls -la",
            risk_level=RiskLevel.HIGH,
        )
        
        # 4. 请求审批（异步，不等待结果）
        approval_task = asyncio.create_task(approver.request(permission))
        
        # 5. 处理审批队列
        await asyncio.sleep(0.2)  # 等待审批请求进入队列
        await process_approval_queue(queue)
        
        # 6. 验证审批请求已被添加到 pending_approvals
        assert len(pending_approvals) > 0, "审批请求应该被添加到待审批列表"
        
        # 7. 获取审批请求信息
        approval_id = list(pending_approvals.keys())[0]
        approval_info = pending_approvals[approval_id]
        
        assert approval_info["tool"] == "shell"
        assert approval_info["risk_level"] == "high"
        
        # 8. 模拟用户批准
        callback.set_response(True)
        
        # 9. 等待审批完成
        result = await approval_task
        
        # 10. 验证结果
        assert result is True, "用户批准后审批应该通过"
        
        # 11. 清理 pending_approvals（模拟 UI 中的删除操作）
        del pending_approvals[approval_id]
        assert len(pending_approvals) == 0, "审批处理后应该从列表中移除"

    @pytest.mark.unit
    async def test_low_risk_auto_approve(self):
        """测试 9: 低风险自动通过"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)
        
        security_config = SecurityConfig(
            auto_approve_low_risk=True,  # 启用低风险自动通过
            approval_callback=callback,
        )
        approver = Approver(security_config)
        
        # 低风险权限请求
        permission = Permission(
            tool="file",
            action="read",
            resource="test.txt",
            risk_level=RiskLevel.LOW,
        )
        
        # 请求审批 - 应该自动通过，不发送请求到队列
        result = await approver.request(permission)
        
        assert result is True, "低风险应该自动通过"
        assert queue.empty(), "低风险不应该发送请求到队列"


class TestSecurityConfig:
    """测试安全配置"""

    @pytest.mark.unit
    def test_security_config_default(self):
        """测试 10: 默认安全配置"""
        config = SecurityConfig()
        
        # 默认应该允许低风险自动通过
        assert config.auto_approve_low_risk is True
        
        # 默认没有审批回调
        assert config.approval_callback is None

    @pytest.mark.unit
    def test_security_config_with_callback(self):
        """测试 11: 带回调的安全配置"""
        queue = asyncio.Queue()
        callback = GradioApprovalCallback(queue)
        
        config = SecurityConfig(
            auto_approve_low_risk=False,
            approval_callback=callback,
        )
        
        assert config.auto_approve_low_risk is False
        assert config.approval_callback is callback


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "unit"])