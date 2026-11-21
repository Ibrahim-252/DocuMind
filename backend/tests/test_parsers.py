import pytest
from pypdf import PdfWriter

from app.ai.parsers import extract_pages


def test_txt_file_is_one_page(tmp_path):
    path = tmp_path / "notes.txt"
    path.write_text("Line one.\nLine two.", encoding="utf-8")
    assert extract_pages(str(path)) == [(1, "Line one.\nLine two.")]


def test_empty_txt_file_gives_no_pages(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("   \n", encoding="utf-8")
    assert extract_pages(str(path)) == []


def test_pdf_without_text_gives_no_pages(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    writer.add_blank_page(width=200, height=200)
    path = tmp_path / "blank.pdf"
    with path.open("wb") as handle:
        writer.write(handle)
    assert extract_pages(str(path)) == []


def test_unsupported_file_type_raises(tmp_path):
    path = tmp_path / "notes.docx"
    path.write_bytes(b"not supported")
    with pytest.raises(ValueError):
        extract_pages(str(path))
