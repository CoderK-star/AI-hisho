from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import MemoCreate, MemoUpdate
from backend.core.workflow.internal.memos import add_memo, get_memo, list_memos, update_memo
from backend.db.session import get_session

router = APIRouter(prefix="/memos", tags=["memos"])


@router.post("")
async def create_memo(
    body: MemoCreate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await add_memo(session, content=body.content, title=body.title)
    from backend.rag.indexer import index_memo
    await index_memo(result)
    return result


@router.get("")
async def get_memos(
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    return await list_memos(session, limit=limit)


@router.get("/{memo_id}")
async def get_memo_detail(
    memo_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await get_memo(session, memo_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Memo not found")
    return result


@router.patch("/{memo_id}")
async def patch_memo(
    memo_id: str,
    body: MemoUpdate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    updates = body.model_dump(exclude_none=True)
    result = await update_memo(session, memo_id, **updates)
    if result is None:
        raise HTTPException(status_code=404, detail="Memo not found")
    return result
