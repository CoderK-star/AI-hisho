from __future__ import annotations

import logging
import threading
from typing import Callable

logger = logging.getLogger(__name__)

OnWakeCallback = Callable[[bytes], None]


class WakeWordDaemon:
    """Background thread that detects a wake word and records the following utterance.

    When the wake word fires, ``on_wake`` is called with the recorded WAV bytes.
    Requires: pip install -e '.[wakeword]'  (openwakeword + sounddevice + numpy)

    Falls back to a warning log and exits the thread if dependencies are missing.
    """

    def __init__(
        self,
        keyword: str = "hey_assistant",
        sensitivity: float = 0.5,
        sample_rate: int = 16000,
        on_wake: OnWakeCallback | None = None,
    ) -> None:
        self._keyword = keyword
        self._sensitivity = sensitivity
        self._sample_rate = sample_rate
        self._on_wake = on_wake
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run, daemon=True, name="wakeword-daemon"
        )
        self._thread.start()
        logger.info("Wake word daemon started (keyword=%r, sensitivity=%.2f)",
                    self._keyword, self._sensitivity)

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Wake word daemon stopped")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _run(self) -> None:
        try:
            self._run_loop()
        except ImportError as exc:
            logger.warning(
                "Wake word detection disabled — missing dependency: %s. "
                "Run: pip install -e '.[wakeword]'",
                exc,
            )
        except Exception:
            logger.exception("Wake word daemon crashed")

    def _run_loop(self) -> None:
        import numpy as np
        import sounddevice as sd  # type: ignore[import]
        from openwakeword.model import Model  # type: ignore[import]

        # openwakeword ships pre-trained models; if no custom model is given
        # it loads the bundled "hey_jarvis" / "alexa" etc.  We load the
        # default bundle and threshold on overall confidence.
        oww_model = Model(inference_framework="onnx")

        chunk_size = 1280  # 80 ms at 16 kHz — openwakeword's expected frame size
        logger.info("Wake word daemon: listening on microphone…")

        with sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="int16",
            blocksize=chunk_size,
        ) as stream:
            while not self._stop_event.is_set():
                chunk, _ = stream.read(chunk_size)
                audio_frame = (chunk[:, 0] if chunk.ndim > 1 else chunk.flatten())
                predictions = oww_model.predict(audio_frame)
                max_score = max(predictions.values()) if predictions else 0.0
                if max_score >= self._sensitivity:
                    logger.info("Wake word detected (score=%.3f) — recording utterance", max_score)
                    self._handle_wake_event(stream)

    def _handle_wake_event(self, stream: object) -> None:  # noqa: ARG002
        """Record the user's utterance after wake word and invoke callback."""
        try:
            from backend.stt_tts.audio import AudioRecorder

            recorder = AudioRecorder()
            audio_bytes = recorder.record()
            if self._on_wake is not None:
                self._on_wake(audio_bytes)
        except Exception:
            logger.exception("Error while handling wake word event")


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_daemon: WakeWordDaemon | None = None


def get_daemon() -> WakeWordDaemon | None:
    return _daemon


def start_daemon(on_wake: OnWakeCallback) -> WakeWordDaemon | None:
    """Start the wake word daemon if enabled in settings. Returns None if disabled."""
    global _daemon
    from backend.config.loader import load_settings

    cfg = load_settings().get("voice", {}).get("wakeword", {})
    if not cfg.get("enabled", False):
        return None

    _daemon = WakeWordDaemon(
        keyword=cfg.get("keyword", "hey_assistant"),
        sensitivity=float(cfg.get("sensitivity", 0.5)),
        on_wake=on_wake,
    )
    _daemon.start()
    return _daemon


def stop_daemon() -> None:
    global _daemon
    if _daemon is not None:
        _daemon.stop()
        _daemon = None
