import logging
import time
from typing import Protocol

from app.config import settings

logger = logging.getLogger("documind.llm")

TIMEOUT_SECONDS = 30.0
MAX_TOKENS = 700
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


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

        self._client = anthropic.Anthropic(api_key=api_key, timeout=TIMEOUT_SECONDS)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        started = time.perf_counter()
        try:
            message = self._client.messages.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            answer = "".join(block.text for block in message.content if block.type == "text")
        except Exception as exc:  # network, auth, rate limit, timeout...
            logger.error("LLM call failed after %.2fs: %s", time.perf_counter() - started, exc)
            raise LLMError(str(exc)) from exc
        logger.info("LLM answered in %.2fs (anthropic, %s)", time.perf_counter() - started, self._model)
        return answer


class OpenRouterLLM:
    """OpenRouter speaks the OpenAI API, so we use the openai package with OpenRouter's address."""

    def __init__(self, api_key: str, model: str):
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key, base_url=OPENROUTER_BASE_URL, timeout=TIMEOUT_SECONDS)
        self._model = model

    def complete(self, system: str, user: str) -> str:
        started = time.perf_counter()
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                max_tokens=MAX_TOKENS,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            answer = response.choices[0].message.content or ""
        except Exception as exc:  # network, auth, rate limit, timeout, unknown model...
            logger.error("LLM call failed after %.2fs: %s", time.perf_counter() - started, exc)
            raise LLMError(str(exc)) from exc
        logger.info("LLM answered in %.2fs (openrouter, %s)", time.perf_counter() - started, self._model)
        return answer


def get_llm() -> LLM:
    if not settings.llm_api_key:
        return FakeLLM()
    if settings.llm_provider.lower() == "openrouter":
        return OpenRouterLLM(settings.llm_api_key, settings.llm_model)
    return AnthropicLLM(settings.llm_api_key, settings.llm_model)
