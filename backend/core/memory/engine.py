from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    entry = MemoryEntry(
        content=content,
        source="user_pinned",
        session_id=session_id,
    )
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return {"id": entry.id, "content": entry.content}


async def save_auto_summary(
    session: AsyncSession,
    summary: str,
    session_id: str,
) -> None:
    entry = MemoryEntry(
        content=summary,
        source="auto_summary",
        session_id=session_id,
    )
    session.add(entry)
    await session.commit()


async def get_active_memories(
    session: AsyncSession,
    limit: int = 10,
) -> list[dict[str, Any]]:
    stmt = (
        select(MemoryEntry)
        .where(MemoryEntry.is_active == True)  # noqa: E712
        .order_by(MemoryEntry.created_at.desc())
        .limit(limit)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {"id": m.id, "content": m.content, "source": m.source}
        for m in rows
    ]
