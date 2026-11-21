import pytest

from app.ai import llm
from app.ai.llm import AnthropicLLM, FakeLLM, LLMError, OpenRouterLLM, get_llm
from app.config import settings
from app.services.rag import NOT_FOUND, answer_question, build_prompt

CHUNKS = [
    {"document_id": 1, "filename": "regulation.pdf", "page": 8, "text": "The internship lasts 40 days.", "score": 0.8},
    {"document_id": 1, "filename": "regulation.pdf", "page": 9, "text": "Apply 30 days before.", "score": 0.5},
]


def test_no_key_gives_fake_llm(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "")
    assert isinstance(get_llm(), FakeLLM)


def test_default_provider_is_anthropic(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "test-key")
    monkeypatch.setattr(settings, "llm_provider", "anthropic")
    assert isinstance(get_llm(), AnthropicLLM)


def test_openrouter_provider(monkeypatch):
    monkeypatch.setattr(settings, "llm_api_key", "sk-or-test")
    monkeypatch.setattr(settings, "llm_provider", "OpenRouter")
    monkeypatch.setattr(settings, "llm_model", "openai/gpt-4.1-mini")
    client = get_llm()
    assert isinstance(client, OpenRouterLLM)
    assert str(client._client.base_url).startswith(llm.OPENROUTER_BASE_URL)


def test_openrouter_failure_becomes_llm_error(monkeypatch):
    client = OpenRouterLLM("sk-or-test", "openai/gpt-4.1-mini")

    def boom(**kwargs):
        raise RuntimeError("network down")

    monkeypatch.setattr(client._client.chat.completions, "create", boom)
    with pytest.raises(LLMError):
        client.complete("system", "user")


def test_no_chunks_says_not_found_without_calling_llm():
    class MustNotBeCalled:
        def complete(self, system, user):
            raise AssertionError("LLM was called although nothing was found")

    assert answer_question("What is the cafeteria menu?", [], llm=MustNotBeCalled()) == NOT_FOUND


def test_prompt_has_numbered_passages_with_file_and_page():
    prompt = build_prompt("How long is the internship?", CHUNKS)
    assert "[1] (regulation.pdf, page 8) The internship lasts 40 days." in prompt
    assert "[2] (regulation.pdf, page 9)" in prompt
    assert prompt.endswith("Question: How long is the internship?")
