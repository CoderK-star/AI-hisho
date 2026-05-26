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


async def _reindex_rag() -> None:
    from backend.rag.engine import RAGEngine
    from backend.rag.indexer import index_all

    if RAGEngine.get_instance() is None:
        return
    async with async_session() as session:
        count = await index_all(session)
    logger.info("RAG: 再インデックス完了 (%d件)", count)


async def _maintain_memories() -> None:
    """記憶エントリの夜間メンテナンス: スコア再計算 → 自動アーカイブ。"""
    from backend.core.memory.pruner import prune_memories, recalculate_all_scores

    async with async_session() as session:
        updated = await recalculate_all_scores(session)
        result = await prune_memories(session)

    logger.info(
        "Memory maintenance: scores_updated=%d archived=%d checked=%d",
        updated,
        result["archived"],
        result["checked"],
    )


def check_reminders() -> None:
    _run_async(_check_reminders())


def run_briefing() -> None:
    _run_async(_briefing())


def reindex_rag() -> None:
    _run_async(_reindex_rag())


def maintain_memories() -> None:
    _run_async(_maintain_memories())
