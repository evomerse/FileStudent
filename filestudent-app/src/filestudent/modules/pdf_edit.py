"""Module Rotation, filigrane, numerotation et rognage (equivalent Rotate/
Watermark/Page numbers/Crop d'iLovePDF).

Les quatre transformations sont independantes et se combinent : angle de
rotation (0 = aucune), marge a rogner (0 = aucune), texte de filigrane
(vide = aucun), numerotation des pages (case a cocher).
"""

from __future__ import annotations

from typing import Any

import pymupdf

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result

VALID_ANGLES = {"0", "90", "180", "270"}


def _crop(page: pymupdf.Page, percent: float) -> None:
    r = page.rect
    dx = r.width * percent / 100
    dy = r.height * percent / 100
    page.set_cropbox(pymupdf.Rect(r.x0 + dx, r.y0 + dy, r.x1 - dx, r.y1 - dy))


def _add_watermark(page: pymupdf.Page, text: str) -> None:
    max_width = page.rect.width * 0.8
    fontsize = 40.0
    while fontsize > 8 and pymupdf.get_text_length(text, fontsize=fontsize) > max_width:
        fontsize -= 2
    width = pymupdf.get_text_length(text, fontsize=fontsize)
    x = (page.rect.width - width) / 2
    y = page.rect.height / 2
    # PyMuPDF n'accepte que des rotations par 90 degres pour insert_text : le
    # filigrane est horizontal, centre, en gris clair semi-transparent.
    page.insert_text((x, y), text, fontsize=fontsize, color=(0.6, 0.6, 0.6), fill_opacity=0.35)


def _add_page_number(page: pymupdf.Page, index: int, total: int) -> None:
    text = f"{index} / {total}"
    fontsize = 9.0
    width = pymupdf.get_text_length(text, fontsize=fontsize)
    x = (page.rect.width - width) / 2
    y = page.rect.height - 30
    page.insert_text((x, y), text, fontsize=fontsize, color=(0.3, 0.3, 0.3))


def run(
    files: list[str],
    angle: str = "0",
    crop_percent: int = 0,
    watermark_text: str = "",
    page_numbers: bool = False,
    **_options: Any,
) -> Result:
    if angle not in VALID_ANGLES:
        raise ValueError(f"Angle de rotation invalide : {angle}")
    watermark_text = watermark_text.strip()
    angle_i = int(angle)
    crop_percent = max(0, min(45, int(crop_percent)))

    if angle_i == 0 and crop_percent == 0 and not watermark_text and not page_numbers:
        raise ValueError(
            "Choisissez au moins une transformation : rotation, rognage, "
            "filigrane ou numerotation."
        )

    created: list[str] = []
    notes: list[str] = []

    for path in files:
        if detect_file_kind(path) != FileKind.PDF:
            notes.append(f"{path} : ignore (pas un PDF).")
            continue

        doc = pymupdf.open(path)
        total = len(doc)
        for i, page in enumerate(doc, start=1):
            if crop_percent:
                _crop(page, crop_percent)
            if angle_i:
                page.set_rotation((page.rotation + angle_i) % 360)
            if watermark_text:
                _add_watermark(page, watermark_text)
            if page_numbers:
                _add_page_number(page, i, total)

        out = sibling_path(path, suffix="_modifie")
        doc.save(out)
        doc.close()
        created.append(out)

    if not created:
        detail = "\n".join(notes) if notes else "aucun PDF exploitable parmi les fichiers deposes."
        raise ValueError(f"Aucun fichier produit.\n{detail}")

    message = f"{len(created)} fichier(s) cree(s) :\n" + "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
