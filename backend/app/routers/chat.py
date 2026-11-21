from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.llm import LLMError
from app.db import get_db
from app.schemas import ChatRequest, ChatResponse, SourceOut
from app.services.rag import answer_question, search_chunks

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, db: Session = Depends(get_db)):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="The question is empty")

    chunks = search_chunks(db, question)
    try:
        answer = answer_question(question, chunks)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail="The AI service is unreachable") from exc

    sources = [
        SourceOut(
            document_id=c["document_id"],
            filename=c["filename"],
            page=c["page"],
            snippet=c["text"][:200],
        )
        for c in chunks
    ]
    return ChatResponse(answer=answer, sources=sources)
