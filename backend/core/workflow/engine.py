from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.intent.rules import IntentType
from backend.core.workflow.internal import memos, reminders, tasks

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    success: bool
    data: Any = None
    tools_called: list[str] | None = None
    error: str | None = None
    needs_llm: bool = False


async def execute(
    intent: IntentType,
    session: AsyncSession,
    user_input: str,
    extracted: dict[str, Any] | None = None,
) -> WorkflowResult:
    extracted = extracted or {}

    if intent == IntentType.TASK_ADD:
        title = extracted.get("title", user_input)
        result = await tasks.add_task(
            session,
            title=title,
            priority=extracted.get("priority", "medium"),
            due_date=extracted.get("due_date"),
        )
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.tasks.add"]
        )

    if intent == IntentType.TASK_LIST:
        result = await tasks.list_tasks(session, status=extracted.get("status"))
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.tasks.list"]
        )

    if intent == IntentType.TASK_UPDATE:
        task_id = extracted.get("task_id", "")
        updates = {k: v for k, v in extracted.items() if k != "task_id"}
        result = await tasks.update_task(session, task_id, **updates)
        if result is None:
            return WorkflowResult(success=False, error="タスクが見つかりません")
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.tasks.update"]
        )

    if intent == IntentType.REMINDER_ADD:
        remind_at = extracted.get("remind_at")
        if not remind_at:
            return WorkflowResult(
                success=False, error="リマインダーの日時が指定されていません", needs_llm=True
            )
        if isinstance(remind_at, str):
            remind_at = datetime.fromisoformat(remind_at)
        result = await reminders.add_reminder(
            session,
            message=extracted.get("message", user_input),
            remind_at=remind_at,
        )
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.reminders.add"]
        )

    if intent == IntentType.REMINDER_LIST:
        result = await reminders.list_reminders(session)
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.reminders.list"]
        )

    if intent == IntentType.MEMO_ADD:
        result = await memos.add_memo(
            session,
            content=extracted.get("content", user_input),
            title=extracted.get("title", ""),
        )
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.memos.add"]
        )

    if intent == IntentType.MEMO_LIST:
        result = await memos.list_memos(session)
        return WorkflowResult(
            success=True, data=result, tools_called=["internal.memos.list"]
        )

    if intent == IntentType.KNOWLEDGE_SEARCH:
        from backend.rag.retriever import retrieve
        results = await retrieve(user_input)
        return WorkflowResult(
            success=True,
            data={"query": user_input, "results": results},
            tools_called=["rag.search"],
            needs_llm=True,
        )

    if intent == IntentType.SCHEDULE_CHECK_CALENDAR:
        from backend.core.workflow.adapters.calendar import get_calendar_adapter
        adapter = get_calendar_adapter()
        if adapter is None:
            return WorkflowResult(
                success=False,
                error="カレンダー連携が設定されていません。config/settings.yaml で calendar.enabled: true にしてください。",
                needs_llm=False,
            )
        events = await adapter.get_upcoming_events(days=7)
        return WorkflowResult(
            success=True,
            data={"events": events},
            tools_called=["adapters.calendar.get_events"],
            needs_llm=True,
        )

    return WorkflowResult(success=True, needs_llm=True)
