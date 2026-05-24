from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from backend.api.routes import chat, memos, reminders, tasks
from backend.config.loader import load_settings
from backend.db.session import init_db
from backend.scheduler.jobs import check_reminders, run_briefing

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

    if sched_cfg.get("enabled", False):
        morning = sched_cfg.get("morning", "08:00")
        evening = sched_cfg.get("evening", "21:00")
        tz = sched_cfg.get("timezone", "Asia/Tokyo")

        mh, mm = morning.split(":")
        scheduler.add_job(run_briefing, "cron", hour=int(mh), minute=int(mm), timezone=tz,
                          id="morning_briefing")

        eh, em = evening.split(":")
        scheduler.add_job(run_briefing, "cron", hour=int(eh), minute=int(em), timezone=tz,
                          id="evening_briefing")

    scheduler.add_job(check_reminders, "interval", minutes=1, id="reminder_check")
    scheduler.start()
    logger.info("Scheduler started")

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="AI秘書 API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(memos.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
