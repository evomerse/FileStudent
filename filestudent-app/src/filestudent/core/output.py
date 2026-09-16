"""Gestion des chemins de sortie : jamais d'ecrasement silencieux d'un fichier."""

from __future__ import annotations

from pathlib import Path


def unique_path(path: str) -> str:
    """Renvoie `path` s'il n'existe pas, sinon `nom (2).ext`, `nom (3).ext`, etc."""
    p = Path(path)
    if not p.exists():
        return str(p)
    n = 2
    while True:
        candidate = p.with_name(f"{p.stem} ({n}){p.suffix}")
        if not candidate.exists():
            return str(candidate)
        n += 1


def sibling_path(original: str, suffix: str = "", new_ext: str | None = None) -> str:
    """Construit un chemin de sortie a cote du fichier d'origine.

    `sibling_path("photo.png", "_ameliore")` -> "photo_ameliore.png"
    `sibling_path("cours.pdf", new_ext=".png")` -> "cours.png"
    """
    p = Path(original)
    ext = new_ext if new_ext is not None else p.suffix
    if ext and not ext.startswith("."):
        ext = "." + ext
    candidate = p.with_name(f"{p.stem}{suffix}{ext}")
    return unique_path(str(candidate))
