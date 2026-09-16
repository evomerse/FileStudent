"""Module Comparer PDF (equivalent Compare PDF d'iLovePDF).

Affiche les vraies differences de texte entre deux versions d'un document
(lignes ajoutees et supprimees), a la difference du module Comparaison de
documents (ai_compare) qui donne un simple score de similarite pour
detecter un plagiat.
"""

from __future__ import annotations

import difflib
import os
from typing import Any

import pymupdf

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.output import unique_path
from filestudent.core.result import Result


def _extract_lines(path: str) -> list[str]:
    with pymupdf.open(path) as doc:
        text = "\n".join(page.get_text() for page in doc)
    return text.splitlines()


def run(files: list[str], **_options: Any) -> Result:
    pdfs = [p for p in files if detect_file_kind(p) == FileKind.PDF]
    if len(pdfs) != 2:
        raise ValueError("Deposez exactement deux PDF a comparer.")

    a_path, b_path = pdfs
    a_lines = _extract_lines(a_path)
    b_lines = _extract_lines(b_path)

    diff = list(
        difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=os.path.basename(a_path),
            tofile=os.path.basename(b_path),
            lineterm="",
        )
    )
    added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
    removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))

    report = "\n".join(diff) if diff else (
        f"Aucune difference de texte entre {os.path.basename(a_path)} "
        f"et {os.path.basename(b_path)}."
    )

    report_path = unique_path(
        os.path.join(os.path.dirname(a_path) or ".", "rapport_differences.txt")
    )
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    summary = f"{added} ligne(s) ajoutee(s), {removed} ligne(s) supprimee(s)."
    return Result(message=f"{summary}\nRapport complet : {report_path}", paths=[report_path])
