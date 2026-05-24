from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_LOG_PATH = _PROJECT_ROOT / "data" / "logs" / "operations.jsonl"


def log_operation(
    intent: str,
    input_summary: str,
    llm_route: str,
    tools_called: list[str] | None = None,
    external_apis_called: list[str] | None = None,
    result: str = "success",
    requires_confirmation: bool = False,
    cloud_escalated: bool = False,
    session_id: str = "",
    log_path: Path | None = None,
) -> None:
    path = log_path or _DEFAULT_LOG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    entry: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).astimezone().isoformat(),
        "session_id": session_id,
        "intent": intent,
        "input_summary": input_summary[:200],
        "llm_route": llm_route,
        "cloud_escalated": cloud_escalated,
        "tools_called": tools_called or [],
        "external_apis_called": external_apis_called or [],
        "result": result,
        "requires_confirmation": requires_confirmation,
    }

    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        logger.exception("Failed to write operation log")
