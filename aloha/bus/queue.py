"""Message Bus - 消息队列实现"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


@dataclass
class Envelope:
    """消息信封"""
    id: str
    sender: str
    recipient: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """消息总线

    简单的异步消息队列实现，用于连接各个组件。
    """

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._handlers: dict[str, Callable] = {}

    def create_queue(self, name: str) -> asyncio.Queue:
        """创建队列"""
        if name not in self._queues:
            self._queues[name] = asyncio.Queue()
        return self._queues[name]

    def get_queue(self, name: str) -> asyncio.Queue | None:
        """获取队列"""
        return self._queues.get(name)

    async def send(self, recipient: str, envelope: Envelope) -> None:
        """发送消息"""
        queue = self._queues.get(recipient)
        if queue:
            await queue.put(envelope)

    async def receive(self, queue_name: str, timeout: float | None = None) -> Envelope | None:
        """接收消息"""
        queue = self._queues.get(queue_name)
        if not queue:
            return None
        try:
            if timeout:
                return await asyncio.wait_for(queue.get(), timeout=timeout)
            return await queue.get()
        except asyncio.TimeoutError:
            return None

    def register_handler(self, name: str, handler: Callable) -> None:
        """注册消息处理器"""
        self._handlers[name] = handler

    def get_handler(self, name: str) -> Callable | None:
        """获取消息处理器"""
        return self._handlers.get(name)

    def clear_queue(self, name: str) -> int:
        """清空队列"""
        queue = self._queues.get(name)
        if not queue:
            return 0
        count = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                count += 1
            except asyncio.QueueEmpty:
                break
        return count

    def queue_size(self, name: str) -> int:
        """获取队列大小"""
        queue = self._queues.get(name)
        return queue.qsize() if queue else 0
