"""Tests des ajouts iLovePDF/iLoveIMG : rognage, reparation, reorganisation,
Markdown, comparaison de differences, censure, recadrage et
redimensionnement exact d'image."""

from __future__ import annotations

import pymupdf
import pytest
from PIL import Image

from filestudent.modules import image_enhance, pdf_compare, pdf_edit, redact, repair, split


def make_pdf(path, pages=1, text="Contenu de test.", width=600, height=800):
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page(width=width, height=height)
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()
    return str(path)


def make_image(path, size=(400, 300), color=(20, 90, 180)):
    Image.new("RGB", size, color).save(path)
    return str(path)


# --- Rogner PDF (pdf_edit) --------------------------------------------------


def test_pdf_crop_reduces_page_size(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", width=600, height=800)
    result = pdf_edit.run([pdf], crop_percent=10)
    doc = pymupdf.open(result.paths[0])
    box = doc.load_page(0).cropbox
    doc.close()
    assert round(box.width) == 480
    assert round(box.height) == 640


# --- Reparer PDF -------------------------------------------------------------


def test_repair_recovers_a_lightly_corrupted_pdf(tmp_path):
    make_pdf(tmp_path / "cours.pdf")
    data = (tmp_path / "cours.pdf").read_bytes()
    broken = tmp_path / "casse.pdf"
    broken.write_bytes(data[:-40])  # xref/trailer tronque

    result = repair.run([str(broken)])
    assert (tmp_path / "casse_repare.pdf").exists()
    assert result.paths


def test_repair_gives_clear_error_on_unrecoverable_file(tmp_path):
    bad = tmp_path / "invalide.pdf"
    bad.write_bytes(b"pas un pdf du tout" * 3)
    with pytest.raises(ValueError, match="Aucun fichier repare"):
        repair.run([str(bad)])


# --- Reorganiser les pages (split) -------------------------------------------


def test_split_reorder_matches_requested_order(tmp_path):
    pdf = str(tmp_path / "cours.pdf")
    doc = pymupdf.open()
    for i in range(1, 5):
        doc.new_page().insert_text((72, 100), f"Marqueur {i}")
    doc.save(pdf)
    doc.close()

    split.run([pdf], action="Reorganiser les pages", pages="3,1,2,4")
    out = pymupdf.open(str(tmp_path / "cours_reorganise.pdf"))
    order = [p.get_text() for p in out]
    out.close()
    assert "Marqueur 3" in order[0]
    assert "Marqueur 1" in order[1]
    assert "Marqueur 2" in order[2]
    assert "Marqueur 4" in order[3]


def test_split_reorder_rejects_incomplete_order(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=4)
    with pytest.raises(ValueError, match="exactement une fois"):
        split.run([pdf], action="Reorganiser les pages", pages="1,2,3")


# --- PDF vers Markdown (conversion) ------------------------------------------


def test_pdf_to_markdown_detects_heading(tmp_path):
    # Plusieurs lignes de corps de texte pour que la heuristique (la taille
    # la PLUS FREQUENTE = corps du texte) ait un vrai "mode" statistique,
    # comme dans un document reel.
    from filestudent.modules import conversion

    pdf_path = tmp_path / "cours.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Grand Titre", fontsize=24)
    page.insert_text((72, 110), "Premiere ligne de corps de texte.", fontsize=11)
    page.insert_text((72, 130), "Deuxieme ligne de corps de texte.", fontsize=11)
    page.insert_text((72, 150), "Troisieme ligne de corps de texte.", fontsize=11)
    doc.save(str(pdf_path))
    doc.close()

    result = conversion.run([str(pdf_path)], target="MD")
    content = (tmp_path / "cours.md").read_text(encoding="utf-8")
    assert "# Grand Titre" in content
    assert "Premiere ligne de corps de texte." in content
    assert result.paths


# --- Comparer PDF (differences) ----------------------------------------------


def test_pdf_compare_finds_added_and_removed_lines(tmp_path):
    a = make_pdf(tmp_path / "v1.pdf", text="Une ligne.\nDeuxieme ligne originale.")
    b = make_pdf(tmp_path / "v2.pdf", text="Une ligne.\nDeuxieme ligne modifiee.\nTroisieme.")

    result = pdf_compare.run([a, b])
    assert "ajoutee" in result.message
    assert (tmp_path / "rapport_differences.txt").exists()


def test_pdf_compare_requires_exactly_two_pdfs(tmp_path):
    a = make_pdf(tmp_path / "v1.pdf")
    with pytest.raises(ValueError, match="exactement deux"):
        pdf_compare.run([a])


# --- Censurer PDF (vraie redaction) ------------------------------------------


def test_redact_actually_removes_the_text(tmp_path):
    pdf = make_pdf(tmp_path / "confidentiel.pdf", text="Le code secret est BANANE42 ici.")
    result = redact.run([pdf], search_text="BANANE42")

    doc = pymupdf.open(result.paths[0])
    remaining = doc.load_page(0).get_text()
    doc.close()
    assert "BANANE42" not in remaining


def test_redact_requires_search_text(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    with pytest.raises(ValueError, match="Indiquez le texte"):
        redact.run([pdf], search_text="")


def test_redact_reports_when_text_not_found(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", text="Rien de sensible ici.")
    with pytest.raises(ValueError, match="Aucune censure"):
        redact.run([pdf], search_text="INTROUVABLE")


# --- Image : recadrer et dimensions exactes ----------------------------------


def test_image_crop_percent(tmp_path):
    img = make_image(tmp_path / "photo.png", size=(400, 300))
    result = image_enhance.run([img], crop_percent=10)
    with Image.open(result.paths[0]) as im:
        assert im.size == (320, 240)


def test_image_custom_size(tmp_path):
    img = make_image(tmp_path / "photo.png")
    result = image_enhance.run([img], custom_size="500x100")
    with Image.open(result.paths[0]) as im:
        assert im.size == (500, 100)


def test_image_custom_size_rejects_bad_format(tmp_path):
    img = make_image(tmp_path / "photo.png")
    with pytest.raises(ValueError, match="Dimensions invalides"):
        image_enhance.run([img], custom_size="500-100")
