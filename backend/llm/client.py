from __future__ import annotations

import logging
from typing import Any

from backend.config.loader import load_settings
from backend.llm.providers.base import LLMMessage, LLMProvider, LLMResponse
from backend.llm.providers.mock import MockProvider
from backend.llm.providers.ollama import OllamaProvider
from backend.llm.providers.openai import OpenAIProvider
from backend.llm.router import RouteTarget

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        self._settings = settings or load_settings().get("llm", {})
        self._providers: dict[str, LLMProvider] = {}
        self._fallback_mode = self._settings.get("local_fallback", "notify")
        self._init_providers()

    def _init_providers(self) -> None:
        providers_cfg = self._settings.get("providers", {})

        if "ollama" in providers_cfg:
            cfg = providers_cfg["ollama"]
            self._providers["local"] = OllamaProvider(
                base_url=cfg.get("base_url", "http://localhost:11434"),
                model=cfg.get("model", "llama3"),
                timeout=int(cfg.get("timeout", 30)),
            )

        if "openai" in providers_cfg:
            cfg = providers_cfg["openai"]
            self._providers["cloud"] = OpenAIProvider(
                model=cfg.get("model", "gpt-4o-mini"),
                timeout=int(cfg.get("timeout", 60)),
            )

        self._providers["mock"] = MockProvider()

    def _get_provider(self, target: RouteTarget) -> LLMProvider:
        if target == RouteTarget.LOCAL:
            return self._providers.get("local", self._providers["mock"])
        if target == RouteTarget.CLOUD:
            return self._providers.get("cloud", self._providers["mock"])
        return self._providers["mock"]

    async def generate(
        self,
        messages: list[LLMMessage],
        target: RouteTarget,
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        provider = self._get_provider(target)

        try:
            return await provider.generate(
                messages, temperature=temperature, max_tokens=max_tokens
            )
        except Exception:
            logger.exception("LLM provider %s failed", provider.name)

            if target != RouteTarget.LOCAL:
                raise

            if self._fallback_mode == "fail":
                raise
            if self._fallback_mode == "cloud":
                cloud = self._providers.get("cloud")
                if cloud:
                    logger.warning("Falling back to cloud provider")
                    return await cloud.generate(
                        messages, temperature=temperature, max_tokens=max_tokens
                    )
                raise
            # "notify" — return error response for the API layer to handle
            return LLMResponse(
                content="[ERROR] ローカルLLMが応答できませんでした。クラウドへの切り替えが必要です。",
                provider="fallback",
                model="none",
            )
