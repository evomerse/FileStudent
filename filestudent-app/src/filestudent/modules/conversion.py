"""Module Conversion (ticket APP-05).

Convertit entre formats d'images (PNG, JPG, WEBP, BMP, TIFF), PDF, et
documents bureautiques (DOCX, PPTX, XLSX), dans les deux sens.

- Image <-> PDF, image <-> image : toujours disponible (Pillow).
- PDF -> DOCX : toujours disponible (pdf2docx, sans dependance externe).
- DOCX -> PDF : mise en page fidele si LibreOffice est installe, sinon un
  rendu texte simplifie (sans images ni tableaux) qui fonctionne partout.
- PPTX/XLSX -> PDF et PDF -> PPTX : necessitent LibreOffice (message clair
  si absent, voir core/office.py).
"""

from __future__ import annotations

import os
import statistics
from typing import Any

import pymupdf
from PIL import Image

from filestudent.core import office
from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import sibling_path
from filestudent.core.result import Result

IMAGE_TARGETS = {"PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF"}
OFFICE_TARGETS = {"DOCX", "PPTX", "XLSX"}
TEXT_TARGETS = {"MD"}
ALL_TARGETS = {"PDF", *IMAGE_TARGETS, *OFFICE_TARGETS, *TEXT_TARGETS}
PIL_FORMAT = {"JPG": "JPEG"}  # PIL nomme le JPEG "JPEG", pas "JPG"
BOLD_FLAG = 1 << 4  # bit "gras" dans PyMuPDF span["flags"]


# --- Image <-> PDF / image -------------------------------------------------


def _image_to_pdf(path: str) -> str:
    out = sibling_path(path, new_ext=".pdf")
    with Image.open(path) as img:
        img.convert("RGB").save(out, "PDF")
    return out


def _image_to_image(path: str, target: str) -> str:
    out = sibling_path(path, new_ext=f".{target.lower()}")
    with Image.open(path) as img:
        fmt = PIL_FORMAT.get(target, target)
        if fmt == "JPEG":
            img = img.convert("RGB")
        img.save(out, fmt)
    return out


def _pdf_to_images(path: str, target: str) -> list[str]:
    fmt = target.lower()
    outputs: list[str] = []
    with pymupdf.open(path) as doc:
        for i, page in enumerate(doc, start=1):
            pixmap = page.get_pixmap(dpi=150)
            out = sibling_path(path, suffix=f"_page{i}", new_ext=f".{fmt}")
            pixmap.save(out, "jpeg" if fmt in ("jpg", "jpeg") else None)
            outputs.append(out)
    return outputs


# --- PDF -> Markdown (toujours disponible) -----------------------------------


def _pdf_to_markdown(path: str) -> str:
    """Conversion heuristique : la taille de police relative a la taille la
    plus frequente du document determine les titres (# / ## / ###). Chaque
    ligne devient un paragraphe Markdown independant : plus simple et plus
    fiable que d'essayer de recomposer des paragraphes multi-lignes a
    partir de la seule position des blocs de texte."""
    out = sibling_path(path, new_ext=".md")

    with pymupdf.open(path) as doc:
        sizes: list[int] = []
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        if span["text"].strip():
                            sizes.append(round(span["size"]))
        # En cas d'egalite de frequence (document court : une ligne de
        # titre, une ligne de corps), on prend la plus petite taille : le
        # corps du texte est presque toujours plus petit qu'un titre.
        body_size = min(statistics.multimode(sizes)) if sizes else 11

        md_lines: list[str] = []
        for page in doc:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    spans = [s for s in line.get("spans", []) if s["text"].strip()]
                    if not spans:
                        continue
                    text = "".join(s["text"] for s in spans).strip()
                    if not text:
                        continue
                    max_size = max(s["size"] for s in spans)
                    is_bold = any(s["flags"] & BOLD_FLAG for s in spans)
                    if max_size >= body_size * 1.8:
                        md_lines.append(f"# {text}")
                    elif max_size >= body_size * 1.4:
                        md_lines.append(f"## {text}")
                    elif max_size >= body_size * 1.15:
                        md_lines.append(f"### {text}")
                    elif is_bold:
                        md_lines.append(f"**{text}**")
                    else:
                        md_lines.append(text)
            md_lines.append("")  # saut de page -> paragraphe vide

    markdown = "\n\n".join(md_lines).strip() + "\n"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(markdown)
    return out


# --- PDF -> DOCX (toujours disponible) --------------------------------------


