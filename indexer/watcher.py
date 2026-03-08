"""Watchdog-based filesystem watcher for incremental indexing."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from indexer.scan_files import get_db_connection, iter_scan_roots, update_index
from models.embedding_model import initialize_embedding_model
from vector.vector_db import delete_file_vectors, initialize_vector_db, upsert_single_file_vector


class IndexEventHandler(FileSystemEventHandler):
    """Handles create/modify/delete events and applies incremental updates."""

    def __init__(self, db_path: str = "index.db") -> None:
        self._conn = get_db_connection(db_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._upsert(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._upsert(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        delete_file_vectors([event.src_path])
        self._upsert(event.dest_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        update_index(self._conn, event.src_path)
        delete_file_vectors([event.src_path])

    def _upsert(self, file_path: str) -> None:
        metadata = update_index(self._conn, file_path)
        if metadata is None:
            delete_file_vectors([file_path])
            return
        upsert_single_file_vector(metadata.path, metadata.name)


def start_watcher(
    home: Optional[Path] = None,
    roots: Iterable[str] = ("Documents", "Desktop", "Downloads", "Projects"),
    db_path: str = "index.db",
) -> Observer:
    """Start observers for configured roots and return running observer."""
    # Warm shared clients once during startup.
    initialize_embedding_model()
    initialize_vector_db()

    event_handler = IndexEventHandler(db_path=db_path)
    observer = Observer()
    for root in iter_scan_roots(home=home, roots=roots):
        observer.schedule(event_handler, str(root), recursive=True)
    observer.start()
    return observer
