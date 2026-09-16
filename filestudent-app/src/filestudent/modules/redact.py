"""Module Censurer PDF (equivalent Redact PDF d'iLovePDF).

Recherche un texte dans chaque page et le censure reellement : le texte
recouvert par le cache noir est supprime du flux du PDF, pas seulement
masque visuellement, via le mecanisme de redaction natif de PyMuPDF
(page.apply_redactions).
"""

from __future__ import annotations

from typing import Any

import pymupdf

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result


def run(files: list[str], search_text: str = "", **_options: Any) -> Result:
    search_text = search_text.strip()
    if not search_text:
        raise ValueError("Indiquez le texte a censurer.")

    created: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.PDF:
            notes.append(f"{path} : ignore (pas un PDF).")
            continue

        doc = pymupdf.open(path)
        total_hits = 0
        for page in doc:
            hits = page.search_for(search_text)
            for rect in hits:
                page.add_redact_annot(rect, fill=(0, 0, 0))
            if hits:
                page.apply_redactions()
            total_hits += len(hits)

        if total_hits == 0:
            doc.close()
            notes.append(f"{path} : texte introuvable, ignore.")
            continue

        out = sibling_path(path, suffix="_censure")
        doc.save(out)
        doc.close()
        created.append(out)
        notes.append(f"{out} : {total_hits} occurrence(s) censuree(s).")

    if not created:
        detail = "\n".join(notes) if notes else "aucun PDF exploitable."
        raise ValueError(f"Aucune censure appliquee.\n{detail}")

    return Result(message="\n".join(notes), paths=created)
