"""Module Securite PDF (equivalent Protect/Unlock d'iLovePDF).

Ajoute ou retire un mot de passe de lecture sur un PDF.
"""

from __future__ import annotations

from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf._encryption import PasswordType

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result

ACTIONS = ["Proteger", "Deverrouiller"]


def _protect(path: str, password: str) -> str:
    reader = PdfReader(path)
    if reader.is_encrypted:
        raise ValueError(f"{path} : deja protege par un mot de passe, ignore.")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    out = sibling_path(path, suffix="_protege")
    with open(out, "wb") as fh:
        writer.write(fh)
    return out


def _unlock(path: str, password: str) -> str:
    reader = PdfReader(path)
    if reader.is_encrypted:
        result = reader.decrypt(password)
        if result == PasswordType.NOT_DECRYPTED:
            raise ValueError(f"{path} : mot de passe incorrect, ignore.")
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    out = sibling_path(path, suffix="_deverrouille")
    with open(out, "wb") as fh:
        writer.write(fh)
    return out


def run(files: list[str], action: str = "Proteger", password: str = "", **_o: Any) -> Result:
    if action not in ACTIONS:
        raise ValueError(f"Action inconnue : {action}")
    if not password:
        raise ValueError("Indiquez un mot de passe.")

    created: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.PDF:
            notes.append(f"{path} : ignore (pas un PDF).")
            continue
        try:
            if action == "Proteger":
                created.append(_protect(path, password))
            else:
                created.append(_unlock(path, password))
        except ValueError as exc:
            notes.append(str(exc))

    if not created:
        detail = "\n".join(notes) if notes else "aucun PDF exploitable parmi les fichiers deposes."
        raise ValueError(f"Aucun fichier produit.\n{detail}")

    action_label = "protege(s)" if action == "Proteger" else "deverrouille(s)"
    message = f"{len(created)} fichier(s) {action_label} :\n" + "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
