from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Task

# DB stores "todo"/"in_progress"; API surface uses "pending" for both
_DB_TO_API_STATUS = {"todo": "pending", "in_progress": "pending"}
_API_TO_DB_STATUS = {"pending": "todo"}


def _serialize_task(t: Task) -> dict[str, Any]:
    return {
        "id": t.id,
        "title": t.title,
        "description": t.description or "",
        "status": _DB_TO_API_STATUS.get(t.status, t.status),
        "priority": t.priority,
        "due_date": t.due_date.isoformat() if t.due_date else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


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
    return _serialize_task(task)


async def list_tasks(
    session: AsyncSession,
    status: str | None = None,
) -> list[dict[str, Any]]:
    stmt = select(Task)
    if status:
        db_status = _API_TO_DB_STATUS.get(status, status)
        if db_status == "todo":
            # "pending" covers both todo and in_progress
            from sqlalchemy import or_
            stmt = stmt.where(or_(Task.status == "todo", Task.status == "in_progress"))
        else:
            stmt = stmt.where(Task.status == db_status)
    stmt = stmt.order_by(Task.created_at.desc())
    rows = (await session.execute(stmt)).scalars().all()
    return [_serialize_task(t) for t in rows]


async def update_task(
    session: AsyncSession,
    task_id: str,
    **updates: Any,
) -> dict[str, Any] | None:
    task = await session.get(Task, task_id)
    if not task:
        return None
    for key, value in updates.items():
        if key == "status":
            value = _API_TO_DB_STATUS.get(value, value)
        if hasattr(task, key):
            setattr(task, key, value)
    await session.commit()
    await session.refresh(task)
    return _serialize_task(task)


async def delete_task(session: AsyncSession, task_id: str) -> bool:
    task = await session.get(Task, task_id)
    if not task:
        return False
    await session.delete(task)
    await session.commit()
    return True
