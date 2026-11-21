import math
import re
import zlib
from functools import lru_cache

from app.config import settings

DIM = 384


@lru_cache(maxsize=1)
def _model():
    # Imported lazily so tests and the API start fast; the model loads once per process.
    from fastembed import TextEmbedding

    return TextEmbedding(model_name=settings.embedding_model)


def _fake_embed(text: str) -> list[float]:
    """Deterministic bag-of-words vector. Used in tests so no model download is needed."""
    vector = [0.0] * DIM
    for token in re.findall(r"\w+", text.lower()):
        vector[zlib.crc32(token.encode()) % DIM] += 1.0
    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    if settings.embedding_backend == "fake":
        return [_fake_embed(t) for t in texts]
    return [vector.tolist() for vector in _model().embed(texts, batch_size=32)]
