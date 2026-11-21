"""HTTP client for the DocuMind API."""

import os

import requests

API_URL = (os.getenv("API_URL") or "http://localhost:8000").strip().rstrip("/")


class ApiError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def _request(method: str, path: str, *, read_timeout: int = 15, **kwargs):
    try:
        response = requests.request(
            method, f"{API_URL}{path}", timeout=(3, read_timeout), **kwargs
        )
    except requests.Timeout as exc:
        raise ApiError(0, "The backend took too long to respond.") from exc
    except requests.RequestException as exc:
        raise ApiError(0, "Cannot connect to the DocuMind backend.") from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
        except ValueError:
            payload = None
        detail = payload.get("detail") if isinstance(payload, dict) else None
        message = detail if isinstance(detail, str) else f"Request failed (HTTP {response.status_code})."
        raise ApiError(response.status_code, message)

    if response.status_code == 204:
        return None
    try:
        return response.json()
    except ValueError as exc:
        raise ApiError(response.status_code, "The backend returned an unreadable response.") from exc


def list_documents():
    return _request("GET", "/documents")


def upload_document(filename: str, content: bytes, mime: str):
    return _request(
        "POST", "/documents", read_timeout=120, files={"file": (filename, content, mime)}
    )


def delete_document(document_id: int):
    _request("DELETE", f"/documents/{document_id}")


def ask(question: str):
    return _request("POST", "/chat", read_timeout=120, json={"question": question})
