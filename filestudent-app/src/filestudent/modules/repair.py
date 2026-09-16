"""Module Reparer PDF (equivalent Repair d'iLovePDF).

PyMuPDF est nettement plus tolerant qu'un lecteur PDF strict envers les
fichiers legerement corrompus ou mal formes (flux manquants, references
cassees, structure non conforme). Ouvrir puis reenregistrer avec nettoyage
recupere souvent un PDF qu'un lecteur classique refuse d'ouvrir.
"""

from __future__ import annotations

from typing import Any

import pymupdf

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result


def run(files: list[str], **_options: Any) -> Result:
    created: list[str] = []
    details: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.PDF:
            notes.append(f"{path} : ignore (pas un PDF).")
            continue
        try:
            doc = pymupdf.open(path)
            page_count = len(doc)
            out = sibling_path(path, suffix="_repare")
            doc.save(out, garbage=4, deflate=True, clean=True)
            doc.close()
        except Exception as exc:
            notes.append(f"{path} : irreparable ({exc}).")
            continue
        created.append(out)
        details.append(f"{out} : {page_count} page(s) recuperee(s).")

    if not created:
        detail = "\n".join(notes) if notes else "aucun PDF exploitable."
        raise ValueError(f"Aucun fichier repare.\n{detail}")

    message = "\n".join(details)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
