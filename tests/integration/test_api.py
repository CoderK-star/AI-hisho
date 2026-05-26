from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.session import init_db
from backend.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.fixture(autouse=True)
def disable_rag(monkeypatch):
    """統合テストでは RAG エンジンを無効化する（モデルDLが不要）。"""
    monkeypatch.setattr("backend.rag.engine.RAGEngine.get_instance", lambda: None)


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_create_and_list_tasks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/tasks", json={"title": "統合テスト"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "統合テスト"

        resp = await client.get("/api/tasks")
        assert resp.status_code == 200
        tasks = resp.json()
        assert any(t["title"] == "統合テスト" for t in tasks)


@pytest.mark.asyncio
async def test_chat_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/chat", json={"message": "タスクの一覧を見せて"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent"] == "task_list"
        assert "session_id" in data


@pytest.mark.asyncio
async def test_create_memo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/memos", json={"title": "テストメモ", "content": "内容テスト"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "テストメモ"


@pytest.mark.asyncio
async def test_create_reminder():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/reminders",
            json={"message": "テスト通知", "remind_at": "2026-12-31T09:00:00"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "テスト通知"
