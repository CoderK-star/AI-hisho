"""検索APIのテスト。"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.session import init_db
from backend.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_search_disabled_returns_503(monkeypatch):
    """RAG が無効な設定では 503 を返すことを確認。"""
    # settings.yaml の rag.enabled に依存しないよう強制的に無効化
    monkeypatch.setattr(
        "backend.rag.retriever.RAGEngine.get_instance",
        lambda: None,
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/search?q=テスト")
        assert resp.status_code == 503
        assert "無効" in resp.json()["detail"]
