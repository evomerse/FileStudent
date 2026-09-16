"""Module Reduction de taille (ticket APP-07).

Compresse un PDF (recompression des images embarquees, nettoyage des objets
inutilises) ou une image (reencodage JPEG a la qualite choisie).
"""

from __future__ import annotations

import io
import os
from typing import Any

import pymupdf
from PIL import Image

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result


def _compress_image(path: str, quality: int) -> tuple[str, int, int]:
    before = os.path.getsize(path)
    out = sibling_path(path, suffix="_compresse", new_ext=".jpg")
    with Image.open(path) as img:
        img.convert("RGB").save(out, "JPEG", quality=quality, optimize=True)
    after = os.path.getsize(out)
    return out, before, after


def _compress_pdf(path: str, quality: int) -> tuple[str, int, int]:
    before = os.path.getsize(path)
    out = sibling_path(path, suffix="_compresse", new_ext=".pdf")

    with pymupdf.open(path) as doc:
        seen: set[int] = set()
        for page in doc:
            for image_info in page.get_images(full=True):
                xref = image_info[0]
                if xref in seen:
                    continue
                seen.add(xref)
                try:
                    extracted = doc.extract_image(xref)
                    with Image.open(io.BytesIO(extracted["image"])) as im:
                        buf = io.BytesIO()
                        im.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True)
                        doc.update_stream(xref, buf.getvalue())
                except Exception:
                    continue
        doc.save(out, garbage=4, deflate=True, clean=True)

    after = os.path.getsize(out)
    return out, before, after


def run(files: list[str], quality: int = 75, **_options: Any) -> Result:
    quality = max(10, min(95, int(quality)))
    lines: list[str] = []
    paths: list[str] = []

    for path in files:
        kind = detect_file_kind(path)
        if kind == FileKind.IMAGE:
            out, before, after = _compress_image(path, quality)
        elif kind == FileKind.PDF:
            out, before, after = _compress_pdf(path, quality)
        else:
            lines.append(f"Ignore (format non pris en charge) : {path}")
            continue

        gain = 0 if before == 0 else round(100 * (before - after) / before)
        sign = "-" if gain >= 0 else "+"
        lines.append(f"{out}\n  {before // 1024} Ko -> {after // 1024} Ko ({sign}{abs(gain)} %)")
        paths.append(out)

    if not paths:
        raise ValueError("Aucun PDF ou image exploitable parmi les fichiers deposes.")

    return Result(message="\n".join(lines), paths=paths)
