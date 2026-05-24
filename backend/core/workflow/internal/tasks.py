from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Task


async def add_task(
    session: AsyncSession,
    title: str,
    description: str = "",
    priority: str = "medium",
    due_date: datetime | None = None,
) -> dict[str, Any]:
    task = Task(
        title=title,
        description=description,
        priority=priority,
        due_date=due_date,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status}


async def list_tasks(
    session: AsyncSession,
    status: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(Task)
    if status:
        stmt = stmt.where(Task.status == status)
    stmt = stmt.order_by(Task.created_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "priority": t.priority,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in rows
    ]


async def update_task(
    session: AsyncSession,
    task_id: str,
    **updates: Any,
) -> dict[str, Any] | None:
    task = await session.get(Task, task_id)
    if not task:
        return None
    for key, value in updates.items():
        if hasattr(task, key):
            setattr(task, key, value)
    await session.commit()
    await session.refresh(task)
    return {"id": task.id, "title": task.title, "status": task.status}
