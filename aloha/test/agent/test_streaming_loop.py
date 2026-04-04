"""StreamingReActLoop 测试"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from pathlib import Path

from aloha.agent.loop import StreamingReActLoop
from aloha.agent.approval_manager import ApprovalManager
from aloha.agent.events import ApprovalRequest, RiskLevel
from aloha.web.service.events import EventManager
from aloha.providers.base import Message, Response, ToolCall
from aloha.bus import MessageBus


class MockProvider:
    def __init__(self):
        self.default_model = "test-model"

    async def chat(
        self, messages, model=None, temperature=None, max_tokens=None, tools=None
    ):
        return Response(
            content="test response",
            model=model or self.default_model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
        )

    async def chat_with_tools(
        self, messages, model=None, temperature=None, max_tokens=None, tools=None
    ):
        return Response(
            content="test response",
            model=model or self.default_model,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            finish_reason="stop",
            tool_calls=[],
        )


class TestStreamingReActLoop:
    @pytest.mark.asyncio
    async def test_approval_emitted_on_high_risk_tool(self):
        event_manager = EventManager()
        approval_manager = ApprovalManager(default_timeout=5)
        bus = MessageBus()

        tool_calls = [
            ToolCall(
                id="tc-001",
                name="file",
                arguments={
                    "operation": "write",
                    "path": "/tmp/test.txt",
                    "content": "hello",
                },
            )
        ]

        mock_provider = MagicMock()
        mock_provider.default_model = "test-model"
        mock_provider.chat_with_tools = AsyncMock(
            return_value=Response(
                content="",
                model="test-model",
                usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
                finish_reason="tool_calls",
                tool_calls=tool_calls,
            )
        )

        loop = StreamingReActLoop(
            event_manager=event_manager,
            approval_manager=approval_manager,
            session_id="test-session",
            bus=bus,
            provider=mock_provider,
            workspace=Path("/tmp"),
            model="test-model",
            enable_security=False,
        )

        queue = asyncio.Queue()
        event_manager.add_client("test-session", queue)

        async def run():
            async def resolve_later():
                await asyncio.sleep(0.2)
                approval_manager.resolve("appr-tc-001", "approved", None)

            task = asyncio.create_task(resolve_later())
            try:
                result = await loop.process_streaming("test input")
                return result
            finally:
                await task

        async def collect_events():
            events = []
            while len(events) < 3:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=1.0)
                    events.append(msg)
                except asyncio.TimeoutError:
                    break
            return events

        run_task = asyncio.create_task(run())
        events_task = asyncio.create_task(collect_events())

        done, pending = await asyncio.wait(
            [run_task, events_task],
            timeout=5.0,
            return_when=asyncio.ALL_COMPLETED,
        )

        events = events_task.result()
        approval_required_found = any(
            "approval_required" in msg for msg in events if isinstance(msg, str)
        )
        assert approval_required_found, (
            f"approval_required not found in events: {events}"
        )

    @pytest.mark.asyncio
    async def test_wait_blocks_until_approval(self):
        event_manager = EventManager()
        approval_manager = ApprovalManager(default_timeout=5)

        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
        )

        await approval_manager.enqueue(request)

        async def resolve_later():
            await asyncio.sleep(0.1)
            approval_manager.resolve("appr-001", "approved", None)

        async def wait_task():
            result = await approval_manager.wait("appr-001")
            return result

        result = await asyncio.gather(resolve_later(), wait_task())
        assert result[1] is True

    @pytest.mark.asyncio
    async def test_timeout_rejected(self):
        event_manager = EventManager()
        approval_manager = ApprovalManager(default_timeout=0.1)

        request = ApprovalRequest(
            id="appr-001",
            tool_name="file",
            action="write",
            arguments={"path": "/tmp/test.txt"},
            risk_level=RiskLevel.HIGH,
            description="写入文件",
            resource="/tmp/test.txt",
            timeout=0.1,
        )

        await approval_manager.enqueue(request)
        result = await approval_manager.wait("appr-001")
        assert result is False

    def test_batch_grouping_by_risk(self):
        event_manager = EventManager()
        approval_manager = ApprovalManager()
        provider = MockProvider()
        bus = MessageBus()

        mock_provider = MagicMock(spec=MockProvider)
        mock_provider.default_model = "test-model"

        loop = StreamingReActLoop(
            event_manager=event_manager,
            approval_manager=approval_manager,
            session_id="test-session",
            bus=bus,
            provider=mock_provider,
            workspace=Path("/tmp"),
            model="test-model",
            enable_security=False,
        )

        tool_calls = [
            ToolCall(id="tc-001", name="shell", arguments={"command": "ls"}),
            ToolCall(id="tc-002", name="file", arguments={"path": "/tmp/test.txt"}),
        ]

        groups = loop._group_by_risk(tool_calls)
        assert isinstance(groups, list)
