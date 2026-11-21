import re
from collections.abc import Iterator


def _units(text: str, size: int) -> Iterator[str]:
    """Break text into pieces that are each at most `size` characters."""
    for paragraph in re.split(r"\n\s*\n", text):
        paragraph = re.sub(r"\s+", " ", paragraph).strip()
        if not paragraph:
            continue
        if len(paragraph) <= size:
            yield paragraph
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            while len(sentence) > size:
                cut = sentence.rfind(" ", 0, size)
                cut = cut if cut > 0 else size
                yield sentence[:cut].strip()
                sentence = sentence[cut:].strip()
            if sentence:
                yield sentence


def _tail(text: str, overlap: int) -> str:
    """The last ~overlap characters of text, starting at a word boundary."""
    if overlap <= 0 or len(text) <= overlap:
        return ""
    piece = text[-overlap:]
    space = piece.find(" ")
    return piece[space + 1 :] if space != -1 else ""


def split_pages(pages: list[tuple[int, str]], size: int = 800, overlap: int = 150) -> list[dict]:
    """Split page texts into chunks of at most `size` characters.

    Each chunk is {"page": int, "index": int, "text": str}. Consecutive chunks on the
    same page share a short overlap so sentences cut at a boundary are not lost.

    Pieces are kept to `size - overlap - 1` characters, so the overlap from the previous
    chunk plus a new piece always fits within `size` and the overlap is never dropped.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be >= 0 and smaller than size")

    piece_size = max(1, size - overlap - 1)
    chunks: list[dict] = []
    index = 0
    for page_number, text in pages:
        current = ""
        for unit in _units(text, piece_size):
            if not current:
                current = unit
            elif len(current) + 1 + len(unit) <= size:
                current = f"{current} {unit}"
            else:
                chunks.append({"page": page_number, "index": index, "text": current})
                index += 1
                tail = _tail(current, overlap)
                if tail and len(tail) + 1 + len(unit) <= size:
                    current = f"{tail} {unit}"
                else:
                    current = unit
        if current.strip():
            chunks.append({"page": page_number, "index": index, "text": current})
            index += 1
    return chunks
