from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Memo


async def add_memo(
    session: AsyncSession,
    content: str,
    title: str = "",
) -> dict[str, Any]:
    memo = Memo(title=title, content=content)
    session.add(memo)
    await session.commit()
    await session.refresh(memo)
    return {"id": memo.id, "title": memo.title, "content": memo.content[:200]}


async def list_memos(
    session: AsyncSession,
    limit: int = 20,
) -> list[dict[str, Any]]:
    stmt = select(Memo).order_by(Memo.created_at.desc()).limit(limit)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": m.id,
            "title": m.title,
            "content": m.content[:200],
            "is_pinned": m.is_pinned,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in rows
    ]


async def get_memo(session: AsyncSession, memo_id: str) -> dict[str, Any] | None:
    memo = await session.get(Memo, memo_id)
    if not memo:
        return None
    return {
        "id": memo.id,
        "title": memo.title,
        "content": memo.content,
        "is_pinned": memo.is_pinned,
    }
