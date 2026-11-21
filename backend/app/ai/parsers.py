from pathlib import Path

from pypdf import PdfReader


def extract_pages(path: str) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] for a PDF or TXT file. Empty pages are skipped."""
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(path)
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append((number, text))
        return pages
    if suffix == ".txt":
        text = Path(path).read_text(encoding="utf-8", errors="ignore").strip()
        return [(1, text)] if text else []
    raise ValueError(f"Unsupported file type: {suffix}")
