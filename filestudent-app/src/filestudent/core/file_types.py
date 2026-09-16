"""Detection du type d'un fichier depose dans l'application (ticket APP-02)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class FileKind(Enum):
    PDF = "pdf"
    IMAGE = "image"
    ARCHIVE = "archive"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


_LABELS = {
    FileKind.PDF: "PDF",
    FileKind.IMAGE: "Image",
    FileKind.ARCHIVE: "Archive",
    FileKind.DOCUMENT: "Document",
    FileKind.UNKNOWN: "Inconnu",
}

_EXTENSION_MAP: dict[str, FileKind] = {
    ".pdf": FileKind.PDF,
    ".png": FileKind.IMAGE,
    ".jpg": FileKind.IMAGE,
    ".jpeg": FileKind.IMAGE,
    ".webp": FileKind.IMAGE,
    ".bmp": FileKind.IMAGE,
    ".tif": FileKind.IMAGE,
    ".tiff": FileKind.IMAGE,
    ".tgz": FileKind.ARCHIVE,
    ".zip": FileKind.ARCHIVE,
    ".docx": FileKind.DOCUMENT,
    ".odt": FileKind.DOCUMENT,
    ".txt": FileKind.DOCUMENT,
    ".pptx": FileKind.DOCUMENT,
    ".xlsx": FileKind.DOCUMENT,
}


def detect_file_kind(path: str) -> FileKind:
    """Determine le type d'un fichier d'apres son nom (extension)."""
    name = Path(path).name.lower()
    if name.endswith(".tar.gz"):
        return FileKind.ARCHIVE
    suffix = Path(name).suffix
    return _EXTENSION_MAP.get(suffix, FileKind.UNKNOWN)


def label_for(kind: FileKind) -> str:
    """Libelle affichable en francais pour un type de fichier."""
    return _LABELS[kind]
