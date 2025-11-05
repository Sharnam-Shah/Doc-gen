import hashlib
import os
from typing import Iterable, List

from sentence_transformers import SentenceTransformer


_model_singleton: SentenceTransformer | None = None


def load_embedding_model(model_name: str) -> SentenceTransformer:
    global _model_singleton
    if _model_singleton is None:
        _model_singleton = SentenceTransformer(model_name)
    return _model_singleton


def file_md5(path: str) -> str:
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def normalize_text(text: str) -> str:
    # Minimal normalization suitable for sentence-transformers
    return " ".join(text.split())


def batch_encode(model: SentenceTransformer, texts: Iterable[str], batch_size: int = 64) -> List[List[float]]:
    # Use convert_to_numpy=False for list-of-lists output compatible with qdrant-client
    return model.encode(list(texts), batch_size=batch_size, show_progress_bar=True, normalize_embeddings=True).tolist()


