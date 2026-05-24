from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Reminder


async def add_reminder(
    session: AsyncSession,
    message: str,
    remind_at: datetime,
    is_recurring: bool = False,
    recurrence_rule: str | None = None,
) -> dict[str, Any]:
    reminder = Reminder(
        message=message,
        remind_at=remind_at,
        is_recurring=is_recurring,
        recurrence_rule=recurrence_rule,
    )
    session.add(reminder)
    await session.commit()
    await session.refresh(reminder)
    return {
        "id": reminder.id,
        "message": reminder.message,
        "remind_at": reminder.remind_at.isoformat(),
    }


async def list_reminders(
    session: AsyncSession,
    include_fired: bool = False,
) -> list[dict[str, Any]]:
    stmt = select(Reminder)
    if not include_fired:
        stmt = stmt.where(Reminder.is_fired == False)  # noqa: E712
    stmt = stmt.order_by(Reminder.remind_at)
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": r.id,
            "message": r.message,
            "remind_at": r.remind_at.isoformat(),
            "is_fired": r.is_fired,
        }
        for r in rows
    ]


async def fire_reminder(session: AsyncSession, reminder_id: str) -> bool:
    reminder = await session.get(Reminder, reminder_id)
    if not reminder:
        return False
    reminder.is_fired = True
    await session.commit()
    return True


async def get_due_reminders(session: AsyncSession) -> list[dict[str, Any]]:
    now = datetime.now()
    stmt = (
        select(Reminder)
        .where(Reminder.is_fired == False, Reminder.remind_at <= now)  # noqa: E712
        .order_by(Reminder.remind_at)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {"id": r.id, "message": r.message, "remind_at": r.remind_at.isoformat()}
        for r in rows
    ]
