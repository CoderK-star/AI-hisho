from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _PROJECT_ROOT / "config"


def _resolve_env_vars(value: str) -> str:
    def _replace(m: re.Match[str]) -> str:
        var, default = m.group(1), m.group(2)
        return os.environ.get(var, default if default is not None else "")

    return re.sub(r"\$\{(\w+)(?::-([^}]*))?\}", _replace, value)


def _walk_resolve(obj: Any) -> Any:
    if isinstance(obj, str):
        return _resolve_env_vars(obj)
    if isinstance(obj, dict):
        return {k: _walk_resolve(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_resolve(v) for v in obj]
    return obj


def load_yaml(name: str) -> dict[str, Any]:
    path = _CONFIG_DIR / name
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return _walk_resolve(raw)


def load_settings() -> dict[str, Any]:
    return load_yaml("settings.yaml")


def load_persona() -> dict[str, Any]:
    return load_yaml("persona.yaml")
