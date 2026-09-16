"""Resultat structure renvoye par chaque module.

Porte a la fois le message affiche a l'utilisateur et la liste des
fichiers/dossiers produits, pour que l'interface propose "Ouvrir le
dossier" / "Ouvrir le fichier" sans avoir a analyser du texte.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    message: str
    paths: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        return self.message
