from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import TaskCreate, TaskUpdate
from backend.core.workflow.internal.tasks import add_task, list_tasks, update_task
from backend.db.session import get_session

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("")
async def create_task(
    body: TaskCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    due = None
    if body.due_date:
        due = datetime.fromisoformat(body.due_date)
    result = await add_task(
        session,
        title=body.title,
        description=body.description,
        priority=body.priority,
        due_date=due,
    )
    return result


@router.get("")
async def get_tasks(
    status: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await list_tasks(session, status=status)


@router.patch("/{task_id}")
async def patch_task(
    task_id: str,
    body: TaskUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    if "due_date" in updates and updates["due_date"]:
        updates["due_date"] = datetime.fromisoformat(updates["due_date"])
    result = await update_task(session, task_id, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return result
