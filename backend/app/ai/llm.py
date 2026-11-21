from typing import Protocol

from app.config import settings


class LLMError(Exception):
    """Raised when the language model service cannot produce an answer."""


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class FakeLLM:
    """Used when no API key is configured (development and tests)."""

    def complete(self, system: str, user: str) -> str:
        return "[fake-llm] This is a placeholder answer based on the retrieved passages. [1]"


class AnthropicLLM:
    def __init__(self, api_key: str, model: str):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key, timeout=30.0)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=700,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(block.text for block in message.content if block.type == "text")
        except Exception as exc:  # network, auth, rate limit, timeout...
            raise LLMError(str(exc)) from exc


def get_llm() -> LLM:
    if settings.llm_api_key:
        return AnthropicLLM(settings.llm_api_key, settings.llm_model)
    return FakeLLM()
