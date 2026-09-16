"""Module Archive .tar.gz (ticket APP-08).

Cree une archive .tar.gz a partir des fichiers/dossiers deposes, ou extrait
une archive .tar.gz si un seul fichier de ce type est depose.
"""

from __future__ import annotations

import os
import tarfile
from typing import Any

from filestudent.core.output import unique_path
from filestudent.core.result import Result


def _is_targz(path: str) -> bool:
    return path.lower().endswith((".tar.gz", ".tgz"))


def _extract(archive_path: str) -> Result:
    base = os.path.basename(archive_path)
    for suffix in (".tar.gz", ".tgz"):
        if base.lower().endswith(suffix):
            base = base[: -len(suffix)]
            break
    dest = unique_path(os.path.join(os.path.dirname(archive_path) or ".", base))
    os.makedirs(dest, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        tar.extractall(dest, filter="data")

    return Result(message=f"Archive extraite dans :\n{dest}", paths=[dest])


def _create(files: list[str], level: int) -> Result:
    out = unique_path(os.path.join(os.path.dirname(files[0]) or ".", "archive.tar.gz"))
    with tarfile.open(out, "w:gz", compresslevel=level) as tar:
        for path in files:
            tar.add(path, arcname=os.path.basename(path))

    size = os.path.getsize(out)
    return Result(message=f"Archive creee ({size // 1024} Ko) :\n{out}", paths=[out])


def run(files: list[str], level: int = 6, **_options: Any) -> Result:
    if not files:
        raise ValueError("Deposez au moins un fichier ou dossier.")

    if len(files) == 1 and _is_targz(files[0]):
        return _extract(files[0])

    level = max(1, min(9, int(level)))
    return _create(files, level)
