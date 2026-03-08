"""Search MCP server with simple in-memory indexing."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SearchIndex:
    files: dict[str, str] = field(default_factory=dict)


_INDEX = SearchIndex()


def index_files(root_directory: str, glob_pattern: str = "**/*") -> int:
    root = Path(root_directory).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Directory not found: {root}")

    _INDEX.files.clear()
    for candidate in root.glob(glob_pattern):
        if candidate.is_file():
            content = candidate.read_text(encoding="utf-8", errors="ignore")
            _INDEX.files[str(candidate)] = content

    return len(_INDEX.files)


def update_index(path: str) -> bool:
    target = Path(path).expanduser().resolve()
    key = str(target)

    if not target.exists() or not target.is_file():
        if key in _INDEX.files:
            del _INDEX.files[key]
            return True
        return False

    _INDEX.files[key] = target.read_text(encoding="utf-8", errors="ignore")
    return True


def search_files(query: str, limit: int = 10) -> list[dict[str, str | int]]:
    if not query.strip():
        return []

    lowered_query = query.lower()
    scored: list[tuple[int, str]] = []

    for file_path, content in _INDEX.files.items():
        lowered_content = content.lower()
        score = lowered_content.count(lowered_query)
        if score > 0:
            scored.append((score, file_path))

    scored.sort(key=lambda item: item[0], reverse=True)
    results = []
    for score, file_path in scored[:limit]:
        results.append({"path": file_path, "score": score})

    return results
