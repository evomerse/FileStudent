"""Dispatch des actions declenchees depuis le menu contextuel de
l'explorateur Windows (voir install-context-menu.ps1 a la racine du
depot), sans ouvrir la fenetre principale de l'application.
"""

from __future__ import annotations

from collections.abc import Callable

from filestudent.core.file_types import FileKind, detect_file_kind
from filestudent.core.result import Result
from filestudent.modules import (
    ai_detect,
    archive,
    compress,
    conversion,
    image_enhance,
    pdf_edit,
    redact,
    repair,
    security,
    split,
)

# Une fonction de saisie renvoie None si l'utilisateur annule la boite de
# dialogue, une chaine sinon.
PromptFn = Callable[[str], "str | None"]


class Cancelled(Exception):
    """Levee quand l'utilisateur annule une boite de dialogue de saisie."""


def _watermark(files: list[str], prompt_text: PromptFn, _prompt_password: PromptFn) -> Result:
    text = prompt_text("Texte du filigrane :")
    if not text:
        raise Cancelled

    created: list[str] = []
    notes: list[str] = []
    for path in files:
        kind = detect_file_kind(path)
        try:
            if kind == FileKind.PDF:
                r = pdf_edit.run([path], watermark_text=text)
            elif kind == FileKind.IMAGE:
                r = image_enhance.run([path], watermark_text=text)
            else:
                notes.append(f"{path} : filigrane non pris en charge pour ce type de fichier.")
                continue
            created.extend(r.paths)
        except ValueError as exc:
            notes.append(str(exc))

    if not created:
        raise ValueError("\n".join(notes) or "Aucun fichier traite.")
    message = "\n".join(created)
    if notes:
        message += "\n\nA noter :\n" + "\n".join(notes)
    return Result(message=message, paths=created)


def _protect(files: list[str], _prompt_text: PromptFn, prompt_password: PromptFn) -> Result:
    password = prompt_password("Mot de passe a appliquer :")
    if not password:
        raise Cancelled
    return security.run(files, action="Proteger", password=password)


def _redact(files: list[str], prompt_text: PromptFn, _prompt_password: PromptFn) -> Result:
    text = prompt_text("Texte a censurer :")
    if not text:
        raise Cancelled
    return redact.run(files, search_text=text)


ACTIONS: dict[str, Callable[..., Result]] = {
    "to-pdf": lambda files, *_: conversion.run(files, target="PDF"),
    "to-word": lambda files, *_: conversion.run(files, target="DOCX"),
    "to-image": lambda files, *_: conversion.run(files, target="PNG"),
    "to-md": lambda files, *_: conversion.run(files, target="MD"),
    "compress": lambda files, *_: compress.run(files, quality=75),
    "enhance": lambda files, *_: image_enhance.run(files),
    "split": lambda files, *_: split.run(files, action="Diviser chaque page"),
    "repair": lambda files, *_: repair.run(files),
    "archive": lambda files, *_: archive.run(files, level=6),
    "detect-ai": lambda files, *_: ai_detect.run(files),
    "watermark": _watermark,
    "protect": _protect,
    "redact": _redact,
}


def run_action(
    action: str,
    files: list[str],
    prompt_text: PromptFn,
    prompt_password: PromptFn,
) -> Result | None:
    """Execute une action de menu contextuel.

    Renvoie un `Result`, ou `None` si l'utilisateur a annule une saisie
    (dans ce cas, l'appelant ne doit rien afficher).
    """
    if action not in ACTIONS:
        raise ValueError(f"Action inconnue : {action}")
    if not files:
        raise ValueError("Aucun fichier fourni.")
    try:
        return ACTIONS[action](files, prompt_text, prompt_password)
    except Cancelled:
        return None
