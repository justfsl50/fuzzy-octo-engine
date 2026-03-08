"""Skill for locating and summarizing documents."""

from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from pathlib import Path

from mcp.filesystem_server import open_file
from skills.search_files import run as search_skill


def _read_pdf(path: Path) -> str:
    if find_spec("pypdf") is None:
        raise RuntimeError("pypdf is required to read PDF files.")

    pypdf = import_module("pypdf")
    reader = pypdf.PdfReader(str(path))
    return "\n".join((page.extract_text() or "") for page in reader.pages)


def _read_docx(path: Path) -> str:
    if find_spec("docx") is None:
        raise RuntimeError("python-docx is required to read DOCX files.")

    docx = import_module("docx")
    document = docx.Document(str(path))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _summarize(text: str, max_sentences: int = 4) -> str:
    sentences = [segment.strip() for segment in text.replace("\n", " ").split(".") if segment.strip()]
    if not sentences:
        return "No content found to summarize."
    return ". ".join(sentences[:max_sentences]) + "."


def run(query: str) -> dict[str, str]:
    matches = search_skill(query=query, limit=1)
    if not matches:
        return {"summary": "No matching document found.", "source": ""}

    source_path = Path(str(matches[0]["path"]))
    suffix = source_path.suffix.lower()

    if suffix == ".pdf":
        content = _read_pdf(source_path)
    elif suffix == ".docx":
        content = _read_docx(source_path)
    else:
        content = open_file(str(source_path))

    return {"summary": _summarize(content), "source": str(source_path)}
