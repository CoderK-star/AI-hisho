from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.schemas.common import ChatResponse
from backend.core.context.engine import load_context
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
from backend.stt_tts.stt import STTError, get_stt_client
from backend.stt_tts.tts import TTSError, get_tts_client

router = APIRouter(prefix="/voice", tags=["voice"])

_llm_client: LLMClient | None = None


def _get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(..., description="音声ファイル (wav/mp3/m4a/ogg)"),
) -> dict[str, str]:
    """音声ファイルをテキストに変換する (STT のみ)。"""
    audio_bytes = await file.read()
    suffix = _content_type_to_ext(file.content_type or "audio/wav")
    try:
        text = await get_stt_client().async_transcribe_bytes(audio_bytes, suffix)
    except STTError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {"text": text, "filename": file.filename or ""}


@router.post("/chat", response_model=ChatResponse)
async def voice_chat(
    file: UploadFile = File(..., description="音声ファイル"),
    session_id: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    """音声入力でチャット。STT → Intent 分類 → LLM → テキスト応答。"""
    audio_bytes = await file.read()
    suffix = _content_type_to_ext(file.content_type or "audio/wav")

    try:
        message = await get_stt_client().async_transcribe_bytes(audio_bytes, suffix)
    except STTError as exc:
        raise HTTPException(status_code=503, detail=f"STT failed: {exc}")

    reply, intent_val, sid, tools = await _run_chat(message, session_id, session, "[voice] ")
    return ChatResponse(reply=reply, intent=intent_val, session_id=sid, tools_called=tools)


@router.post("/speak")
async def speak_text(
    text: str = Form(..., description="読み上げるテキスト"),
) -> Response:
    """テキストを音声合成して返す (TTS のみ)。"""
    try:
        audio_bytes = await get_tts_client().synthesize(text)
    except TTSError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return Response(content=audio_bytes, media_type=_detect_audio_mime(audio_bytes))


@router.post("/chat-spoken")
async def voice_chat_spoken(
    file: UploadFile = File(..., description="音声ファイル"),
    session_id: str | None = Form(default=None),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """音声入力 → チャット → TTS で音声レスポンスを返す (完全音声フロー)。"""
    audio_bytes = await file.read()
    suffix = _content_type_to_ext(file.content_type or "audio/wav")

    try:
        message = await get_stt_client().async_transcribe_bytes(audio_bytes, suffix)
    except STTError as exc:
        raise HTTPException(status_code=503, detail=f"STT failed: {exc}")

    reply, intent_val, sid, _tools = await _run_chat(message, session_id, session, "[voice-spoken] ")

    try:
        reply_audio = await get_tts_client().synthesize(reply)
    except TTSError as exc:
        raise HTTPException(status_code=503, detail=f"TTS failed: {exc}")

    return Response(
        content=reply_audio,
        media_type=_detect_audio_mime(reply_audio),
        headers={
            "X-Reply-Text": reply,
            "X-Intent": intent_val,
            "X-Session-Id": sid,
        },
    )


# ---------------------------------------------------------------------------
# Shared chat processing
# ---------------------------------------------------------------------------


async def _run_chat(
    message: str,
    session_id: str | None,
    session: AsyncSession,
    log_prefix: str = "",
) -> tuple[str, str, str, list[str]]:
    """Core chat pipeline shared by text-reply and audio-reply voice endpoints."""
    sid = session_id or uuid.uuid4().hex
    classification = classify(message)
    intent = classification.intent

    await save_conversation(session, sid, "user", message)
    ctx = await load_context(intent, session, sid)
    target = route(intent)
    wf_result = await workflow_execute(intent, session, message)
    tools_called = wf_result.tools_called or []

    if _is_rule_based_only(target, wf_result):
        reply = _format_rule_based(intent, wf_result)
    elif target in (RouteTarget.LOCAL, RouteTarget.CLOUD) or wf_result.needs_llm:
        msgs = _build_messages(ctx, wf_result, message)
        response = await _get_llm().generate(msgs, target)
        reply = response.content
    else:
        reply = wf_result.error or "処理できませんでした。"

    reply = format_response(reply)
    await save_conversation(session, sid, "assistant", reply)

    log_operation(
        intent=intent.value,
        input_summary=f"{log_prefix}{message[:100]}",
        llm_route=target.value,
        tools_called=tools_called,
        session_id=sid,
    )
    return reply, intent.value, sid, tools_called


# ---------------------------------------------------------------------------
# Helpers (mirrors logic in chat.py without creating a shared dep)
# ---------------------------------------------------------------------------


def _is_rule_based_only(target: RouteTarget, wf: WorkflowResult) -> bool:
    return target == RouteTarget.RULE_BASED and wf.success and not wf.needs_llm


def _format_rule_based(intent: IntentType, wf: WorkflowResult) -> str:
    if wf.error:
        return wf.error
    if wf.data is None:
        return "データがありません。"
    return json.dumps(wf.data, ensure_ascii=False, indent=2)


def _build_messages(ctx, wf: WorkflowResult, user_input: str) -> list[LLMMessage]:  # type: ignore[no-untyped-def]
    from backend.core.context.engine import ContextData

    messages: list[LLMMessage] = [
        LLMMessage(role="system", content=_build_system_prompt(ctx, wf)),
    ]
    for conv in ctx.recent_conversations:
        messages.append(LLMMessage(role=conv["role"], content=conv["content"]))
    messages.append(LLMMessage(role="user", content=user_input))
    if wf.data and not _is_rag_result(wf):
        messages.append(
            LLMMessage(
                role="system",
                content=f"実行結果: {json.dumps(wf.data, ensure_ascii=False)}",
            )
        )
    return messages


def _is_rag_result(wf: WorkflowResult) -> bool:
    return bool(wf.tools_called and "rag.search" in wf.tools_called)


def _build_system_prompt(ctx, wf: WorkflowResult) -> str:  # type: ignore[no-untyped-def]
    import json as _json

    parts = [
        "あなたはユーザの個人秘書アシスタントです。",
        "簡潔で正確な情報を提供してください。",
        f"現在時刻: {ctx.current_time}",
    ]
    if ctx.tasks:
        parts.append(f"未完了タスク: {_json.dumps(ctx.tasks, ensure_ascii=False)}")
    if ctx.reminders:
        parts.append(f"リマインダー: {_json.dumps(ctx.reminders, ensure_ascii=False)}")
    if ctx.memories:
        lines = ["重要な記憶（重要度順）:"]
        for m in ctx.memories:
            lines.append(f"  [{m['source']}] {m['content'][:200]}")
        parts.append("\n".join(lines))
    if _is_rag_result(wf) and wf.data:
        results = wf.data.get("results", [])
        if results:
            lines = ["関連するメモ・記録:"]
            for r in results:
                lines.append(f"  [{r['type']}] {r['text'][:300]}")
            parts.append("\n".join(lines))
            parts.append("上記の関連情報を参考にして回答してください。")
    return "\n".join(parts)


def _content_type_to_ext(content_type: str) -> str:
    mapping = {
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/wave": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".m4a",
        "audio/x-m4a": ".m4a",
        "audio/ogg": ".ogg",
        "audio/webm": ".webm",
        "audio/flac": ".flac",
    }
    return mapping.get(content_type.split(";")[0].strip(), ".wav")


def _detect_audio_mime(data: bytes) -> str:
    if data[:4] == b"RIFF":
        return "audio/wav"
    if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio/mpeg"
    if data[:4] == b"OggS":
        return "audio/ogg"
    return "audio/wav"
