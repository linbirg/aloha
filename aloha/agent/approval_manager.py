"""ApprovalManager - 审批队列 + 幂等性 + 超时管理"""

import asyncio
import time
from aloha.agent.events import ApprovalRequest, ApprovalDecision


class ApprovalManager:
    def __init__(self, default_timeout: float = 300):
        self._queue: asyncio.Queue[ApprovalRequest] = asyncio.Queue()
        self._futures: dict[str, asyncio.Future[bool]] = {}
        self._resolved: dict[str, ApprovalDecision] = {}
        self.default_timeout = default_timeout
        self._timeout_tasks: set[asyncio.Task] = set()

    async def enqueue(self, request: ApprovalRequest) -> bool:
        existing = self._resolved.get(request.id)
        if existing:
            return existing.decision == "approved"

        if request.id in self._futures:
            return False

        future: asyncio.Future[bool] = asyncio.Future()
        self._futures[request.id] = future
        await self._queue.put(request)
        self._start_timeout_task(request.id, request.timeout)
        return True

    async def wait(self, approval_id: str) -> bool:
        resolved = self._resolved.get(approval_id)
        if resolved:
            return resolved.decision == "approved"

        future = self._futures.get(approval_id)
        if not future:
            return False

        try:
            return await asyncio.wait_for(future, timeout=self.default_timeout)
        except asyncio.TimeoutError:
            self._futures.pop(approval_id, None)
            return False

    def resolve(
        self, approval_id: str, decision: str, reason: str | None = None
    ) -> bool:
        if approval_id in self._resolved:
            return False

        self._resolved[approval_id] = ApprovalDecision(
            approval_id=approval_id,
            decision=decision,
            reason=reason,
            approved_at=time.time(),
        )

        future = self._futures.pop(approval_id, None)
        if future and not future.done():
            future.set_result(decision == "approved")
            return True
        return False

    def _start_timeout_task(self, approval_id: str, timeout: float) -> None:
        async def timeout_task():
            await asyncio.sleep(timeout)
            self._record_timeout(approval_id)

        task = asyncio.create_task(timeout_task())
        self._timeout_tasks.add(task)
        task.add_done_callback(self._timeout_tasks.discard)

    def _record_timeout(self, approval_id: str) -> None:
        if approval_id in self._resolved:
            return
        self._resolved[approval_id] = ApprovalDecision(
            approval_id=approval_id,
            decision="rejected",
            reason="timeout",
            approved_at=time.time(),
        )
        future = self._futures.pop(approval_id, None)
        if future and not future.done():
            future.set_result(False)

    async def get_queue_status(self) -> tuple[int, ApprovalRequest | None]:
        if self._queue.empty():
            return 0, None
        return self._queue.qsize(), None

    def is_resolved(self, approval_id: str) -> bool:
        return approval_id in self._resolved

    def get_decision(self, approval_id: str) -> ApprovalDecision | None:
        return self._resolved.get(approval_id)
