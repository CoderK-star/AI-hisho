from __future__ import annotations

import asyncio
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


class STTError(Exception):
    pass


class STTClient:
    """Speech-to-Text client using Whisper (faster-whisper backend)."""

    def __init__(self, model: str = "base", language: str = "ja", device: str = "cpu") -> None:
        self._model_name = model
        self._language = language if language != "auto" else None
        self._device = device
        self._model = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel  # type: ignore[import]

            self._model = WhisperModel(
                self._model_name,
                device=self._device,
                compute_type="int8",
            )
            logger.info("Whisper model loaded: %s on %s", self._model_name, self._device)
        except ImportError as e:
            raise STTError(
                "faster-whisper is not installed. Run: pip install -e '.[stt]'"
            ) from e

    def transcribe_file(self, audio_path: str | Path) -> str:
        """Transcribe an audio file to text. Synchronous — run in thread if needed."""
        self._load_model()
        try:
            segments, info = self._model.transcribe(
                str(audio_path),
                language=self._language,
                beam_size=5,
            )
            text = " ".join(s.text.strip() for s in segments)
            logger.debug("STT: %r (detected_lang=%s)", text[:60], info.language)
            return text.strip()
        except Exception as e:
            raise STTError(f"Transcription failed: {e}") from e

    def transcribe_bytes(self, audio_data: bytes, suffix: str = ".wav") -> str:
        """Transcribe raw audio bytes to text."""
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
            f.write(audio_data)
            tmp_path = Path(f.name)
        try:
            return self.transcribe_file(tmp_path)
        finally:
            tmp_path.unlink(missing_ok=True)

    async def async_transcribe_bytes(self, audio_data: bytes, suffix: str = ".wav") -> str:
        """Async wrapper — runs transcription in the default thread pool."""
        return await asyncio.to_thread(self.transcribe_bytes, audio_data, suffix)


_stt_client: STTClient | None = None


def get_stt_client() -> STTClient:
    global _stt_client
    if _stt_client is None:
        from backend.config.loader import load_settings

        cfg = load_settings().get("stt", {})
        _stt_client = STTClient(
            model=cfg.get("model", "base"),
            language=cfg.get("language", "ja"),
            device=cfg.get("device", "cpu"),
        )
    return _stt_client
