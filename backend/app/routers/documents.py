from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Document
from app.schemas import DocumentOut
from app.services.ingest import run_ingest

router = APIRouter(tags=["documents"])
ALLOWED_SUFFIXES = {".pdf", ".txt"}


@router.post("/documents", response_model=DocumentOut, status_code=202)
def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    original_name = Path(file.filename or "").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are accepted")

    limit = settings.max_upload_mb * 1024 * 1024
    data = file.file.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail=f"File is larger than {settings.max_upload_mb} MB")
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{uuid4().hex}{suffix}"  # never trust the client's file name on disk
    stored_path.write_bytes(data)

    document = Document(filename=original_name, stored_path=str(stored_path), status="pending")
    db.add(document)
    db.commit()
    db.refresh(document)
    background.add_task(run_ingest, document.id)
    return document


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.id.desc())).all()


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    Path(document.stored_path).unlink(missing_ok=True)
    db.delete(document)  # chunks are removed by ON DELETE CASCADE
    db.commit()
    return Response(status_code=204)
