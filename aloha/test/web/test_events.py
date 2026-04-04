"""EventManager 测试"""

import pytest
import asyncio
from aloha.web.service.events import EventManager


class TestEventManager:
    def test_add_remove_client(self):
        manager = EventManager()
        queue = asyncio.Queue()

        manager.add_client("session-1", queue)
        assert manager.client_count("session-1") == 1

        manager.remove_client("session-1", queue)
        assert manager.client_count("session-1") == 0

    @pytest.mark.asyncio
    async def test_publish_to_single_client(self):
        manager = EventManager()
        queue = asyncio.Queue()
        manager.add_client("session-1", queue)

        await manager.publish("session-1", "test_event", {"key": "value"})

        assert queue.qsize() == 1
        msg = await queue.get()
        assert "event: test_event" in msg
        assert '"key": "value"' in msg

    @pytest.mark.asyncio
    async def test_publish_to_multiple_clients_same_session(self):
        manager = EventManager()
        queue1 = asyncio.Queue()
        queue2 = asyncio.Queue()
        manager.add_client("session-1", queue1)
        manager.add_client("session-1", queue2)

        await manager.publish("session-1", "test_event", {"key": "value"})

        assert queue1.qsize() == 1
        assert queue2.qsize() == 1

    @pytest.mark.asyncio
    async def test_publish_no_client(self):
        manager = EventManager()
        queue = asyncio.Queue()

        manager.add_client("session-1", queue)
        await manager.publish("session-2", "test_event", {"key": "value"})

        assert queue.qsize() == 0

    def test_client_count(self):
        manager = EventManager()
        queue1 = asyncio.Queue()
        queue2 = asyncio.Queue()

        assert manager.client_count("session-1") == 0

        manager.add_client("session-1", queue1)
        assert manager.client_count("session-1") == 1

        manager.add_client("session-1", queue2)
        assert manager.client_count("session-1") == 2

        manager.remove_client("session-1", queue1)
        assert manager.client_count("session-1") == 1

        manager.remove_client("session-1", queue2)
        assert manager.client_count("session-1") == 0
