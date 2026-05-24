from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.db.models import Base

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


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session  # type: ignore[misc]
