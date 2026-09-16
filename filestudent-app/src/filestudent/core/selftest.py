"""Auto-diagnostic embarque : verifie que chaque module fonctionne reellement
sur la machine en cours, y compris a l'interieur d'un executable PyInstaller
fige (ou les erreurs d'import silencieuses sont le risque principal).

Se lance avec `filestudent --selftest` (ou `python -m filestudent --selftest`).
N'ouvre aucune fenetre : affiche un rapport dans le terminal et renvoie un
code de sortie non nul si un module echoue.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path


def _make_image(path: Path) -> str:
    from PIL import Image

    Image.new("RGB", (80, 60), (200, 60, 60)).save(path)
    return str(path)


def _make_pdf(path: Path, pages: int = 2) -> str:
    import pymupdf

    doc = pymupdf.open()
    for i in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} de test.")
    doc.save(str(path))
    doc.close()
    return str(path)


def _make_docx(path: Path) -> str:
    import docx

    document = docx.Document()
    document.add_paragraph("Paragraphe de test pour l'auto-diagnostic.")
    document.save(str(path))
    return str(path)


def _make_txt(path: Path) -> str:
    path.write_text(
        "Un texte de test suffisamment long pour etre analyse par les modules IA.",
        encoding="utf-8",
    )
    return str(path)


def run_selftest() -> bool:
    from filestudent.modules import (
        ai_compare,
        ai_detect,
        archive,
        compress,
        conversion,
        image_enhance,
        merge,
        pdf_compare,
        pdf_edit,
        redact,
        repair,
        security,
        split,
    )

    tmp = Path(tempfile.mkdtemp(prefix="filestudent_selftest_"))
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, fn) -> None:
        try:
            fn()
            checks.append((name, True, ""))
        except Exception as exc:  # noqa: BLE001 - on veut voir l'echec, pas planter
            checks.append((name, False, f"{type(exc).__name__}: {exc}"))

    img = _make_image(tmp / "photo.png")
    pdf = _make_pdf(tmp / "cours.pdf")
    pdf_v2 = _make_pdf(tmp / "cours_v2.pdf", pages=3)
    docx_path = _make_docx(tmp / "rapport.docx")
    txt_a = _make_txt(tmp / "texte_a.txt")
    txt_b = _make_txt(tmp / "texte_b.txt")

    check("Conversion (image -> PDF)", lambda: conversion.run([img], target="PDF"))
    check("Conversion (PDF -> DOCX, pdf2docx)", lambda: conversion.run([pdf], target="DOCX"))
    check("Conversion (DOCX -> PDF)", lambda: conversion.run([docx_path], target="PDF"))
    check("Conversion (PDF -> Markdown)", lambda: conversion.run([pdf], target="MD"))
    check("Fusion", lambda: merge.run([pdf, img]))
    check("Diviser un PDF", lambda: split.run([pdf], action="Extraire des pages", pages="1"))
    check(
        "Diviser un PDF (reorganiser)",
        lambda: split.run([pdf], action="Reorganiser les pages", pages="2,1"),
    )
    check("Reduction de taille", lambda: compress.run([img], quality=70))
    check(
        "Rotation, filigrane, numerotation, rognage",
        lambda: pdf_edit.run(
            [pdf], angle="90", crop_percent=5, watermark_text="TEST", page_numbers=True
        ),
    )
    check("Reparer PDF", lambda: repair.run([pdf]))
    check("Comparer PDF", lambda: pdf_compare.run([pdf, pdf_v2]))
    check("Censurer PDF", lambda: redact.run([pdf], search_text="test"))
    check("Securite PDF", lambda: security.run([pdf], action="Proteger", password="test1234"))
    check("Archive .tar.gz", lambda: archive.run([img, pdf], level=6))
    check(
        "Amelioration d'image",
        lambda: image_enhance.run(
            [img], filter_name="Nettete", upscale="x2", crop_percent=5, custom_size="200x150"
        ),
    )
    check("Detection de texte IA", lambda: ai_detect.run([txt_a]))
    check("Comparaison de documents", lambda: ai_compare.run([txt_a, txt_b]))

    print("Auto-diagnostic FileStudent")
    print("=" * 40)
    ok_count = 0
    for name, ok, detail in checks:
        status = "OK  " if ok else "ECHEC"
        print(f"[{status}] {name}" + (f" : {detail}" if detail else ""))
        ok_count += int(ok)
    print("=" * 40)
    print(f"{ok_count}/{len(checks)} module(s) fonctionnels.")

    shutil.rmtree(tmp, ignore_errors=True)
    return ok_count == len(checks)


def main() -> None:
    success = run_selftest()
    sys.exit(0 if success else 1)
