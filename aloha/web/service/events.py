"""SSE EventManager - SSE 连接与事件发布管理"""

import asyncio
import json
from typing import Any


class EventManager:
    def __init__(self):
        self._clients: dict[str, list[asyncio.Queue[str]]] = {}

    def add_client(self, session_id: str, queue: asyncio.Queue[str]) -> None:
        self._clients.setdefault(session_id, []).append(queue)

    def remove_client(self, session_id: str, queue: asyncio.Queue[str]) -> None:
        if session_id in self._clients:
            try:
                self._clients[session_id].remove(queue)
            except ValueError:
                pass
            if not self._clients[session_id]:
                del self._clients[session_id]

    async def publish(self, session_id: str, event: str, data: Any) -> None:
        if session_id not in self._clients:
            return
        message = f"event: {event}\ndata: {json.dumps(data)}\n\n"
        coros = [queue.put(message) for queue in self._clients[session_id]]
        if coros:
            await asyncio.gather(*coros)

    def client_count(self, session_id: str) -> int:
        return len(self._clients.get(session_id, []))


_event_manager: EventManager | None = None


def get_event_manager() -> EventManager:
    global _event_manager
    if _event_manager is None:
        _event_manager = EventManager()
    return _event_manager
