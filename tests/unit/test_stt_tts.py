"""Phase 4 — STT / TTS / Voice API unit tests."""
from __future__ import annotations

import io
import struct

import pytest
import pytest_asyncio
import respx
from httpx import Response

from backend.stt_tts.tts import (
    MockTTS,
    OpenAITTS,
    TTSClient,
    TTSError,
    VoicevoxTTS,
    _minimal_wav,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _is_valid_wav(data: bytes) -> bool:
    return len(data) >= 44 and data[:4] == b"RIFF" and data[8:12] == b"WAVE"


# ---------------------------------------------------------------------------
# _minimal_wav
# ---------------------------------------------------------------------------


def test_minimal_wav_is_valid_wav() -> None:
    wav = _minimal_wav()
    assert _is_valid_wav(wav)


def test_minimal_wav_custom_duration() -> None:
    wav = _minimal_wav(duration_samples=3200)
    assert _is_valid_wav(wav)
    # data chunk length = 3200 * 2 bytes (16-bit PCM)
    data_len = struct.unpack_from("<I", wav, 40)[0]
    assert data_len == 3200 * 2


# ---------------------------------------------------------------------------
# MockTTS
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_tts_returns_wav() -> None:
    client = TTSClient(MockTTS())
    audio = await client.synthesize("こんにちは")
    assert _is_valid_wav(audio)


@pytest.mark.asyncio
async def test_mock_tts_empty_text() -> None:
    client = TTSClient(MockTTS())
    audio = await client.synthesize("")
    assert _is_valid_wav(audio)


# ---------------------------------------------------------------------------
# VoicevoxTTS (HTTP mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voicevox_tts_success() -> None:
    fake_wav = _minimal_wav()

    with respx.mock(base_url="http://localhost:50021") as mock:
        mock.post("/audio_query").mock(return_value=Response(200, json={"speedScale": 1.0}))
        mock.post("/synthesis").mock(return_value=Response(200, content=fake_wav))

        provider = VoicevoxTTS(url="http://localhost:50021", speaker_id=1)
        audio = await provider.synthesize("テスト")

    assert audio == fake_wav


@pytest.mark.asyncio
async def test_voicevox_tts_server_error_raises() -> None:
    with respx.mock(base_url="http://localhost:50021") as mock:
        mock.post("/audio_query").mock(return_value=Response(500))

        provider = VoicevoxTTS(url="http://localhost:50021")
        client = TTSClient(provider)
        with pytest.raises(TTSError):
            await client.synthesize("テスト")


# ---------------------------------------------------------------------------
# OpenAITTS (HTTP mocked)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_openai_tts_success() -> None:
    fake_mp3 = b"\xff\xfb" + b"\x00" * 100  # minimal fake MP3

    with respx.mock(base_url="https://api.openai.com") as mock:
        mock.post("/v1/audio/speech").mock(return_value=Response(200, content=fake_mp3))

        provider = OpenAITTS(api_key="test-key", voice="alloy")
        audio = await provider.synthesize("Hello")

    assert audio == fake_mp3


@pytest.mark.asyncio
async def test_openai_tts_auth_error_raises() -> None:
    with respx.mock(base_url="https://api.openai.com") as mock:
        mock.post("/v1/audio/speech").mock(return_value=Response(401, json={"error": "unauthorized"}))

        provider = OpenAITTS(api_key="bad-key")
        client = TTSClient(provider)
        with pytest.raises(TTSError):
            await client.synthesize("Hello")


# ---------------------------------------------------------------------------
# STTClient (no faster-whisper required — tests the fallback path)
# ---------------------------------------------------------------------------


def test_stt_client_raises_on_missing_dependency() -> None:
    """STTClient should raise STTError (not ImportError) when faster-whisper absent."""
    import importlib
    import sys

    # Temporarily hide faster_whisper from the import system
    original = sys.modules.get("faster_whisper")
    sys.modules["faster_whisper"] = None  # type: ignore[assignment]
    try:
        # Re-import to get a fresh client without cached model
        from backend.stt_tts.stt import STTClient, STTError

        client = STTClient(model="base")
        with pytest.raises(STTError, match="faster-whisper"):
            client._load_model()
    finally:
        if original is None:
            sys.modules.pop("faster_whisper", None)
        else:
            sys.modules["faster_whisper"] = original


# ---------------------------------------------------------------------------
# Voice API endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_voice_transcribe_endpoint() -> None:
    """POST /api/voice/transcribe should return transcribed text."""
    from unittest.mock import AsyncMock, patch

    import httpx
    from httpx import ASGITransport

    from backend.main import app

    fake_text = "テストの音声です"

    with patch("backend.api.routes.voice.get_stt_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.async_transcribe_bytes = AsyncMock(return_value=fake_text)
        mock_get.return_value = mock_client

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            fake_wav = _minimal_wav()
            response = await ac.post(
                "/api/voice/transcribe",
                files={"file": ("test.wav", fake_wav, "audio/wav")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["text"] == fake_text


@pytest.mark.asyncio
async def test_voice_speak_endpoint() -> None:
    """POST /api/voice/speak should return audio bytes."""
    from unittest.mock import AsyncMock, patch

    import httpx
    from httpx import ASGITransport

    from backend.main import app

    fake_wav = _minimal_wav()

    with patch("backend.api.routes.voice.get_tts_client") as mock_get:
        mock_client = AsyncMock()
        mock_client.synthesize = AsyncMock(return_value=fake_wav)
        mock_get.return_value = mock_client

        transport = ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post(
                "/api/voice/speak",
                data={"text": "こんにちは"},
            )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/")
    assert response.content == fake_wav
