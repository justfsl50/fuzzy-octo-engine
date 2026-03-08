"""Skill for searching indexed files and returning top matches."""

from __future__ import annotations

from mcp.search_server import search_files


def run(query: str, limit: int = 5) -> list[dict[str, str | int]]:
    matches = search_files(query=query, limit=limit)
    return matches[:limit]
