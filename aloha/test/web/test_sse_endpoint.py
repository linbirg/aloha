"""SSE 端点测试"""

import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from aloha.web.service.api import app
from aloha.web.service.events import get_event_manager


class TestSSEEndpoint:
    @pytest.mark.asyncio
    async def test_approval_submit_endpoint(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/approvals/test-001",
                json={"decision": "approved", "reason": None},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_approval_submit_rejected(self):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/api/approvals/test-002",
                json={"decision": "rejected", "reason": "not needed"},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
