"""Detection et pilotage de LibreOffice en mode headless.

Utilise pour convertir Word/PowerPoint/Excel vers PDF, et PDF vers
PowerPoint/Excel. Quand LibreOffice n'est pas installe, chaque appelant doit
proposer une alternative ou un message clair : jamais un plantage silencieux
(voir README, section "Dependance optionnelle").
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

_WINDOWS_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
]


def find_libreoffice() -> str | None:
    """Cherche l'executable LibreOffice sur le PATH, puis a des emplacements
    Windows courants si l'installateur n'a pas modifie le PATH."""
    for name in ("soffice", "libreoffice", "soffice.exe"):
        path = shutil.which(name)
        if path:
            return path
    for candidate in _WINDOWS_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return None


def is_available() -> bool:
    return find_libreoffice() is not None


def convert(path: str, target_ext: str, out_dir: str, timeout: int = 120) -> str:
    """Convertit `path` vers l'extension `target_ext` (sans le point) via
    LibreOffice headless. Renvoie le chemin du fichier produit.

    Leve `RuntimeError` si LibreOffice est absent ou si la conversion echoue.
    """
    soffice = find_libreoffice()
    if not soffice:
        raise RuntimeError(
            "LibreOffice n'est pas installe (ou introuvable) sur cette machine. "
            "Ce format necessite LibreOffice pour etre converti : "
            "https://www.libreoffice.org/download/"
        )

    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        soffice,
        "--headless",
        "--norestart",
        "--convert-to",
        target_ext,
        "--outdir",
        out_dir,
        path,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("LibreOffice n'a pas repondu a temps pour cette conversion.") from exc

    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip()
        raise RuntimeError(f"Echec de la conversion LibreOffice : {detail or 'erreur inconnue'}")

    produced = os.path.join(out_dir, f"{Path(path).stem}.{target_ext}")
    if not os.path.exists(produced):
        raise RuntimeError("LibreOffice n'a produit aucun fichier de sortie pour cette conversion.")
    return produced
