from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from backend.core.workflow.adapters.calendar import get_calendar_adapter

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/events")
async def list_events(
    days: int = Query(7, ge=1, le=90, description="何日先まで取得するか"),
) -> dict:
    adapter = get_calendar_adapter()
    if adapter is None:
        raise HTTPException(
            status_code=503,
            detail="カレンダー連携が無効です。settings.yaml の calendar.enabled を true に設定してください。",
        )
    events = await adapter.get_upcoming_events(days=days)
    return {"days": days, "count": len(events), "events": events}


@router.get("/health")
async def calendar_health() -> dict:
    adapter = get_calendar_adapter()
    if adapter is None:
        return {"available": False, "reason": "calendar.enabled が false"}
    ok = await adapter.health_check()
    return {"available": ok, "reason": "認証済み" if ok else "認証が必要です"}
