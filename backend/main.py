from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from backend.api.routes import calendar, chat, logs, memos, reminders, search, tasks
from backend.config.loader import load_settings
from backend.db.session import init_db
from backend.scheduler.jobs import check_reminders, reindex_rag, run_briefing

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    await init_db()
    logger.info("Database initialized")

    settings = load_settings()
    sched_cfg = settings.get("scheduler", {}).get("briefing", {})
    tz = sched_cfg.get("timezone", "Asia/Tokyo")

    if sched_cfg.get("enabled", False):
        morning = sched_cfg.get("morning", "08:00")
        evening = sched_cfg.get("evening", "21:00")

        mh, mm = morning.split(":")
        scheduler.add_job(run_briefing, "cron", hour=int(mh), minute=int(mm),
                          timezone=tz, id="morning_briefing")

        eh, em = evening.split(":")
        scheduler.add_job(run_briefing, "cron", hour=int(eh), minute=int(em),
                          timezone=tz, id="evening_briefing")

    scheduler.add_job(check_reminders, "interval", minutes=1, id="reminder_check")

    # RAG 初期化 & 定期再インデックス
    from backend.rag.engine import RAGEngine
    rag_engine = RAGEngine.get_instance()
    if rag_engine is not None:
        try:
            await rag_engine.initialize()
            from backend.db.session import async_session
            from backend.rag.indexer import index_all
            async with async_session() as session:
                count = await index_all(session)
            logger.info("RAG: 起動時インデックス完了 (%d件)", count)
        except Exception:
            logger.exception("RAG 初期化に失敗しました")

        scheduler.add_job(reindex_rag, "interval", hours=1, id="rag_reindex")

    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="AI秘書 API",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(memos.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(logs.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
