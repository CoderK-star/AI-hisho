from datetime import datetime, timedelta

import pytest

from backend.core.workflow.internal.reminders import (
    add_reminder,
    fire_reminder,
    get_due_reminders,
    list_reminders,
)


@pytest.mark.asyncio
async def test_add_and_list(db_session):
    remind_at = datetime.now() + timedelta(hours=1)
    result = await add_reminder(db_session, message="テスト通知", remind_at=remind_at)
    assert result["message"] == "テスト通知"

    reminders = await list_reminders(db_session)
    assert len(reminders) == 1


@pytest.mark.asyncio
async def test_fire_reminder(db_session):
    remind_at = datetime.now() + timedelta(hours=1)
    result = await add_reminder(db_session, message="発火テスト", remind_at=remind_at)
    assert await fire_reminder(db_session, result["id"])

    active = await list_reminders(db_session, include_fired=False)
    assert len(active) == 0


@pytest.mark.asyncio
async def test_due_reminders(db_session):
    past = datetime.now() - timedelta(minutes=5)
    future = datetime.now() + timedelta(hours=1)
    await add_reminder(db_session, message="過去", remind_at=past)
    await add_reminder(db_session, message="未来", remind_at=future)

    due = await get_due_reminders(db_session)
    assert len(due) == 1
    assert due[0]["message"] == "過去"
