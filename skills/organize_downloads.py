"""Skill to propose and optionally apply download organization actions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mcp.filesystem_server import create_folder, list_files, move_file
from shared.safety import ConfirmationGate, ConfirmationRequest


CATEGORY_RULES: dict[str, set[str]] = {
    "documents": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".md"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"},
    "archives": {".zip", ".tar", ".gz", ".7z", ".rar"},
    "audio": {".mp3", ".wav", ".flac", ".aac"},
    "video": {".mp4", ".mov", ".mkv", ".avi"},
    "apps": {".dmg", ".exe", ".msi", ".appimage", ".pkg"},
}


@dataclass
class MoveProposal:
    source: str
    destination: str
    category: str


def _category_for_extension(extension: str) -> str:
    ext = extension.lower()
    for category, known_extensions in CATEGORY_RULES.items():
        if ext in known_extensions:
            return category
    return "other"


def propose_moves(downloads_directory: str) -> list[MoveProposal]:
    root = Path(downloads_directory).expanduser().resolve()
    proposals: list[MoveProposal] = []

    for file_path in list_files(str(root), recursive=False):
        source = Path(file_path)
        category = _category_for_extension(source.suffix)
        destination = root / category / source.name
        proposals.append(
            MoveProposal(
                source=str(source),
                destination=str(destination),
                category=category,
            )
        )

    return proposals


def apply_moves(proposals: list[MoveProposal], user_confirmation: str | None = None) -> list[str]:
    request = ConfirmationRequest(
        action="apply_download_organization",
        target=f"{len(proposals)} files",
        reason="This will move files into categorized folders.",
    )
    ConfirmationGate.require_confirmation(request, user_confirmation)

    moved: list[str] = []
    for proposal in proposals:
        create_folder(str(Path(proposal.destination).parent))
        moved_path = move_file(
            source=proposal.source,
            destination=proposal.destination,
            user_confirmation=ConfirmationGate.CONFIRM_PHRASE,
        )
        moved.append(moved_path)

    return moved