def _pdf_to_docx(path: str) -> str:
    from pdf2docx import Converter

    out = sibling_path(path, new_ext=".docx")
    converter = Converter(path)
    try:
        converter.convert(out)
    finally:
        converter.close()
    return out


# --- DOCX -> PDF, avec repli si LibreOffice est absent ----------------------


def _wrap_text(text: str, fontsize: float, max_width: float, fontname: str = "helv") -> list[str]:
    words = text.split()
    if not words:
        return [""]
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if pymupdf.get_text_length(trial, fontname=fontname, fontsize=fontsize) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _docx_to_pdf_fallback(path: str) -> str:
    """Rendu texte simplifie : sans LibreOffice, on perd les images, les
    tableaux et la mise en page fine, mais le contenu textuel est preserve."""
    import docx

    try:
        document = docx.Document(path)
    except Exception as exc:
        raise ValueError(
            f"Fichier Word illisible (vide ou corrompu) : {os.path.basename(path)}. "
            "Ouvrez-le dans Word et enregistrez-le avant de reessayer."
        ) from exc
    out = sibling_path(path, new_ext=".pdf")
    doc = pymupdf.open()
    margin = 72
    page = doc.new_page()
    max_width = page.rect.width - 2 * margin
    y = margin

    for para in document.paragraphs:
        text = para.text
        is_heading = bool(para.style and para.style.name.startswith("Heading"))
        fontsize = 15 if is_heading else 11
        if not text.strip():
            y += fontsize
            continue
        for line in _wrap_text(text, fontsize, max_width):
            if y > page.rect.height - margin:
                page = doc.new_page()
                y = margin
            page.insert_text((margin, y), line, fontsize=fontsize)
            y += fontsize * 1.4
        y += fontsize * 0.6

    doc.save(out)
    doc.close()
    return out


def _docx_to_pdf(path: str, out_dir: str) -> tuple[str, bool]:
    """Renvoie (chemin_produit, a_utilise_libreoffice)."""
    if office.is_available():
        return office.convert(path, "pdf", out_dir), True
    return _docx_to_pdf_fallback(path), False


# --- Point d'entree ----------------------------------------------------------


def run(files: list[str], target: str = "PDF", **_options: Any) -> Result:
    target = target.upper()
    if target not in ALL_TARGETS:
        raise ValueError(f"Format de sortie non pris en charge : {target}")

    created: list[str] = []
    notes: list[str] = []

    for path in files:
        ext = os.path.splitext(path)[1].lower()
        kind = detect_file_kind(path)
        out_dir = os.path.dirname(path) or "."

        if os.path.getsize(path) == 0:
            notes.append(f"{path} : fichier vide (0 octet), rien a convertir.")
            continue

        try:
            if kind == FileKind.IMAGE:
                if target == "PDF":
                    created.append(_image_to_pdf(path))
                elif target in IMAGE_TARGETS:
                    created.append(_image_to_image(path, target))
                else:
                    notes.append(f"{path} : une image ne peut pas devenir un {target}.")

            elif ext == ".pdf":
                if target == "PDF":
                    notes.append(f"{path} : deja au format PDF.")
                elif target in IMAGE_TARGETS:
                    created.extend(_pdf_to_images(path, target))
                elif target == "DOCX":
                    created.append(_pdf_to_docx(path))
                elif target == "MD":
                    created.append(_pdf_to_markdown(path))
                elif target in ("PPTX", "XLSX"):
                    created.append(office.convert(path, target.lower(), out_dir))

            elif ext == ".docx":
                if target != "PDF":
                    notes.append(f"{path} : seule la conversion DOCX vers PDF est geree.")
                else:
                    produced, used_libreoffice = _docx_to_pdf(path, out_dir)
                    created.append(produced)
                    if not used_libreoffice:
                        notes.append(
                            f"{produced} : LibreOffice non detecte, rendu texte simplifie "
                            "(images et tableaux non conserves)."
                        )

            elif ext in (".pptx", ".xlsx"):
                if target != "PDF":
                    notes.append(f"{path} : seule la conversion vers PDF est geree pour ce format.")
                else:
                    created.append(office.convert(path, "pdf", out_dir))

            else:
                notes.append(f"{path} : format non pris en charge.")

        except (RuntimeError, ValueError) as exc:
            notes.append(f"{path} : {exc}")

    if not created:
        detail = "\n".join(notes) if notes else "aucun fichier exploitable."
        raise ValueError(f"Aucun fichier converti.\n{detail}")

    message = f"{len(created)} fichier(s) cree(s) :\n" + "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)
