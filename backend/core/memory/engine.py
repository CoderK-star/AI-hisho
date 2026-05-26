from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.memory.scorer import compute_importance_score, initial_score
from backend.db.models import ConversationLog, MemoryEntry


async def save_conversation(
    session: AsyncSession,
    session_id: str,
    role: str,
    content: str,
) -> None:
    log = ConversationLog(session_id=session_id, role=role, content=content)
    session.add(log)
    await session.commit()


async def pin_memory(
    session: AsyncSession,
    content: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    score = initial_score("user_pinned")
    entry = MemoryEntry(
        content=content,
        source="user_pinned",
        session_id=session_id,
        importance_score=score,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return {
        "id": entry.id,
        "content": entry.content,
        "importance_score": entry.importance_score,
    }


async def save_auto_summary(
    session: AsyncSession,
    summary: str,
    session_id: str,
) -> None:
    score = initial_score("auto_summary")
    entry = MemoryEntry(
        content=summary,
        source="auto_summary",
        session_id=session_id,
        importance_score=score,
    )
    session.add(entry)
    await session.commit()


async def get_active_memories(
    session: AsyncSession,
    limit: int = 10,
    *,
    record_access: bool = False,
) -> list[dict[str, Any]]:
    """重要度スコアの高い順にアクティブな記憶エントリを返す。

    Args:
        limit: 取得件数上限
        record_access: True にするとアクセス回数を加算し、スコアを再計算する。
                       ユーザが明示的に記憶一覧を閲覧した場合のみ True にすること。
    """
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.is_active == True)  # noqa: E712
        .order_by(MemoryEntry.importance_score.desc(), MemoryEntry.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()

    if record_access and rows:
        now = datetime.now()
        for entry in rows:
            entry.access_count += 1
            entry.last_accessed_at = now
            entry.importance_score = compute_importance_score(
                source=entry.source,
                created_at=entry.created_at,
                access_count=entry.access_count,
                last_accessed_at=entry.last_accessed_at,
                now=now,
            )
        await session.commit()

    return [
        {
            "id": m.id,
            "content": m.content,
            "source": m.source,
            "importance_score": m.importance_score,
            "access_count": m.access_count,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in rows
    ]


async def deactivate_memory(session: AsyncSession, memory_id: str) -> bool:
    """指定した記憶エントリを非アクティブ化（論理削除）する。"""
    entry = await session.get(MemoryEntry, memory_id)
    if not entry:
        return False
    entry.is_active = False
    await session.commit()
    return True
