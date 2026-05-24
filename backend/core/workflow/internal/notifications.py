from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


async def send_notification(message: str, method: str = "terminal") -> bool:
    if method == "terminal":
        logger.info("[NOTIFICATION] %s", message)
        print(f"\n🔔 {message}\n")
        return True

    if method == "os":
        try:
            import subprocess
            import sys

            if sys.platform == "win32":
                ps_cmd = (
                    f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms") '
                    f"| Out-Null; "
                    f'[System.Windows.Forms.MessageBox]::Show("{message}", "AI秘書")'
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

    logger.warning("Unknown notification method: %s", method)
    return False
