from __future__ import annotations

import logging
import struct
from abc import ABC, abstractmethod

import httpx

logger = logging.getLogger(__name__)


class TTSError(Exception):
    pass


class TTSProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str) -> bytes:
        """Return raw audio bytes (WAV or MP3)."""


class VoicevoxTTS(TTSProvider):
    """VOICEVOX REST API client (local server required)."""

    def __init__(self, url: str = "http://localhost:50021", speaker_id: int = 1) -> None:
        self._url = url.rstrip("/")
        self._speaker_id = speaker_id

    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                f"{self._url}/audio_query",
                params={"text": text, "speaker": self._speaker_id},
            )
            r.raise_for_status()
            r2 = await client.post(
                f"{self._url}/synthesis",
                params={"speaker": self._speaker_id},
                json=r.json(),
                headers={"Content-Type": "application/json"},
            )
            r2.raise_for_status()
            return r2.content


class OpenAITTS(TTSProvider):
    """OpenAI TTS API client."""

    def __init__(self, api_key: str, voice: str = "alloy", model: str = "tts-1") -> None:
        self._api_key = api_key
        self._voice = voice
        self._model = model

    async def synthesize(self, text: str) -> bytes:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(
                "https://api.openai.com/v1/audio/speech",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self._model, "input": text, "voice": self._voice,
                      "response_format": "mp3"},
            )
            r.raise_for_status()
            return r.content


class MockTTS(TTSProvider):
    """No-op provider for tests and disabled-TTS environments."""

    async def synthesize(self, text: str) -> bytes:
        logger.info("[MockTTS] synthesize(%r)", text[:50])
        return _minimal_wav()


def _minimal_wav(duration_samples: int = 1600, sample_rate: int = 16000) -> bytes:
    """Return a minimal valid WAV file containing silence."""
    data = b"\x00\x00" * duration_samples
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(data), b"WAVE",
        b"fmt ", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16,
        b"data", len(data),
    )
    return header + data


class TTSClient:
    def __init__(self, provider: TTSProvider) -> None:
        self._provider = provider

    async def synthesize(self, text: str) -> bytes:
        try:
            return await self._provider.synthesize(text)
        except Exception as e:
            raise TTSError(f"TTS synthesis failed: {e}") from e

    async def play(self, text: str) -> None:
        """Synthesize and play audio through the default output device."""
        audio_bytes = await self.synthesize(text)
        _play_audio(audio_bytes)


def _play_audio(audio_bytes: bytes) -> None:
    """Play audio bytes via sounddevice (optional dependency)."""
    try:
        import io

        import sounddevice as sd  # type: ignore[import]
        import soundfile as sf  # type: ignore[import]

        data, samplerate = sf.read(io.BytesIO(audio_bytes))
        sd.play(data, samplerate)
        sd.wait()
    except ImportError:
        logger.warning("sounddevice/soundfile not installed; audio playback skipped")
    except Exception:
        logger.exception("Audio playback failed")


_tts_client: TTSClient | None = None


def get_tts_client() -> TTSClient:
    global _tts_client
    if _tts_client is None:
        import os

        from backend.config.loader import load_settings

        cfg = load_settings().get("tts", {})
        provider_name = cfg.get("provider", "mock")

        if provider_name == "voicevox":
            vc = cfg.get("voicevox", {})
            provider: TTSProvider = VoicevoxTTS(
                url=vc.get("url", "http://localhost:50021"),
                speaker_id=int(vc.get("speaker_id", 1)),
            )
        elif provider_name == "openai":
            oc = cfg.get("openai", {})
            provider = OpenAITTS(
                api_key=os.environ.get("OPENAI_API_KEY", ""),
                voice=oc.get("voice", "alloy"),
                model=oc.get("model", "tts-1"),
            )
        else:
            provider = MockTTS()

        _tts_client = TTSClient(provider)
    return _tts_client
