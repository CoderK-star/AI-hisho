"""検索APIのテスト。RAG無効時に503を返すことを確認。"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.session import init_db
from backend.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_search_disabled_returns_503():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/search?q=テスト")
        # RAG が無効な環境では 503
        assert resp.status_code == 503
        assert "無効" in resp.json()["detail"]
