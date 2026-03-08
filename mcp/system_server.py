"""System health MCP server backed by psutil."""

from __future__ import annotations

import psutil


def cpu_usage(interval_seconds: float = 0.1) -> float:
    return psutil.cpu_percent(interval=interval_seconds)


def memory_usage() -> dict[str, int | float]:
    memory = psutil.virtual_memory()
    return {
        "total": memory.total,
        "available": memory.available,
        "used": memory.used,
        "percent": memory.percent,
    }


def disk_usage(path: str = "/") -> dict[str, int | float]:
    disk = psutil.disk_usage(path)
    return {
        "total": disk.total,
        "used": disk.used,
        "free": disk.free,
        "percent": disk.percent,
    }
