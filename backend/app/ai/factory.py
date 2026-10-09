"""
Picks the active AIProvider from the AI_PROVIDER env var. This is the only
place that knows which concrete provider class is in use — everything else
(agent, tools, API) talks to the AIProvider interface only.
"""
from functools import lru_cache

from app.ai.base import AIProvider
from app.config import get_settings


@lru_cache
def get_ai_provider() -> AIProvider:
    settings = get_settings()
    provider = settings.ai_provider.lower()

    if provider == "mock":
        from app.ai.providers.mock_provider import MockAIProvider
        return MockAIProvider()

    if provider == "claude":
        from app.ai.providers.claude_provider import ClaudeProvider
        return ClaudeProvider()

    if provider == "ollama":
        from app.ai.providers.ollama_provider import OllamaProvider
        return OllamaProvider()

    raise ValueError(f"Unknown AI_PROVIDER: {settings.ai_provider!r} (expected mock, claude, or ollama)")
