import pytest

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


SENTENCE = "The compulsory internship lasts a total of forty working days. "


def test_small_paragraphs_are_merged_into_one_chunk():
    chunks = split_pages([(1, "First paragraph.\n\nSecond paragraph.\n\nThird paragraph.")])
    assert len(chunks) == 1
    assert "First" in chunks[0]["text"] and "Third" in chunks[0]["text"]


def test_long_text_is_cut_at_sentence_ends():
    chunks = split_pages([(1, SENTENCE * 100)], overlap=0)
    assert all(c["text"].endswith(".") for c in chunks)


def test_every_next_chunk_starts_with_overlap():
    chunks = split_pages([(1, SENTENCE * 60)], size=800, overlap=150)
    assert len(chunks) > 2
    for previous, current in zip(chunks, chunks[1:], strict=False):
        first_words = " ".join(current["text"].split(" ")[:4])
        assert first_words in previous["text"]


def test_overlap_never_crosses_pages():
    chunks = split_pages([(1, SENTENCE * 20), (2, "Page two starts here.")])
    assert chunks[-1] == {"page": 2, "index": len(chunks) - 1, "text": "Page two starts here."}


def test_bad_settings_raise():
    with pytest.raises(ValueError):
        split_pages([(1, "text")], size=100, overlap=100)
    with pytest.raises(ValueError):
        split_pages([(1, "text")], size=0)
