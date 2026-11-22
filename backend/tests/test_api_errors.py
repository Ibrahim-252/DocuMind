from app.ai.llm import LLMError
from app.config import settings
from app.routers import chat as chat_router


def test_file_over_the_size_limit_is_rejected(client, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_mb", 1)
    big = b"a" * (2 * 1024 * 1024)
    response = client.post("/documents", files={"file": ("big.txt", big, "text/plain")})
    assert response.status_code == 413


def test_empty_file_is_rejected(client):
    response = client.post("/documents", files={"file": ("empty.txt", b"", "text/plain")})
    assert response.status_code == 400
    assert response.json()["detail"] == "The file is empty"


def test_llm_failure_returns_502(client, monkeypatch):
    def broken(question, chunks):
        raise LLMError("boom")

    monkeypatch.setattr(chat_router, "answer_question", broken)
    response = client.post("/chat", json={"question": "anything"})
    assert response.status_code == 502