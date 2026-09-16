"""Extraction de texte depuis un PDF, un DOCX ou un fichier texte.

Utilise par les modules IA (detection de texte genere et comparaison de
documents, tickets APP-12 et APP-13).
"""

from __future__ import annotations

import os
from pathlib import Path


def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()

    if os.path.getsize(path) == 0:
        raise ValueError(f"{Path(path).name} : fichier vide (0 octet), rien a analyser.")

    if suffix == ".pdf":
        import pymupdf

        try:
            with pymupdf.open(path) as doc:
                return "\n\n".join(page.get_text() for page in doc)
        except Exception as exc:
            raise ValueError(
                f"PDF illisible (corrompu) : {Path(path).name}."
            ) from exc

    if suffix == ".docx":
        import docx

        try:
            document = docx.Document(path)
        except Exception as exc:
            raise ValueError(
                f"Fichier Word illisible (vide ou corrompu) : {Path(path).name}. "
                "Ouvrez-le dans Word et enregistrez-le avant de reessayer."
            ) from exc
        return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())

    if suffix == ".txt":
        return Path(path).read_text(encoding="utf-8", errors="replace")

    raise ValueError(
        f"Format non pris en charge pour l'extraction de texte : {Path(path).name} "
        "(formats geres : .pdf, .docx, .txt)"
    )
