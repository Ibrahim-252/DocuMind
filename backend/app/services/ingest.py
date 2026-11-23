import logging

from sqlalchemy.orm import Session

from app.ai.chunking import split_pages
from app.ai.embeddings import embed_texts
from app.ai.parsers import extract_pages
from app.config import settings
from app.db import SessionLocal
from app.models import Chunk, Document

logger = logging.getLogger("documind.ingest")


def ingest_document(db: Session, document_id: int) -> None:
    """Read a stored document, split it, embed the pieces and save them."""
    document = db.get(Document, document_id)
    if document is None:
        return
    try:
        document.status = "processing"
        document.error_message = None
        db.commit()

        pieces = split_pages(
            extract_pages(document.stored_path), size=settings.chunk_size, overlap=settings.chunk_overlap
        )
        if not pieces:
            raise ValueError("No readable text found (scanned PDFs are not supported).")
        vectors = embed_texts([p["text"] for p in pieces])

        db.add_all(
            Chunk(
                document_id=document.id,
                chunk_index=piece["index"],
                page_number=piece["page"],
                content=piece["text"],
                embedding=vector,
            )
            for piece, vector in zip(pieces, vectors, strict=True)
        )
        document.status = "ready"
        db.commit()
    except Exception as exc:
        logger.exception("Ingest failed for document %s", document_id)
        db.rollback()
        failed = db.get(Document, document_id)
        if failed is not None:
            failed.status = "failed"
            failed.error_message = str(exc)[:500]
            db.commit()


def run_ingest(document_id: int) -> None:
    """Background-task entry point. Opens its OWN session: the request session is closed."""
    with SessionLocal() as db:
        ingest_document(db, document_id)
