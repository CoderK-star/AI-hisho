from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import MemoryPinRequest
from backend.core.memory.engine import deactivate_memory, get_active_memories, pin_memory
from backend.core.memory.pruner import prune_memories, recalculate_all_scores
from backend.db.session import get_session
from backend.rag.indexer import index_memory

router = APIRouter(prefix="/memories", tags=["memories"])


@router.get("")
async def list_memories(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """重要度スコア順にアクティブな記憶エントリを返す。アクセス回数を加算する。"""
    memories = await get_active_memories(session, limit=limit, record_access=True)
    return {"count": len(memories), "memories": memories}


@router.post("/pin")
async def pin(
    body: MemoryPinRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """ユーザが明示的に記憶をピン留めする（importance_score = 1.0）。"""
    result = await pin_memory(session, content=body.content)
    await index_memory(result)
    return result


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """記憶エントリを非アクティブ化（論理削除）する。"""
    ok = await deactivate_memory(session, memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"id": memory_id, "deactivated": True}


@router.post("/prune")
async def run_prune(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """重要度の低い auto_summary を手動でアーカイブし、全スコアを再計算する。"""
    scores_updated = await recalculate_all_scores(session)
    prune_result = await prune_memories(session)
    return {
        "scores_updated": scores_updated,
        "archived": prune_result["archived"],
        "checked": prune_result["checked"],
    }
