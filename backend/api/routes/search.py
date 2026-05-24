from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.rag.retriever import is_available, retrieve

router = APIRouter(prefix="/search", tags=["search"])


@router.get("")
async def search_knowledge(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    if not is_available():
        raise HTTPException(
            status_code=503,
            detail="RAG が無効です。settings.yaml の rag.enabled を true に設定してください。",
        )
    results = await retrieve(q, limit=limit)
    return {"query": q, "count": len(results), "results": results}
