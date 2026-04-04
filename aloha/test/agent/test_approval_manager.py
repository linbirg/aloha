"""ApprovalManager 测试"""

import pytest
import asyncio
from aloha.agent.approval_manager import ApprovalManager
from aloha.agent.events import ApprovalRequest, RiskLevel


class TestApprovalManager:
    @pytest.mark.asyncio
    async def test_enqueue_returns_true_first_time(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        result = await manager.enqueue(request)
        assert result is True

    @pytest.mark.asyncio
    async def test_enqueue_returns_false_duplicate(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        result = await manager.enqueue(request)
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_approved(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        result = manager.resolve("appr-001", "approved", None)
        assert result is True

    @pytest.mark.asyncio
    async def test_resolve_rejected(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        result = manager.resolve("appr-001", "rejected", "not needed")
        assert result is True

    @pytest.mark.asyncio
    async def test_resolve_idempotent(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        manager.resolve("appr-001", "approved", None)
        result = manager.resolve("appr-001", "approved", None)
        assert result is False

    @pytest.mark.asyncio
    async def test_wait_returns_approved(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)

        async def resolve_later():
            await asyncio.sleep(0.1)
            manager.resolve("appr-001", "approved", None)

        async def wait_task():
            result = await manager.wait("appr-001")
            assert result is True

        await asyncio.gather(resolve_later(), wait_task())

    @pytest.mark.asyncio
    async def test_wait_returns_false_on_timeout(self):
        manager = ApprovalManager(default_timeout=0.1)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        result = await manager.wait("appr-001")
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_approved_wait_returns_true_immediately(self):
        manager = ApprovalManager(default_timeout=5)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await manager.enqueue(request)
        manager.resolve("appr-001", "approved", None)
        result = await manager.wait("appr-001")
        assert result is True

    @pytest.mark.asyncio
    async def test_timeout_task_auto_rejects(self):
        manager = ApprovalManager(default_timeout=0.2)
        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
            timeout=0.2,
        )

        await manager.enqueue(request)

        result = await manager.wait("appr-001")
        assert result is False

        await asyncio.sleep(0.1)
        decision = manager.get_decision("appr-001")
        assert decision is not None
        assert decision.decision == "rejected"
        assert decision.reason == "timeout"
