import logging
import time

from fastapi import FastAPI, Request

from app.config import settings
from app.routers import chat, documents

logging.basicConfig(level=settings.log_level.upper(), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("documind.api")

app = FastAPI(
    title="DocuMind API",
    version="0.1.0",
    description=(
        "RAG document assistant. Upload PDF or TXT documents, then ask questions "
        "and get answers with file and page sources."
    ),
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - started) * 1000
    logger.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(documents.router)
app.include_router(chat.router)
