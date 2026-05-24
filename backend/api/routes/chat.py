from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import ChatRequest, ChatResponse
from backend.core.context.engine import ContextData, load_context
from backend.core.intent.classifier import classify
from backend.core.intent.rules import IntentType
from backend.core.logging import log_operation
from backend.core.memory.engine import save_conversation
from backend.core.persona import format_response
from backend.core.workflow.engine import WorkflowResult, execute as workflow_execute
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

    if _is_rule_based_only(target, wf_result):
        reply = _format_rule_based(intent, wf_result)
    elif target in (RouteTarget.LOCAL, RouteTarget.CLOUD) or wf_result.needs_llm:
        messages = _build_messages(ctx, wf_result, req.message)
        llm = _get_llm()
        response = await llm.generate(messages, target)
        reply = response.content
    else:
        reply = wf_result.error or "処理できませんでした。"

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


def _is_rule_based_only(target: RouteTarget, wf: WorkflowResult) -> bool:
    return target == RouteTarget.RULE_BASED and wf.success and not wf.needs_llm


def _format_rule_based(intent: IntentType, wf: WorkflowResult) -> str:
    if wf.error:
        return wf.error
    if wf.data is None:
        return "データがありません。"
    return json.dumps(wf.data, ensure_ascii=False, indent=2)


def _build_messages(
    ctx: ContextData, wf: WorkflowResult, user_input: str
) -> list[LLMMessage]:
    messages: list[LLMMessage] = [
        LLMMessage(role="system", content=_build_system_prompt(ctx, wf)),
    ]
    for conv in ctx.recent_conversations:
        messages.append(LLMMessage(role=conv["role"], content=conv["content"]))
    messages.append(LLMMessage(role="user", content=user_input))

    if wf.data and not _is_rag_result(wf):
        messages.append(
            LLMMessage(role="system", content=f"実行結果: {json.dumps(wf.data, ensure_ascii=False)}")
        )
    return messages


def _is_rag_result(wf: WorkflowResult) -> bool:
    return bool(wf.tools_called and "rag.search" in wf.tools_called)


def _build_system_prompt(ctx: ContextData, wf: WorkflowResult) -> str:
    parts = [
        "あなたはユーザの個人秘書アシスタントです。",
        "簡潔で正確な情報を提供してください。",
        f"現在時刻: {ctx.current_time}",
    ]
    if ctx.tasks:
        parts.append(f"未完了タスク: {json.dumps(ctx.tasks, ensure_ascii=False)}")
    if ctx.reminders:
        parts.append(f"リマインダー: {json.dumps(ctx.reminders, ensure_ascii=False)}")

    # RAG 検索結果をコンテキストとして注入
    if _is_rag_result(wf) and wf.data:
        results = wf.data.get("results", [])
        if results:
            rag_lines = ["関連するメモ・記録:"]
            for r in results:
                rag_lines.append(f"  [{r['type']}] {r['text'][:300]}")
            parts.append("\n".join(rag_lines))
            parts.append("上記の関連情報を参考にして回答してください。")

    # カレンダーイベントをコンテキストとして注入
    if wf.tools_called and "adapters.calendar.get_events" in wf.tools_called and wf.data:
        events = wf.data.get("events", [])
        if events:
            ev_lines = ["カレンダーの予定:"]
            for e in events:
                ev_lines.append(f"  {e['start']} — {e['title']}")
            parts.append("\n".join(ev_lines))

    return "\n".join(parts)
