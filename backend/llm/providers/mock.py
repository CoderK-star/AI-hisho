from __future__ import annotations

from backend.llm.providers.base import LLMMessage, LLMProvider, LLMResponse


class MockProvider(LLMProvider):
    @property
    def name(self) -> str:
        return "mock"

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> LLMResponse:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        return LLMResponse(
            content=f"[Mock] Received: {last_user[:100]}",
            provider="mock",
            model="mock-v1",
            usage={"prompt_tokens": 0, "completion_tokens": 0},
        )

    async def health_check(self) -> bool:
        return True
