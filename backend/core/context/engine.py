from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.intent.rules import IntentType
from backend.db.models import ConversationLog, Memo, Reminder, Task


@dataclass
class ContextData:
    current_time: str = ""
    recent_conversations: list[dict[str, str]] = field(default_factory=list)
    tasks: list[dict[str, Any]] = field(default_factory=list)
    reminders: list[dict[str, Any]] = field(default_factory=list)
    memos: list[dict[str, Any]] = field(default_factory=list)


_INTENT_LOADERS: dict[IntentType, list[str]] = {
    IntentType.CHAT: ["time", "conversations"],
    IntentType.TASK_ADD: ["time", "tasks"],
    IntentType.TASK_LIST: ["time", "tasks"],
    IntentType.TASK_UPDATE: ["time", "tasks"],
    IntentType.REMINDER_ADD: ["time", "reminders"],
    IntentType.REMINDER_LIST: ["time", "reminders"],
    IntentType.MEMO_ADD: ["time"],
    IntentType.MEMO_LIST: ["time", "memos"],
    IntentType.SCHEDULE_CHECK: ["time", "tasks", "reminders"],
    IntentType.BRIEFING: ["time", "tasks", "reminders", "memos"],
    IntentType.MEMORY_PIN: ["time"],
    IntentType.KNOWLEDGE_SEARCH: ["time", "conversations"],
    IntentType.SCHEDULE_CHECK_CALENDAR: ["time"],
    IntentType.HELP: ["time"],
}


async def load_context(
    intent: IntentType, session: AsyncSession, session_id: str | None = None
) -> ContextData:
    loaders = _INTENT_LOADERS.get(intent, ["time"])
    ctx = ContextData()

    if "time" in loaders:
        ctx.current_time = datetime.now().isoformat()

    if "conversations" in loaders and session_id:
        stmt = (
            select(ConversationLog)
            .where(ConversationLog.session_id == session_id)
            .order_by(ConversationLog.created_at.desc())
            .limit(20)
        )
        rows = (await session.execute(stmt)).scalars().all()
        ctx.recent_conversations = [
            {"role": r.role, "content": r.content} for r in reversed(rows)
        ]

    if "tasks" in loaders:
        stmt = select(Task).where(Task.status.in_(["todo", "in_progress"]))
        rows = (await session.execute(stmt)).scalars().all()
        ctx.tasks = [
            {"id": t.id, "title": t.title, "status": t.status,
             "priority": t.priority, "due_date": t.due_date.isoformat() if t.due_date else None}
            for t in rows
        ]

    if "reminders" in loaders:
        stmt = select(Reminder).where(Reminder.is_fired == False)  # noqa: E712
        rows = (await session.execute(stmt)).scalars().all()
        ctx.reminders = [
            {"id": r.id, "message": r.message, "remind_at": r.remind_at.isoformat()}
            for r in rows
        ]

    if "memos" in loaders:
        stmt = select(Memo).order_by(Memo.created_at.desc()).limit(10)
        rows = (await session.execute(stmt)).scalars().all()
        ctx.memos = [
            {"id": m.id, "title": m.title, "content": m.content[:200]}
            for m in rows
        ]

    return ctx
