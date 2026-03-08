"""Filesystem MCP server helpers."""

from __future__ import annotations

from pathlib import Path
import shutil

from shared.safety import ConfirmationGate, ConfirmationRequest


def list_files(directory: str = ".", recursive: bool = False) -> list[str]:
    base = Path(directory).expanduser().resolve()
    if not base.exists() or not base.is_dir():
        raise FileNotFoundError(f"Directory not found: {base}")

    if recursive:
        return sorted(str(path) for path in base.rglob("*") if path.is_file())

    return sorted(str(path) for path in base.iterdir() if path.is_file())


def open_file(path: str, encoding: str = "utf-8") -> str:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    return file_path.read_text(encoding=encoding)


def move_file(source: str, destination: str, user_confirmation: str | None = None) -> str:
    source_path = Path(source).expanduser().resolve()
    destination_path = Path(destination).expanduser().resolve()

    if not source_path.exists() or not source_path.is_file():
        raise FileNotFoundError(f"File not found: {source_path}")

    request = ConfirmationRequest(
        action="move_file",
        target=f"{source_path} -> {destination_path}",
        reason="Moving files can overwrite destination content.",
    )
    ConfirmationGate.require_confirmation(request, user_confirmation)

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    moved = shutil.move(str(source_path), str(destination_path))
    return str(Path(moved).resolve())


def create_folder(path: str) -> str:
    folder_path = Path(path).expanduser().resolve()
    folder_path.mkdir(parents=True, exist_ok=True)
    return str(folder_path)


def delete_file(path: str, user_confirmation: str | None = None) -> str:
    file_path = Path(path).expanduser().resolve()
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    request = ConfirmationRequest(
        action="delete_file",
        target=str(file_path),
        reason="Deleting a file is irreversible.",
    )
    ConfirmationGate.require_confirmation(request, user_confirmation)

    file_path.unlink()
    return str(file_path)
