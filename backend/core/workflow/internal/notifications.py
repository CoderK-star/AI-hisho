from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def send_notification(message: str, method: str = "terminal", speak: bool = False) -> bool:
    """Send a notification via the specified method.

    Args:
        message: Notification text.
        method: ``terminal`` | ``os`` | ``speech``.
        speak: If True and method is not ``speech``, also speak the message
               via TTS (requires ``voice.notification_speech: true`` in settings).
    """
    success = await _send(message, method)

    if speak or _notification_speech_enabled():
        await _speak_notification(message)

    return success


async def _send(message: str, method: str) -> bool:
    if method == "terminal":
        logger.info("[NOTIFICATION] %s", message)
        print(f"\n🔔 {message}\n")
        return True

    if method == "os":
        try:
            import subprocess
            import sys

            if sys.platform == "win32":
                safe_msg = message.replace('"', "'")
                ps_cmd = (
                    '[System.Reflection.Assembly]::LoadWithPartialName'
                    '("System.Windows.Forms") | Out-Null; '
                    f'[System.Windows.Forms.MessageBox]::Show("{safe_msg}", "AI秘書")'
                )
                subprocess.Popen(
                    ["powershell", "-Command", ps_cmd],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
            elif sys.platform == "darwin":
                subprocess.Popen(["osascript", "-e", f'display notification "{message}"'])
            else:
                subprocess.Popen(["notify-send", "AI秘書", message])
            return True
        except Exception:
            logger.exception("OS notification failed, falling back to terminal")
            print(f"\n🔔 {message}\n")
            return True

    if method == "speech":
        await _speak_notification(message)
        return True

    logger.warning("Unknown notification method: %s", method)
    return False


def _notification_speech_enabled() -> bool:
    try:
        from backend.config.loader import load_settings

        return bool(load_settings().get("voice", {}).get("notification_speech", False))
    except Exception:
        return False


async def _speak_notification(message: str) -> None:
    try:
        from backend.stt_tts.tts import get_tts_client

        await get_tts_client().play(message)
    except Exception:
        logger.exception("TTS notification failed")
