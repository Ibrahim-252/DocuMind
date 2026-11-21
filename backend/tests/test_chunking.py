from app.ai.chunking import split_pages


def test_empty_input_gives_no_chunks():
    assert split_pages([]) == []
    assert split_pages([(1, "   \n\n  ")]) == []


def test_short_text_is_one_chunk_with_page_number():
    chunks = split_pages([(3, "A short paragraph.")])
    assert len(chunks) == 1
    assert chunks[0]["page"] == 3
    assert chunks[0]["index"] == 0


def test_long_text_never_exceeds_size():
    text = ("This is a sentence about internships and regulations. " * 200).strip()
    chunks = split_pages([(1, text)], size=800, overlap=150)
    assert len(chunks) > 1
    assert all(len(c["text"]) <= 800 for c in chunks)
    assert [c["index"] for c in chunks] == list(range(len(chunks)))


def test_text_without_spaces_is_still_cut():
    chunks = split_pages([(1, "x" * 2000)], size=800)
    assert all(len(c["text"]) <= 800 for c in chunks)


def test_pages_keep_their_own_numbers():
    chunks = split_pages([(1, "First page text."), (5, "Fifth page text.")])
    assert [c["page"] for c in chunks] == [1, 5]
