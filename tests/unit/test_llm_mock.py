import pytest

from backend.llm.providers.base import LLMMessage
from backend.llm.providers.mock import MockProvider


@pytest.mark.asyncio
async def test_mock_generate():
    provider = MockProvider()
    messages = [LLMMessage(role="user", content="hello")]
    result = await provider.generate(messages)
    assert "hello" in result.content
    assert result.provider == "mock"


@pytest.mark.asyncio
async def test_mock_health():
    provider = MockProvider()
    assert await provider.health_check()
