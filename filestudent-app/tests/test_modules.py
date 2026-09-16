"""Tests des 7 modules reels (plus de stubs a partir du jour 1 bis)."""

from __future__ import annotations

import os

import pymupdf
import pytest
from PIL import Image

from filestudent.modules import (
    ai_compare,
    ai_detect,
    archive,
    compress,
    conversion,
    image_enhance,
    merge,
    pdf_edit,
    security,
    split,
)


def make_image(path, size=(80, 50), color=(200, 50, 50)):
    Image.new("RGB", size, color).save(path)
    return str(path)


def make_pdf(path, pages=1, text="Contenu de test."):
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()
    return str(path)


# --- Conversion -------------------------------------------------------------


def test_conversion_image_to_pdf(tmp_path):
    img = make_image(tmp_path / "photo.png")
    conversion.run([img], target="PDF")
    assert (tmp_path / "photo.pdf").exists()


def test_conversion_pdf_to_images(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=2)
    conversion.run([pdf], target="PNG")
    assert (tmp_path / "cours_page1.png").exists()
    assert (tmp_path / "cours_page2.png").exists()


def test_conversion_no_op_raises_clear_error(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    with pytest.raises(ValueError, match="Aucun fichier converti"):
        conversion.run([pdf], target="PDF")


# --- Fusion -------------------------------------------------------------


def test_merge_combines_pdf_and_image_in_order(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf")
    img = make_image(tmp_path / "b.png")
    from pypdf import PdfReader

    merge.run([pdf, img])
    out = tmp_path / "fusion.pdf"
    assert out.exists()
    assert len(PdfReader(str(out)).pages) == 2


def test_merge_requires_at_least_two_files(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf")
    with pytest.raises(ValueError, match="au moins deux"):
        merge.run([pdf])


# --- Reduction de taille -------------------------------------------------------------


def test_compress_image_actually_shrinks(tmp_path):
    img_path = tmp_path / "photo.png"
    Image.effect_noise((400, 300), 40).convert("RGB").save(img_path, "PNG")
    before = os.path.getsize(img_path)

    compress.run([str(img_path)], quality=60)

    out = tmp_path / "photo_compresse.jpg"
    assert out.exists()
    assert out.stat().st_size < before


def test_compress_pdf_produces_smaller_or_valid_output(tmp_path):
    img_path = tmp_path / "photo.png"
    Image.effect_noise((400, 300), 40).convert("RGB").save(img_path, "PNG")
    pdf_path = tmp_path / "cours.pdf"
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=300)
    page.insert_image(page.rect, filename=str(img_path))
    doc.save(str(pdf_path))
    doc.close()

    compress.run([str(pdf_path)], quality=60)
    assert (tmp_path / "cours_compresse.pdf").exists()


# --- Archive -------------------------------------------------------------


def test_archive_create_then_extract_roundtrip(tmp_path):
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("contenu a")
    f2.write_text("contenu b")

    archive.run([str(f1), str(f2)], level=9)
    archive_path = tmp_path / "archive.tar.gz"
    assert archive_path.exists()

    archive.run([str(archive_path)])
    extracted = tmp_path / "archive"
    assert sorted(os.listdir(extracted)) == ["a.txt", "b.txt"]
    assert (extracted / "a.txt").read_text() == "contenu a"


# --- Amelioration d'image -------------------------------------------------------------


def test_image_enhance_upscale_changes_dimensions(tmp_path):
    img = make_image(tmp_path / "photo.png", size=(80, 50))
    image_enhance.run([img], filter_name="Nettete", upscale="x2")
    out = tmp_path / "photo_ameliore.png"
    with Image.open(out) as im:
        assert im.size == (160, 100)


def test_image_enhance_rejects_unknown_filter(tmp_path):
    img = make_image(tmp_path / "photo.png")
    with pytest.raises(ValueError, match="Filtre inconnu"):
        image_enhance.run([img], filter_name="Nimportequoi")


# --- Detection de texte IA -------------------------------------------------------------


def test_ai_detect_scores_regular_text_higher_than_varied_text(tmp_path):
    varied = tmp_path / "varie.txt"
    varied.write_text(
        "Bonjour. Aujourd'hui il fait beau et j'ai decide d'aller me promener "
        "dans le parc avec mon chien qui adore courir apres les ecureuils.",
        encoding="utf-8",
    )
    regular = tmp_path / "regulier.txt"
    regular.write_text(
        ("Le systeme traite les donnees de maniere efficace et fiable. " * 6).strip(),
        encoding="utf-8",
    )

    varied_result = ai_detect.run([str(varied)])
    regular_result = ai_detect.run([str(regular)])

    def score_of(result) -> float:
        first_line = result.message.splitlines()[0]
        return float(first_line.split(":")[1].strip().rstrip(" %"))

    assert score_of(regular_result) > score_of(varied_result)


def test_ai_detect_writes_report_file(tmp_path):
    txt = tmp_path / "texte.txt"
    txt.write_text("Une phrase suffisamment longue pour etre analysee par le module.")
    ai_detect.run([str(txt)])
    assert (tmp_path / "rapport_detection_ia.txt").exists()


# --- Comparaison de documents -------------------------------------------------------------


def test_ai_compare_detects_near_duplicate(tmp_path):
    a = tmp_path / "devoir_1.txt"
    b = tmp_path / "devoir_2.txt"
    c = tmp_path / "devoir_3.txt"
    shared = "La revolution industrielle a transforme les societes europeennes au 19e siecle."
    a.write_text(shared)
    b.write_text(shared + " Ainsi que l'apparition de nouvelles classes sociales.")
    c.write_text("Les ecosystemes marins abritent une biodiversite exceptionnelle et fragile.")

    result = ai_compare.run([str(a), str(b), str(c)])

    assert "devoir_1.txt" in result.message and "devoir_2.txt" in result.message
    assert (tmp_path / "rapport_comparaison.txt").exists()


def test_ai_compare_requires_at_least_two_files(tmp_path):
    a = tmp_path / "devoir_1.txt"
    a.write_text("Un texte.")
    with pytest.raises(ValueError, match="au moins deux"):
        ai_compare.run([str(a)])


# --- Diviser un PDF ----------------------------------------------------------


def test_split_extract_pages(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=5)
    from pypdf import PdfReader

    split.run([pdf], action="Extraire des pages", pages="1-2,4")
    out = tmp_path / "cours_extrait.pdf"
    assert len(PdfReader(str(out)).pages) == 3


def test_split_remove_pages(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=5)
    from pypdf import PdfReader

    split.run([pdf], action="Supprimer des pages", pages="3")
    out = tmp_path / "cours_sans_pages.pdf"
    assert len(PdfReader(str(out)).pages) == 4


def test_split_one_file_per_page(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=3)
    result = split.run([pdf], action="Diviser chaque page")
    assert len(result.paths) == 3


def test_split_rejects_empty_page_range(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=3)
    with pytest.raises(ValueError, match="Indiquez les pages"):
        split.run([pdf], action="Extraire des pages", pages="")


# --- Rotation, filigrane, numerotation ----------------------------------------


def test_pdf_edit_applies_rotation_watermark_and_numbering(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", pages=2)
    result = pdf_edit.run(
        [pdf], angle="90", watermark_text="BROUILLON", page_numbers=True
    )
    out = result.paths[0]
    doc = pymupdf.open(out)
    assert doc.load_page(0).rotation == 90
    text = doc.load_page(0).get_text()
    assert "BROUILLON" in text
    assert "1 / 2" in text
    doc.close()


def test_pdf_edit_requires_at_least_one_transformation(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    with pytest.raises(ValueError, match="Choisissez au moins une transformation"):
        pdf_edit.run([pdf])


# --- Securite PDF -------------------------------------------------------------


def test_security_protect_then_unlock_roundtrip(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    from pypdf import PdfReader

    protected = security.run([pdf], action="Proteger", password="secret123")
    assert PdfReader(protected.paths[0]).is_encrypted

    unlocked = security.run(protected.paths, action="Deverrouiller", password="secret123")
    assert not PdfReader(unlocked.paths[0]).is_encrypted


def test_security_unlock_rejects_wrong_password(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    protected = security.run([pdf], action="Proteger", password="secret123")
    with pytest.raises(ValueError, match="Aucun fichier produit"):
        security.run(protected.paths, action="Deverrouiller", password="mauvais")


# --- Conversion Office ---------------------------------------------------------


def test_conversion_pdf_to_docx(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", text="Un paragraphe de test.")
    result = conversion.run([str(pdf)], target="DOCX")
    assert (tmp_path / "cours.docx").exists()
    assert result.paths == [str(tmp_path / "cours.docx")]


def test_conversion_docx_to_pdf_fallback_without_libreoffice(tmp_path, monkeypatch):
    import docx

    from filestudent.core import office

    monkeypatch.setattr(office, "find_libreoffice", lambda: None)

    docx_path = tmp_path / "rapport.docx"
    d = docx.Document()
    d.add_paragraph("Un paragraphe de test pour la conversion sans LibreOffice.")
    d.save(str(docx_path))

    result = conversion.run([str(docx_path)], target="PDF")
    assert (tmp_path / "rapport.pdf").exists()
    assert "LibreOffice non detecte" in result.message


# --- Amelioration d'image, options etendues ------------------------------------


def test_image_enhance_resize_and_rotate(tmp_path):
    img = make_image(tmp_path / "photo.png", size=(400, 300))
    result = image_enhance.run([img], resize="50 %", rotate="90")
    with Image.open(result.paths[0]) as im:
        # 400x300 pivote a 90 degres (expand) -> 300x400, puis 50% -> 150x200.
        assert im.size == (150, 200)


def test_image_enhance_watermark_adds_text(tmp_path):
    img = make_image(tmp_path / "photo.png", size=(300, 200))
    result = image_enhance.run([img], watermark_text="CONFIDENTIEL")
    assert result.paths and os.path.exists(result.paths[0])
