from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import ReminderCreate
from backend.core.workflow.internal.reminders import add_reminder, list_reminders
from backend.db.session import get_session

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.post("")
async def create_reminder(
    body: ReminderCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    remind_at = datetime.fromisoformat(body.remind_at)
    result = await add_reminder(
        session,
        message=body.message,
        remind_at=remind_at,
        is_recurring=body.is_recurring,
        recurrence_rule=body.recurrence_rule,
    )
    return result


@router.get("")
async def get_reminders(
    include_fired: bool = False,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await list_reminders(session, include_fired=include_fired)
