from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import ChatRequest, ChatResponse
from backend.core.context.engine import load_context
from backend.core.intent.classifier import classify
from backend.core.logging import log_operation
from backend.core.memory.engine import save_conversation
from backend.core.persona import format_response
from backend.core.workflow.engine import execute as workflow_execute
from backend.db.session import get_session
from backend.llm.client import LLMClient
from backend.llm.providers.base import LLMMessage
from backend.llm.router import RouteTarget, route

router = APIRouter()
_llm_client: LLMClient | None = None


def _get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    session_id = req.session_id or uuid.uuid4().hex

    classification = classify(req.message)
    intent = classification.intent

    await save_conversation(session, session_id, "user", req.message)

    ctx = await load_context(intent, session, session_id)

    target = route(intent)

    wf_result = await workflow_execute(intent, session, req.message)
    tools_called = wf_result.tools_called or []

    if target == RouteTarget.RULE_BASED and wf_result.success and not wf_result.needs_llm:
        import json
        reply = json.dumps(wf_result.data, ensure_ascii=False, indent=2)
    elif target in (RouteTarget.LOCAL, RouteTarget.CLOUD) or wf_result.needs_llm:
        messages = [
            LLMMessage(role="system", content=_build_system_prompt(ctx)),
        ]
        for conv in ctx.recent_conversations:
            messages.append(LLMMessage(role=conv["role"], content=conv["content"]))
        messages.append(LLMMessage(role="user", content=req.message))

        if wf_result.data:
            import json
            data_str = json.dumps(wf_result.data, ensure_ascii=False)
            messages.append(
                LLMMessage(role="system", content=f"実行結果: {data_str}")
            )

        llm = _get_llm()
        response = await llm.generate(messages, target)
        reply = response.content
    else:
        reply = "お手伝いできることがあれば、お気軽にどうぞ。"

    reply = format_response(reply)
    await save_conversation(session, session_id, "assistant", reply)

    log_operation(
        intent=intent.value,
        input_summary=req.message[:100],
        llm_route=target.value,
        tools_called=tools_called,
        session_id=session_id,
    )

    return ChatResponse(
        reply=reply,
        intent=intent.value,
        session_id=session_id,
        tools_called=tools_called,
    )


def _build_system_prompt(ctx: object) -> str:
    import json
    parts = [
        "あなたはユーザの個人秘書アシスタントです。",
        "簡潔で正確な情報を提供してください。",
        f"現在時刻: {getattr(ctx, 'current_time', '')}",
    ]
    if hasattr(ctx, "tasks") and ctx.tasks:
        parts.append(f"未完了タスク: {json.dumps(ctx.tasks, ensure_ascii=False)}")
    if hasattr(ctx, "reminders") and ctx.reminders:
        parts.append(f"リマインダー: {json.dumps(ctx.reminders, ensure_ascii=False)}")
    return "\n".join(parts)
