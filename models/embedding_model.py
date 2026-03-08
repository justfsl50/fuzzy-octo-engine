"""Shared sentence-transformer embedding model loader."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable, List

from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Load and cache embedding model for process lifetime."""
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> List[float]:
    """Embed a single text string."""
    vector = get_model().encode(text, normalize_embeddings=True)
    return vector.tolist()


def embed_texts(texts: Iterable[str]) -> List[List[float]]:
    """Embed multiple text strings in one batch."""
    text_list = list(texts)
    if not text_list:
        return []
    vectors = get_model().encode(text_list, normalize_embeddings=True)
    return vectors.tolist()


def initialize_embedding_model() -> None:
    """Warm model at startup to avoid first-request loading penalty."""
    get_model()
