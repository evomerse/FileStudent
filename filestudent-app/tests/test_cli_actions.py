"""Tests du dispatcher d'actions du menu contextuel (ticket APP-23)."""

from __future__ import annotations

import pymupdf
import pytest
from PIL import Image

from filestudent.core.cli_actions import run_action


def make_image(path, size=(100, 80), color=(30, 80, 150)):
    Image.new("RGB", size, color).save(path)
    return str(path)


def make_pdf(path, text="Contenu de test."):
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), text)
    doc.save(str(path))
    doc.close()
    return str(path)


def no_prompt(_label):
    raise AssertionError("Ce prompt ne devrait pas etre appele pour cette action.")


def test_to_pdf_on_image(tmp_path):
    img = make_image(tmp_path / "photo.png")
    result = run_action("to-pdf", [img], no_prompt, no_prompt)
    assert (tmp_path / "photo.pdf").exists()
    assert result.paths == [str(tmp_path / "photo.pdf")]


def test_to_word_on_pdf(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("to-word", [pdf], no_prompt, no_prompt)
    assert (tmp_path / "cours.docx").exists()
    assert result.paths


def test_watermark_prompts_for_text_and_applies_it(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("watermark", [pdf], lambda label: "BROUILLON", no_prompt)
    out = result.paths[0]
    doc = pymupdf.open(out)
    assert "BROUILLON" in doc.load_page(0).get_text()
    doc.close()


def test_watermark_cancelled_returns_none(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("watermark", [pdf], lambda label: None, no_prompt)
    assert result is None


def test_protect_prompts_for_password(tmp_path):
    from pypdf import PdfReader

    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("protect", [pdf], no_prompt, lambda label: "secret123")
    assert PdfReader(result.paths[0]).is_encrypted


def test_protect_cancelled_returns_none(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("protect", [pdf], no_prompt, lambda label: None)
    assert result is None


def test_to_md_on_pdf(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("to-md", [pdf], no_prompt, no_prompt)
    assert (tmp_path / "cours.md").exists()
    assert result.paths


def test_repair_on_pdf(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("repair", [pdf], no_prompt, no_prompt)
    assert (tmp_path / "cours_repare.pdf").exists()
    assert result.paths


def test_redact_prompts_for_text_and_removes_it(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf", text="Le mot CACHE29 doit disparaitre.")
    result = run_action("redact", [pdf], lambda label: "CACHE29", no_prompt)
    doc = pymupdf.open(result.paths[0])
    assert "CACHE29" not in doc.load_page(0).get_text()
    doc.close()


def test_redact_cancelled_returns_none(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    result = run_action("redact", [pdf], lambda label: None, no_prompt)
    assert result is None


def test_archive_on_a_folder(tmp_path):
    (tmp_path / "sous_dossier").mkdir()
    (tmp_path / "sous_dossier" / "a.txt").write_text("contenu")
    result = run_action("archive", [str(tmp_path / "sous_dossier")], no_prompt, no_prompt)
    assert result.paths and result.paths[0].endswith("archive.tar.gz")


def test_unknown_action_raises_clear_error(tmp_path):
    pdf = make_pdf(tmp_path / "cours.pdf")
    with pytest.raises(ValueError, match="Action inconnue"):
        run_action("bidule", [pdf], no_prompt, no_prompt)


def test_no_files_raises_clear_error():
    with pytest.raises(ValueError, match="Aucun fichier fourni"):
        run_action("compress", [], no_prompt, no_prompt)
