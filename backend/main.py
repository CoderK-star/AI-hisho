from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

from backend.api.routes import calendar, chat, logs, memories, memos, reminders, search, tasks
from backend.api.routes import voice as voice_routes
from backend.config.loader import load_settings
from backend.db.session import init_db, migrate_db
from backend.scheduler.jobs import check_reminders, maintain_memories, reindex_rag, run_briefing

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(_PROJECT_ROOT / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_main_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[no-untyped-def]
    global _main_loop
    _main_loop = asyncio.get_event_loop()

    await init_db()
    await migrate_db()
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

    # Memory 夜間メンテナンス (毎日 03:00)
    settings = load_settings()
    mem_tz = settings.get("scheduler", {}).get("briefing", {}).get("timezone", "Asia/Tokyo")
    scheduler.add_job(
        maintain_memories, "cron", hour=3, minute=0, timezone=mem_tz, id="memory_maintenance"
    )

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

    # Phase 4 — wake word daemon (optional; enabled via voice.wakeword.enabled in settings)
    from backend.stt_tts.wakeword import start_daemon, stop_daemon

    def _on_wake(audio_bytes: bytes) -> None:
        if _main_loop and _main_loop.is_running():
            asyncio.run_coroutine_threadsafe(
                _handle_wake_audio(audio_bytes), _main_loop
            )

    start_daemon(_on_wake)

    yield

    stop_daemon()
    scheduler.shutdown()
    logger.info("Scheduler stopped")


async def _handle_wake_audio(audio_bytes: bytes) -> None:
    """Process audio triggered by the wake word daemon."""
    from backend.db.session import async_session
    from backend.stt_tts.stt import STTError, get_stt_client
    from backend.stt_tts.tts import TTSError, get_tts_client
    from backend.api.routes.voice import _run_chat

    try:
        message = await get_stt_client().async_transcribe_bytes(audio_bytes)
        logger.info("Wake word utterance: %r", message)
    except STTError:
        logger.exception("STT failed for wake word utterance")
        return

    async with async_session() as session:
        reply, _intent, _sid, _tools = await _run_chat(
            message, None, session, "[wakeword] "
        )

    logger.info("Wake word reply: %r", reply)
    try:
        await get_tts_client().play(reply)
    except TTSError:
        logger.exception("TTS playback failed for wake word reply")


app = FastAPI(
    title="AI秘書 API",
    version="0.3.0",
    lifespan=lifespan,
)

app.include_router(chat.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(reminders.router, prefix="/api")
app.include_router(memos.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(memories.router, prefix="/api")
app.include_router(voice_routes.router, prefix="/api")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
