from __future__ import annotations

import asyncio
import logging

from backend.config.loader import load_settings
from backend.core.workflow.internal.notifications import send_notification
from backend.core.workflow.internal.reminders import fire_reminder, get_due_reminders
from backend.core.workflow.internal.tasks import list_tasks
from backend.db.session import async_session

logger = logging.getLogger(__name__)


def _run_async(coro):  # type: ignore[no-untyped-def]
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        asyncio.run(coro)


async def _check_reminders() -> None:
    async with async_session() as session:
        due = await get_due_reminders(session)
        settings = load_settings()
        method = settings.get("notification", {}).get("method", "terminal")
        for reminder in due:
            await send_notification(
                f"リマインダー: {reminder['message']}", method=method
            )
            await fire_reminder(session, reminder["id"])


async def _briefing() -> None:
    async with async_session() as session:
        all_tasks = await list_tasks(session)
        settings = load_settings()
        method = settings.get("notification", {}).get("method", "terminal")

        todo = [t for t in all_tasks if t["status"] in ("todo", "in_progress")]
        if not todo:
            await send_notification("現在のタスクはありません。", method=method)
            return

        lines = [f"未完了タスク: {len(todo)}件"]
        for t in todo[:5]:
            lines.append(f"  - [{t['priority']}] {t['title']}")
        if len(todo) > 5:
            lines.append(f"  ... 他 {len(todo) - 5}件")

        await send_notification("\n".join(lines), method=method)


def check_reminders() -> None:
    _run_async(_check_reminders())


def run_briefing() -> None:
    _run_async(_briefing())
