"""Memory プルーナーと engine のユニットテスト。"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backend.core.memory.engine import (
    deactivate_memory,
    get_active_memories,
    pin_memory,
    save_auto_summary,
)
from backend.core.memory.pruner import prune_memories, recalculate_all_scores
from backend.db.models import MemoryEntry


# ── フィクスチャ ─────────────────────────────────────────────────────────────

async def _insert_memory(
    session,
    content: str,
    source: str = "auto_summary",
    days_ago: int = 0,
    importance_score: float = 0.5,
    access_count: int = 0,
) -> MemoryEntry:
    entry = MemoryEntry(
        content=content,
        source=source,
        importance_score=importance_score,
        access_count=access_count,
        is_active=True,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)

    if days_ago > 0:
        # created_at を過去に設定
        from sqlalchemy import update
        from backend.db.models import MemoryEntry as ME
        past = datetime.now() - timedelta(days=days_ago)
        await session.execute(
            update(ME).where(ME.id == entry.id).values(created_at=past)
        )
        await session.commit()
        await session.refresh(entry)

    return entry


# ── pin_memory ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pin_memory_sets_high_score(db_session):
    result = await pin_memory(db_session, content="重要な情報")
    assert result["importance_score"] == 1.0
    assert result["content"] == "重要な情報"


# ── save_auto_summary ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_save_auto_summary_sets_initial_score(db_session):
    await save_auto_summary(db_session, summary="セッション要約", session_id="sess1")
    memories = await get_active_memories(db_session)
    assert len(memories) == 1
    # 直後のスコアは 0.7 前後（base=0.5 + recency=0.2）
    assert memories[0]["importance_score"] > 0.5


# ── get_active_memories ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_active_memories_sorted_by_score(db_session):
    await _insert_memory(db_session, "低スコア", importance_score=0.3)
    await _insert_memory(db_session, "高スコア", importance_score=0.9)
    await _insert_memory(db_session, "中スコア", importance_score=0.6)

    memories = await get_active_memories(db_session, limit=10)
    scores = [m["importance_score"] for m in memories]
    assert scores == sorted(scores, reverse=True)


@pytest.mark.asyncio
async def test_get_active_memories_record_access(db_session):
    await _insert_memory(db_session, "テスト", access_count=0)

    memories_before = await get_active_memories(db_session, record_access=False)
    assert memories_before[0]["access_count"] == 0

    await get_active_memories(db_session, record_access=True)
    memories_after = await get_active_memories(db_session, record_access=False)
    assert memories_after[0]["access_count"] == 1


@pytest.mark.asyncio
async def test_get_active_memories_excludes_inactive(db_session):
    entry = await _insert_memory(db_session, "非アクティブ")
    entry.is_active = False
    await db_session.commit()

    memories = await get_active_memories(db_session)
    assert len(memories) == 0


# ── deactivate_memory ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_deactivate_memory(db_session):
    entry = await _insert_memory(db_session, "削除対象")
    ok = await deactivate_memory(db_session, entry.id)
    assert ok is True

    memories = await get_active_memories(db_session)
    assert not any(m["id"] == entry.id for m in memories)


@pytest.mark.asyncio
async def test_deactivate_nonexistent_memory(db_session):
    ok = await deactivate_memory(db_session, "nonexistent_id")
    assert ok is False


# ── prune_memories ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_prune_archives_old_low_score(db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.core.memory.pruner.load_settings",
        lambda: {"memory": {"importance": {"auto_archive_threshold": 0.3, "auto_archive_after_days": 14}}},
    )
    # 60日前の auto_summary → score ≈ 0.2 → アーカイブ対象
    await _insert_memory(db_session, "古い要約", source="auto_summary", days_ago=60, importance_score=0.5)

    result = await prune_memories(db_session)
    assert result["archived"] == 1

    memories = await get_active_memories(db_session)
    assert len(memories) == 0


@pytest.mark.asyncio
async def test_prune_keeps_user_pinned(db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.core.memory.pruner.load_settings",
        lambda: {"memory": {"importance": {"auto_archive_threshold": 0.3, "auto_archive_after_days": 14}}},
    )
    # 365日前の user_pinned → スコアに関わらずアーカイブしない
    await _insert_memory(
        db_session, "ピン留め記憶", source="user_pinned", days_ago=365, importance_score=1.0
    )

    result = await prune_memories(db_session)
    assert result["archived"] == 0

    memories = await get_active_memories(db_session)
    assert len(memories) == 1


@pytest.mark.asyncio
async def test_prune_keeps_recent_memory(db_session, monkeypatch):
    monkeypatch.setattr(
        "backend.core.memory.pruner.load_settings",
        lambda: {"memory": {"importance": {"auto_archive_threshold": 0.3, "auto_archive_after_days": 14}}},
    )
    # 5日前 → min_days(14) 未満のためプルーン対象外
    await _insert_memory(db_session, "新しい要約", source="auto_summary", days_ago=5, importance_score=0.5)

    result = await prune_memories(db_session)
    assert result["archived"] == 0


# ── recalculate_all_scores ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_recalculate_all_scores(db_session):
    await _insert_memory(db_session, "スコア更新対象", importance_score=0.99)

    updated = await recalculate_all_scores(db_session)
    assert updated == 1

    memories = await get_active_memories(db_session)
    # 直後の作成なので recency bonus あり → 0.7 前後
    assert memories[0]["importance_score"] < 0.99
