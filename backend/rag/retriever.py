from __future__ import annotations

from typing import Any

from backend.rag.engine import RAGEngine


async def retrieve(query: str, limit: int = 5) -> list[dict[str, Any]]:
    engine = RAGEngine.get_instance()
    if engine is None:
        return []
    return await engine.search(query, limit=limit)


def is_available() -> bool:
    return RAGEngine.get_instance() is not None
