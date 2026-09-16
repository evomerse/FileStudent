"""Module Diviser et organiser un PDF (equivalent du Split / Organize
d'iLovePDF).

Quatre actions au choix : extraire des pages precises, supprimer des pages
precises, reorganiser toutes les pages dans un nouvel ordre, ou diviser
chaque page en un fichier separe.
"""

from __future__ import annotations

from typing import Any

from pypdf import PdfReader, PdfWriter

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result

ACTIONS = [
    "Extraire des pages",
    "Supprimer des pages",
    "Reorganiser les pages",
    "Diviser chaque page",
]


def _parse_ranges(spec: str, page_count: int) -> set[int]:
    """Convertit "1-3,5,8-10" en indices de pages 0-based, valides."""
    spec = spec.strip()
    if not spec:
        raise ValueError("Indiquez les pages concernees, par exemple 1-3,5,8-10.")

    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            bounds = part.split("-", 1)
            try:
                start, end = int(bounds[0]), int(bounds[1])
            except ValueError as exc:
                raise ValueError(f"Plage de pages invalide : {part}") from exc
            if start < 1 or end < start:
                raise ValueError(f"Plage de pages invalide : {part}")
            for p in range(start, min(end, page_count) + 1):
                indices.add(p - 1)
        else:
            try:
                p = int(part)
            except ValueError as exc:
                raise ValueError(f"Numero de page invalide : {part}") from exc
            if p < 1 or p > page_count:
                raise ValueError(f"La page {p} n'existe pas (document de {page_count} page(s)).")
            indices.add(p - 1)

    if not indices:
        raise ValueError("Aucune page valide dans la selection.")
    return indices


def _parse_order(spec: str, page_count: int) -> list[int]:
    """Convertit "3,1,2,4" en indices 0-based dans le nouvel ordre : chaque
    page du document doit apparaitre exactement une fois."""
    spec = spec.strip()
    if not spec:
        raise ValueError("Indiquez le nouvel ordre des pages, par exemple 3,1,2,4.")

    order: list[int] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            p = int(part)
        except ValueError as exc:
            raise ValueError(f"Numero de page invalide : {part}") from exc
        if p < 1 or p > page_count:
            raise ValueError(f"La page {p} n'existe pas (document de {page_count} page(s)).")
        order.append(p - 1)

    if sorted(order) != list(range(page_count)):
        raise ValueError(
            f"L'ordre doit contenir chaque page de 1 a {page_count}, exactement une fois."
        )
    return order


def _write_subset(reader: PdfReader, indices: list[int], out: str) -> None:
    writer = PdfWriter()
    for i in indices:
        writer.add_page(reader.pages[i])
    with open(out, "wb") as fh:
        writer.write(fh)


def run(files: list[str], action: str = "Extraire des pages", pages: str = "", **_o: Any) -> Result:
    if action not in ACTIONS:
        raise ValueError(f"Action inconnue : {action}")

    created: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.PDF:
            notes.append(f"{path} : ignore (pas un PDF).")
            continue

        reader = PdfReader(path)
        n = len(reader.pages)

        if action == "Diviser chaque page":
            for i in range(n):
                out = sibling_path(path, suffix=f"_page{i + 1}")
                _write_subset(reader, [i], out)
                created.append(out)
            continue

        if action == "Reorganiser les pages":
            order = _parse_order(pages, n)
            out = sibling_path(path, suffix="_reorganise")
            _write_subset(reader, order, out)
            created.append(out)
            continue

        indices = _parse_ranges(pages, n)
        if action == "Extraire des pages":
            keep = sorted(indices)
            suffix = "_extrait"
        else:  # Supprimer des pages
            keep = [i for i in range(n) if i not in indices]
            suffix = "_sans_pages"

        if not keep:
            notes.append(f"{path} : cette operation ne laisserait aucune page, ignore.")
            continue

        out = sibling_path(path, suffix=suffix)
        _write_subset(reader, keep, out)
        created.append(out)

    if not created:
        detail = "\n".join(notes) if notes else "aucun PDF exploitable parmi les fichiers deposes."
        raise ValueError(f"Aucun fichier produit.\n{detail}")

    message = f"{len(created)} fichier(s) cree(s) :\n" + "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
