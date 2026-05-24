from __future__ import annotations

from typing import Any

from backend.config.loader import load_persona


def format_response(raw: str, persona_config: dict[str, Any] | None = None) -> str:
    config = persona_config or load_persona()
    style = config.get("style", {})
    formatting = config.get("formatting", {})

    lines = raw.strip().splitlines()
    max_lines = formatting.get("max_response_lines", 20)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("...")

    result = "\n".join(lines)

    suffix = style.get("suffix", "")
    if suffix and not result.endswith(("。", "！", "？", ".", "!", "?")):
        pass

    return result
