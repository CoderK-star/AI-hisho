"""操作ログAPIのテスト。"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from backend.db.session import init_db
from backend.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_get_logs_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.api.routes.logs._LOG_FILE", tmp_path / "ops.jsonl")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/logs")
        assert resp.status_code == 200
        assert resp.json()["entries"] == []


@pytest.mark.asyncio
async def test_get_logs_with_data(tmp_path, monkeypatch):
    log_file = tmp_path / "ops.jsonl"
    entries = [
        {"timestamp": "2026-05-24T10:00:00+09:00", "intent": "task_add",
         "input_summary": "テスト", "llm_route": "local", "result": "success",
         "tools_called": [], "external_apis_called": [], "cloud_escalated": False,
         "requires_confirmation": False, "session_id": "abc"},
        {"timestamp": "2026-05-24T11:00:00+09:00", "intent": "chat",
         "input_summary": "こんにちは", "llm_route": "local", "result": "success",
         "tools_called": [], "external_apis_called": [], "cloud_escalated": False,
         "requires_confirmation": False, "session_id": "def"},
    ]
    log_file.write_text("\n".join(json.dumps(e) for e in entries))
    monkeypatch.setattr("backend.api.routes.logs._LOG_FILE", log_file)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/logs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2

        resp = await client.get("/api/logs?intent=task_add")
        assert resp.json()["count"] == 1
        assert resp.json()["entries"][0]["intent"] == "task_add"


@pytest.mark.asyncio
async def test_log_viewer_html(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.api.routes.logs._LOG_FILE", tmp_path / "ops.jsonl")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/logs/view")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "操作ログ" in resp.text
