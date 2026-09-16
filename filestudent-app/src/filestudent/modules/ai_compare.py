"""Module Comparaison de documents (ticket APP-13).

Version MVP : comparaison locale de similarite entre plusieurs documents
deposes (empreintes de groupes de mots), sans recherche sur le web. Voir le
backlog pour la version avec recherche en ligne.
"""

from __future__ import annotations

import os
import re
from itertools import combinations
from typing import Any

from filestudent.core.output import unique_path
from filestudent.core.result import Result
from filestudent.core.text_extract import extract_text

SHINGLE_SIZE = 8


def _shingles(text: str) -> set[str]:
    words = re.findall(r"\w+", text.lower())
    if len(words) < SHINGLE_SIZE:
        return {" ".join(words)} if words else set()
    return {" ".join(words[i : i + SHINGLE_SIZE]) for i in range(len(words) - SHINGLE_SIZE + 1)}


def _similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return round(100 * intersection / union, 1) if union else 0.0


def run(files: list[str], **_options: Any) -> Result:
    if len(files) < 2:
        raise ValueError("Deposez au moins deux fichiers a comparer.")

    texts = {}
    for path in files:
        try:
            texts[path] = extract_text(path)
        except ValueError:
            texts[path] = None

    usable = {p: t for p, t in texts.items() if t}
    if len(usable) < 2:
        raise ValueError(
            "Au moins deux fichiers doivent etre dans un format exploitable (.pdf, .docx, .txt)."
        )

    shingle_sets = {p: _shingles(t) for p, t in usable.items()}

    lines = ["Similarite entre documents (empreintes de groupes de mots) :", ""]
    for a, b in combinations(usable.keys(), 2):
        sim = _similarity(shingle_sets[a], shingle_sets[b])
        lines.append(f"{os.path.basename(a)}  <->  {os.path.basename(b)} : {sim:.0f} %")

    ignored = [p for p, t in texts.items() if not t]
    if ignored:
        lines.append("")
        lines.append("Ignores (format non pris en charge) :")
        lines.extend(f"  {p}" for p in ignored)

    report = "\n".join(lines)
    report_path = unique_path(
        os.path.join(os.path.dirname(files[0]) or ".", "rapport_comparaison.txt")
    )
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    message = report + f"\n\nRapport complet : {report_path}"
    return Result(message=message, paths=[report_path])
