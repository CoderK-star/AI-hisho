from __future__ import annotations

import logging
import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_DB = f"sqlite+aiosqlite:///{_PROJECT_ROOT / 'data' / 'db' / 'assistant.db'}"

_db_url = os.environ.get("DATABASE_URL", _DEFAULT_DB)

# SQLite の場合、DBファイルの親ディレクトリを自動作成する
if _db_url.startswith("sqlite"):
    _db_path_str = _db_url.split("///", 1)[-1]
    if _db_path_str and _db_path_str != ":memory:":
        Path(_db_path_str).parent.mkdir(parents=True, exist_ok=True)

engine = create_async_engine(_db_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def migrate_db() -> None:
    """既存DBに不足カラムを追加する（Alembicなしの簡易マイグレーション）。

    新規インストール時は init_db() が全カラムを作成するためこの関数は no-op になる。
    既存DBのアップグレード時にのみカラムが追加される。
    """
    async with engine.begin() as conn:
        result = await conn.execute(text("PRAGMA table_info(memory_entries)"))
        existing_cols = {row[1] for row in result.fetchall()}

        additions = [
            ("importance_score", "REAL NOT NULL DEFAULT 0.5"),
            ("access_count", "INTEGER NOT NULL DEFAULT 0"),
            ("last_accessed_at", "DATETIME"),
        ]
        for col, definition in additions:
            if col not in existing_cols:
                await conn.execute(
                    text(f"ALTER TABLE memory_entries ADD COLUMN {col} {definition}")
                )
                logger.info("migrate_db: added column memory_entries.%s", col)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session  # type: ignore[misc]
