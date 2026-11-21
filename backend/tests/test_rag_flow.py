from tests.conftest import upload_text

REGULATION = (
    "The compulsory internship lasts thirty working days.\n\n"
    "Students must submit the internship report within two weeks after the internship ends."
)


def test_upload_becomes_ready_and_chat_returns_sources(client):
    upload = upload_text(client, "regulation.txt", REGULATION)
    assert upload.status_code == 202

    documents = client.get("/documents").json()
    assert [d["status"] for d in documents] == ["ready"]

    answer = client.post("/chat", json={"question": "How long does the internship last?"})
    assert answer.status_code == 200
    body = answer.json()
    assert body["sources"], "expected at least one source"
    assert body["sources"][0]["filename"] == "regulation.txt"
    assert body["sources"][0]["page"] == 1


def test_question_with_no_match_says_not_found(client):
    upload_text(client, "regulation.txt", REGULATION)
    answer = client.post("/chat", json={"question": "zzzz qqqq xxxx"}).json()
    assert answer["sources"] == []
    assert "could not find" in answer["answer"].lower()


def test_chat_without_any_document_says_not_found(client):
    answer = client.post("/chat", json={"question": "anything at all"})
    assert answer.status_code == 200
    assert answer.json()["sources"] == []


def test_invalid_file_type_and_empty_question(client):
    assert upload_text(client, "malware.exe", "nope").status_code == 400
    assert client.post("/chat", json={"question": "   "}).status_code == 400


def test_deleting_a_document_removes_it_and_its_chunks(client):
    upload_text(client, "regulation.txt", REGULATION)
    document_id = client.get("/documents").json()[0]["id"]

    assert client.delete(f"/documents/{document_id}").status_code == 204
    assert client.get("/documents").json() == []
    assert client.delete(f"/documents/{document_id}").status_code == 404
    assert client.post("/chat", json={"question": "internship"}).json()["sources"] == []


def test_file_without_readable_text_fails_gracefully(client):
    assert upload_text(client, "blank.txt", "   \n  ").status_code == 202
    document = client.get("/documents").json()[0]
    assert document["status"] == "failed"
    assert "No readable text" in document["error_message"]
