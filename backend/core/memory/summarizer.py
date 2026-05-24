from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import ConversationLog


async def summarize_session(session: AsyncSession, session_id: str) -> str:
    stmt = (
        select(ConversationLog)
        .where(ConversationLog.session_id == session_id)
        .order_by(ConversationLog.created_at)
    )
    rows = (await session.execute(stmt)).scalars().all()

    if not rows:
        return ""

    user_messages = [r.content for r in rows if r.role == "user"]
    topics = ", ".join(msg[:50] for msg in user_messages[:5])
    return f"セッション {session_id}: ユーザの話題 — {topics}"
