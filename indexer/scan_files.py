"""File system scanning and SQLite persistence helpers."""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Iterator, Optional

DEFAULT_SCAN_DIRS = ("Documents", "Desktop", "Downloads", "Projects")


@dataclass(frozen=True)
class FileMetadata:
    """Metadata persisted for an indexed file."""

    name: str
    path: str
    extension: str
    size: int
    modified_date: str


def _utc_iso_from_epoch(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def create_connection(db_path: str = "index.db") -> sqlite3.Connection:
    """Open a SQLite connection configured for concurrent reads/writes."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def initialize_database(conn: sqlite3.Connection) -> None:
    """Create required schema if it does not exist."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            path TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            extension TEXT NOT NULL,
            size INTEGER NOT NULL,
            modified_date TEXT NOT NULL,
            indexed_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_name ON files(name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_files_extension ON files(extension);")
    conn.commit()


@lru_cache(maxsize=1)
def get_db_connection(db_path: str = "index.db") -> sqlite3.Connection:
    """Load SQLite connection once at startup for lower latency on updates."""
    conn = create_connection(db_path)
    initialize_database(conn)
    return conn


def extract_file_metadata(file_path: Path) -> Optional[FileMetadata]:
    """Return metadata for a file path, skipping unreadable or non-file entries."""
    try:
        if not file_path.is_file():
            return None
        stat = file_path.stat()
    except (FileNotFoundError, PermissionError, OSError):
        return None

    return FileMetadata(
        name=file_path.name,
        path=str(file_path.resolve()),
        extension=file_path.suffix.lower(),
        size=stat.st_size,
        modified_date=_utc_iso_from_epoch(stat.st_mtime),
    )


def iter_scan_roots(
    home: Optional[Path] = None,
    roots: Iterable[str] = DEFAULT_SCAN_DIRS,
) -> Iterator[Path]:
    """Yield absolute paths for all configured scan roots that exist."""
    base = Path.home() if home is None else home
    for root in roots:
        candidate = base / root
        if candidate.exists() and candidate.is_dir():
            yield candidate


def scan_files_recursively(
    home: Optional[Path] = None,
    roots: Iterable[str] = DEFAULT_SCAN_DIRS,
) -> Iterator[FileMetadata]:
    """Recursively walk scan roots and yield metadata for each discovered file."""
    for root in iter_scan_roots(home=home, roots=roots):
        for dirpath, _, filenames in os.walk(root):
            for filename in filenames:
                metadata = extract_file_metadata(Path(dirpath) / filename)
                if metadata:
                    yield metadata


def upsert_file_record(conn: sqlite3.Connection, metadata: FileMetadata) -> None:
    """Insert or update a file metadata row."""
    conn.execute(
        """
        INSERT INTO files(path, name, extension, size, modified_date, indexed_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(path) DO UPDATE SET
            name=excluded.name,
            extension=excluded.extension,
            size=excluded.size,
            modified_date=excluded.modified_date,
            indexed_at=datetime('now');
        """,
        (metadata.path, metadata.name, metadata.extension, metadata.size, metadata.modified_date),
    )


def delete_file_record(conn: sqlite3.Connection, file_path: str) -> None:
    """Delete a file row by path."""
    conn.execute("DELETE FROM files WHERE path = ?;", (str(Path(file_path).resolve()),))


def persist_scan(conn: sqlite3.Connection, metadata_iter: Iterable[FileMetadata]) -> int:
    """Persist a metadata iterable in a single transaction and return count."""
    count = 0
    with conn:
        for metadata in metadata_iter:
            upsert_file_record(conn, metadata)
            count += 1
    return count


def full_scan_and_persist(conn: sqlite3.Connection, home: Optional[Path] = None) -> int:
    """Run recursive scan for default roots and persist results to SQLite."""
    return persist_scan(conn, scan_files_recursively(home=home))


def update_index(conn: sqlite3.Connection, file_path: str) -> Optional[FileMetadata]:
    """Incrementally update index for a path. Deletes if missing, upserts if present."""
    metadata = extract_file_metadata(Path(file_path))
    with conn:
        if metadata is None:
            delete_file_record(conn, file_path)
            return None
        upsert_file_record(conn, metadata)
        return metadata
