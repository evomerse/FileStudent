"""Module Detection de texte IA (ticket APP-12).

Version MVP : heuristiques statistiques uniquement (variation de la
longueur des phrases, richesse du vocabulaire), sans telechargement de
modele. Le resultat est un score de probabilite indicatif par paragraphe,
jamais un verdict. Voir le backlog pour une version basee sur un vrai modele.
"""

from __future__ import annotations

import os
import re
import statistics
from typing import Any

from filestudent.core.output import unique_path
from filestudent.core.result import Result
from filestudent.core.text_extract import extract_text

AVERTISSEMENT = (
    "Ceci est un indicateur statistique approximatif, pas une preuve. "
    "Un score eleve ne signifie pas qu'un texte est genere par une IA, "
    "et un score bas ne le garantit pas non plus."
)


def _sentence_lengths(text: str) -> list[int]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [len(s.split()) for s in sentences if s.strip()]


def _paragraph_score(paragraph: str) -> float:
    words = re.findall(r"\w+", paragraph.lower())
    if len(words) < 8:
        return 0.0

    lengths = _sentence_lengths(paragraph)
    if len(lengths) >= 2 and statistics.mean(lengths) > 0:
        burstiness = statistics.pstdev(lengths) / statistics.mean(lengths)
    else:
        burstiness = 1.0
    regularity_score = max(0.0, 1.0 - min(burstiness, 1.0))

    unique_ratio = len(set(words)) / len(words)
    repetition_score = max(0.0, 1.0 - unique_ratio)

    score = 0.65 * regularity_score + 0.35 * repetition_score
    return round(score * 100, 1)


def run(files: list[str], **_options: Any) -> Result:
    if not files:
        raise ValueError("Deposez au moins un fichier a analyser.")

    report_lines = [AVERTISSEMENT, ""]
    overall_scores: list[float] = []

    for path in files:
        try:
            text = extract_text(path)
        except ValueError as exc:
            report_lines.append(f"{os.path.basename(path)} : ignore ({exc})\n")
            continue
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            report_lines.append(f"{os.path.basename(path)} : aucun texte exploitable.\n")
            continue

        report_lines.append(f"=== {os.path.basename(path)} ===")
        file_scores: list[float] = []
        for i, para in enumerate(paragraphs, start=1):
            if len(re.findall(r"\w+", para)) < 8:
                continue
            score = _paragraph_score(para)
            file_scores.append(score)
            excerpt = para[:80] + ("..." if len(para) > 80 else "")
            report_lines.append(f"  Paragraphe {i} : {score:.0f} % - {excerpt}")

        if file_scores:
            avg = round(statistics.mean(file_scores), 1)
            overall_scores.append(avg)
            report_lines.append(f"  -> Score moyen du fichier : {avg:.0f} %\n")
        else:
            report_lines.append("  (pas assez de texte pour un score fiable)\n")

    if not overall_scores:
        raise ValueError("Aucun paragraphe assez long pour etre analyse dans les fichiers deposes.")

    global_avg = round(statistics.mean(overall_scores), 1)
    report_lines.insert(1, f"Score global indicatif : {global_avg:.0f} %\n")

    report = "\n".join(report_lines)
    report_path = unique_path(
        os.path.join(os.path.dirname(files[0]) or ".", "rapport_detection_ia.txt")
    )
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(report)

    message = f"Score global indicatif : {global_avg:.0f} %\nRapport complet : {report_path}"
    return Result(message=message, paths=[report_path])
