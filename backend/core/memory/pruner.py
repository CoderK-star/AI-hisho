"""記憶エントリの自動アーカイブと重要度スコアの一括再計算。

- user_pinned はアーカイブしない（永続保護）
- auto_summary は設定値より古く、スコアが閾値未満になったら非アクティブ化
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.loader import load_settings
from backend.core.memory.scorer import compute_importance_score
from backend.db.models import MemoryEntry

logger = logging.getLogger(__name__)


def _get_memory_config() -> dict:
    return load_settings().get("memory", {}).get("importance", {})


async def prune_memories(session: AsyncSession) -> dict[str, int]:
    """重要度スコアが閾値未満かつ最小経過日数を超えた auto_summary をアーカイブする。

    Returns:
        {"archived": アーカイブ数, "checked": 対象チェック数}
    """
    cfg = _get_memory_config()
    threshold = float(cfg.get("auto_archive_threshold", 0.3))
    min_days = int(cfg.get("auto_archive_after_days", 14))

    now = datetime.now()
    cutoff = now - timedelta(days=min_days)

    stmt = (
        select(MemoryEntry)
        .where(
            MemoryEntry.is_active == True,   # noqa: E712
            MemoryEntry.source == "auto_summary",
            MemoryEntry.created_at <= cutoff,
        )
    )
    entries = (await session.execute(stmt)).scalars().all()

    archived = 0
    for entry in entries:
        score = compute_importance_score(
            source=entry.source,
            created_at=entry.created_at,
            access_count=entry.access_count,
            last_accessed_at=entry.last_accessed_at,
            now=now,
        )
        entry.importance_score = score
        if score < threshold:
            entry.is_active = False
            archived += 1
            logger.info(
                "Memory archived: id=%s score=%.4f days=%d",
                entry.id,
                score,
                (now - entry.created_at).days,
            )

    await session.commit()
    logger.info("prune_memories: checked=%d archived=%d", len(entries), archived)
    return {"archived": archived, "checked": len(entries)}


async def recalculate_all_scores(session: AsyncSession) -> int:
    """全アクティブ記憶エントリのスコアを現在時刻で再計算する（定期実行用）。

    Returns:
        更新したエントリ数
    """
    now = datetime.now()
    stmt = select(MemoryEntry).where(MemoryEntry.is_active == True)  # noqa: E712
    entries = (await session.execute(stmt)).scalars().all()

    for entry in entries:
        entry.importance_score = compute_importance_score(
            source=entry.source,
            created_at=entry.created_at,
            access_count=entry.access_count,
            last_accessed_at=entry.last_accessed_at,
            now=now,
        )

    await session.commit()
    logger.info("recalculate_all_scores: updated %d entries", len(entries))
    return len(entries)
