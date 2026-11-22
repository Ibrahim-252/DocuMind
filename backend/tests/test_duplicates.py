from tests.conftest import upload_text


def test_duplicate_filename_is_rejected(client):
    first = upload_text(client, "regulation.txt", "first version")
    second = upload_text(client, "Regulation.TXT", "second version")
    assert first.status_code == 202
    assert second.status_code == 409
    assert len(client.get("/documents").json()) == 1


def test_same_name_is_allowed_after_deleting_the_old_one(client):
    upload_text(client, "regulation.txt", "first version")
    document_id = client.get("/documents").json()[0]["id"]
    assert client.delete(f"/documents/{document_id}").status_code == 204
    assert upload_text(client, "regulation.txt", "second version").status_code == 202