"""Chroma vector database integration."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import chromadb
from chromadb.api.models.Collection import Collection

from models.embedding_model import embed_text, embed_texts

COLLECTION_NAME = "file_index"


@lru_cache(maxsize=1)
def get_chroma_client(storage_path: str = ".chroma") -> chromadb.PersistentClient:
    """Initialize and cache a persistent Chroma client."""
    Path(storage_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=storage_path)


@lru_cache(maxsize=1)
def get_collection(name: str = COLLECTION_NAME) -> Collection:
    """Get or create the main collection once per process."""
    return get_chroma_client().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def _to_doc_text(file_name: str, extracted_text: Optional[str] = None) -> str:
    if extracted_text:
        return f"{file_name}\n{extracted_text}"
    return file_name


def upsert_file_vectors(
    file_paths: Iterable[str],
    file_names: Iterable[str],
    extracted_texts: Optional[Iterable[Optional[str]]] = None,
) -> None:
    """Upsert vectors for files using names and optional extracted text."""
    paths = [str(Path(path).resolve()) for path in file_paths]
    names = list(file_names)

    if extracted_texts is None:
        texts = [None] * len(paths)
    else:
        texts = list(extracted_texts)

    if not paths:
        return

    if not (len(paths) == len(names) == len(texts)):
        raise ValueError("file_paths, file_names, and extracted_texts must have the same length")

    documents = [_to_doc_text(name, text) for name, text in zip(names, texts)]
    embeddings = embed_texts(documents)
    metadatas = [{"path": path, "name": name} for path, name in zip(paths, names)]

    get_collection().upsert(
        ids=paths,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def upsert_single_file_vector(
    file_path: str,
    file_name: str,
    extracted_text: Optional[str] = None,
) -> None:
    """Convenience function for incremental single-file upsert."""
    path = str(Path(file_path).resolve())
    document = _to_doc_text(file_name, extracted_text)
    get_collection().upsert(
        ids=[path],
        embeddings=[embed_text(document)],
        documents=[document],
        metadatas=[{"path": path, "name": file_name}],
    )


def delete_file_vectors(file_paths: Iterable[str]) -> None:
    """Delete vectors by file path ids."""
    ids = [str(Path(path).resolve()) for path in file_paths]
    if ids:
        get_collection().delete(ids=ids)


def query_files(query_text: str, top_k: int = 5) -> dict:
    """Query top-k nearest files."""
    query_embedding = embed_text(query_text)
    return get_collection().query(query_embeddings=[query_embedding], n_results=top_k)


def initialize_vector_db() -> None:
    """Warm vector DB collection at startup so first query is low-latency."""
    get_collection()
