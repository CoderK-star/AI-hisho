from __future__ import annotations

import io
import logging

logger = logging.getLogger(__name__)

_DEFAULT_SAMPLE_RATE = 16000
_SILENCE_THRESHOLD = 0.01   # RMS amplitude below this counts as silence
_SILENCE_DURATION_SEC = 1.5  # consecutive seconds of silence to end recording
_MAX_DURATION_SEC = 30.0


class AudioRecorder:
    """Records audio from the default microphone until silence is detected.

    Requires: pip install -e '.[voice]'  (sounddevice + soundfile + numpy)
    """

    def __init__(
        self,
        sample_rate: int = _DEFAULT_SAMPLE_RATE,
        silence_threshold: float = _SILENCE_THRESHOLD,
        silence_duration: float = _SILENCE_DURATION_SEC,
        max_duration: float = _MAX_DURATION_SEC,
    ) -> None:
        self._sample_rate = sample_rate
        self._silence_threshold = silence_threshold
        self._silence_duration = silence_duration
        self._max_duration = max_duration

    def record(self) -> bytes:
        """Block until voice input ends. Returns WAV bytes."""
        try:
            import numpy as np
            import sounddevice as sd  # type: ignore[import]
        except ImportError as e:
            raise RuntimeError(
                "sounddevice/numpy not installed. Run: pip install -e '.[voice]'"
            ) from e

        chunk_sec = 0.1
        chunk_size = int(self._sample_rate * chunk_sec)
        silence_chunks_needed = int(self._silence_duration / chunk_sec)
        max_chunks = int(self._max_duration / chunk_sec)

        frames: list[np.ndarray] = []
        silent_count = 0

        logger.debug("AudioRecorder: listening (silence=%.1fs)", self._silence_duration)
        with sd.InputStream(
            samplerate=self._sample_rate, channels=1, dtype="float32"
        ) as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_size)
                frames.append(chunk.copy())
                rms = float(np.sqrt(np.mean(chunk**2)))
                if rms < self._silence_threshold:
                    silent_count += 1
                    # Only end early if we already have some speech
                    if silent_count >= silence_chunks_needed and len(frames) > silence_chunks_needed:
                        break
                else:
                    silent_count = 0

        logger.debug("AudioRecorder: %d frames captured", len(frames))
        audio = np.concatenate(frames, axis=0)
        return _ndarray_to_wav(audio, self._sample_rate)


def _ndarray_to_wav(audio: "np.ndarray", sample_rate: int) -> bytes:  # type: ignore[name-defined]
    try:
        import soundfile as sf  # type: ignore[import]
    except ImportError as e:
        raise RuntimeError("soundfile not installed. Run: pip install -e '.[voice]'") from e

    buf = io.BytesIO()
    sf.write(buf, audio, sample_rate, format="WAV", subtype="PCM_16")
    return buf.getvalue()
