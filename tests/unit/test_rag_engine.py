"""RAGエンジンのテスト。

スキップ条件:
  - qdrant-client[fastembed] が未インストール
  - HuggingFace へのネットワーク接続不可（モデルダウンロードが必要なため）
"""
from __future__ import annotations

import pytest

try:
    from qdrant_client import QdrantClient  # noqa: F401

    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False

pytestmark = pytest.mark.skipif(not _QDRANT_AVAILABLE, reason="qdrant-client not installed")


def _require_network(func):
    """ネットワーク接続が必要なテスト用デコレータ。接続失敗時はスキップする。"""
    import functools

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            msg = str(e).lower()
            if any(k in msg for k in ("ssl", "connect", "certificate", "network", "timeout")):
                pytest.skip(f"Network/SSL unavailable: {e}")
            raise

    return wrapper


@pytest.fixture
def rag_engine(tmp_path, monkeypatch):
    from backend.rag.engine import RAGEngine

    RAGEngine.reset()
    cfg = {
        "enabled": True,
        "mode": "local",
        "local_path": str(tmp_path / "rag"),
        "collection": "test_col",
        "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "top_k": 3,
    }
    engine = RAGEngine(cfg)
    return engine


@pytest.mark.asyncio
@_require_network
async def test_initialize(rag_engine):
    await rag_engine.initialize()
    assert rag_engine._initialized


@pytest.mark.asyncio
@_require_network
async def test_index_and_search(rag_engine):
    await rag_engine.initialize()

    await rag_engine.index_document(
        doc_type="memo",
        doc_id="memo-001",
        text="プロジェクトXのキックオフミーティングは来週月曜日",
        metadata={"title": "プロジェクトX"},
    )
    await rag_engine.index_document(
        doc_type="memo",
        doc_id="memo-002",
        text="買い物リスト: 牛乳、卵、パン",
        metadata={"title": "買い物"},
    )

    results = await rag_engine.search("プロジェクトX ミーティング")
    assert len(results) >= 1
    assert any("プロジェクトX" in r["text"] for r in results)


@pytest.mark.asyncio
@_require_network
async def test_delete_document(rag_engine):
    await rag_engine.initialize()
    await rag_engine.index_document("memo", "del-001", "削除するメモ")
    await rag_engine.delete_document("memo", "del-001")
    results = await rag_engine.search("削除するメモ")
    assert not any(r.get("doc_id") == "del-001" for r in results)


@pytest.mark.asyncio
async def test_get_instance_disabled(monkeypatch):
    from backend.rag.engine import RAGEngine

    RAGEngine.reset()
    monkeypatch.setattr(
        "backend.rag.engine.load_settings",
        lambda: {"rag": {"enabled": False}},
    )
    assert RAGEngine.get_instance() is None
    RAGEngine.reset()
