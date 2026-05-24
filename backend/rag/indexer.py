from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Memo, MemoryEntry
from backend.rag.engine import RAGEngine

logger = logging.getLogger(__name__)


async def index_all(session: AsyncSession) -> int:
    engine = RAGEngine.get_instance()
    if engine is None:
        return 0

    await engine.initialize()
    count = 0

    stmt = select(Memo)
    memos = (await session.execute(stmt)).scalars().all()
    for memo in memos:
        text = f"{memo.title}\n{memo.content}".strip() if memo.title else memo.content
        await engine.index_document(
            doc_type="memo",
            doc_id=memo.id,
            text=text,
            metadata={"title": memo.title},
        )
        count += 1

    stmt = select(MemoryEntry).where(MemoryEntry.is_active == True)  # noqa: E712
    memories = (await session.execute(stmt)).scalars().all()
    for memory in memories:
        await engine.index_document(
            doc_type="memory",
            doc_id=memory.id,
            text=memory.content,
            metadata={"source": memory.source},
        )
        count += 1

    logger.info("RAG: %d件のドキュメントをインデックスしました", count)
    return count


async def index_memo(doc: dict[str, Any]) -> None:
    engine = RAGEngine.get_instance()
    if engine is None:
        return
    text = f"{doc.get('title', '')}\n{doc.get('content', '')}".strip()
    await engine.index_document(
        doc_type="memo",
        doc_id=doc["id"],
        text=text,
        metadata={"title": doc.get("title", "")},
    )


async def index_memory(doc: dict[str, Any]) -> None:
    engine = RAGEngine.get_instance()
    if engine is None:
        return
    await engine.index_document(
        doc_type="memory",
        doc_id=doc["id"],
        text=doc["content"],
        metadata={"source": doc.get("source", "")},
    )
