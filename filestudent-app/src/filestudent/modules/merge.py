"""Module Fusion (ticket APP-06).

Fusionne plusieurs PDF et/ou images, dans l'ordre donne, en un seul PDF.
"""

from __future__ import annotations

import io
import os
from typing import Any

from PIL import Image
from pypdf import PdfReader, PdfWriter

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import unique_path
from filestudent.core.result import Result


def run(files: list[str], **_options: Any) -> Result:
    if len(files) < 2:
        raise ValueError("Deposez au moins deux fichiers a fusionner.")

    writer = PdfWriter()
    used: list[str] = []

    for path in files:
        kind = detect_file_kind(path)
        if kind == FileKind.PDF:
            reader = PdfReader(path)
            for page in reader.pages:
                writer.add_page(page)
            used.append(path)
        elif kind == FileKind.IMAGE:
            with Image.open(path) as img:
                img_rgb = img.convert("RGB")
                buf = io.BytesIO()
                img_rgb.save(buf, "PDF")
                buf.seek(0)
                page_reader = PdfReader(buf)
                writer.add_page(page_reader.pages[0])
            used.append(path)

    if not used:
        raise ValueError("Aucun fichier PDF ou image exploitable parmi les fichiers deposes.")

    out = unique_path(os.path.join(os.path.dirname(files[0]) or ".", "fusion.pdf"))
    with open(out, "wb") as fh:
        writer.write(fh)

    return Result(message=f"Fusion de {len(used)} fichier(s) reussie :\n{out}", paths=[out])
