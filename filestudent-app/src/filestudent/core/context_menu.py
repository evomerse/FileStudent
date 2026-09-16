"""Installation/desinstallation du menu contextuel Windows (clic droit dans
l'explorateur ou sur le bureau), directement depuis l'application, sans
script separe (ticket APP-23).

Chaque action est une entree DIRECTE du clic droit (pas un sous-menu en
cascade) : le mecanisme de sous-menu en cascade de Windows (valeur
"SubCommands") s'est avere peu fiable en pratique, meme quand la cle
principale s'affiche correctement, ce qui explique pourquoi tres peu
d'outils l'utilisent. Chaque entree porte le prefixe "FileStudent - " pour
rester reconnaissable et groupee visuellement, sans dependre de ce
mecanisme fragile.

Ecrit uniquement dans HKEY_CURRENT_USER : aucun droit administrateur requis.
Le module `winreg` fait partie de la bibliotheque standard mais n'existe
que sous Windows : tout appel est garde par `is_windows()`, et l'import se
fait a la demande pour que ce fichier reste importable (et testable) sur
n'importe quel systeme.
"""

from __future__ import annotations

import sys

# (identifiant de cle, libelle affiche, argument --action, sans le --file)
FILE_VERBS: list[tuple[str, str, str]] = [
    ("FileStudent_ToPDF", "FileStudent - Convertir en PDF", "--action=to-pdf"),
    ("FileStudent_ToWord", "FileStudent - Convertir en Word (.docx)", "--action=to-word"),
    ("FileStudent_ToImage", "FileStudent - Convertir en image (PNG)", "--action=to-image"),
    ("FileStudent_ToMarkdown", "FileStudent - Convertir en Markdown", "--action=to-md"),
    ("FileStudent_Compress", "FileStudent - Reduire la taille", "--action=compress"),
    ("FileStudent_Enhance", "FileStudent - Ameliorer l'image", "--action=enhance"),
    ("FileStudent_Split", "FileStudent - Diviser en pages", "--action=split"),
    ("FileStudent_Repair", "FileStudent - Reparer le PDF", "--action=repair"),
    ("FileStudent_Redact", "FileStudent - Censurer un texte...", "--action=redact"),
    ("FileStudent_Watermark", "FileStudent - Ajouter un filigrane...", "--action=watermark"),
    ("FileStudent_Protect", "FileStudent - Proteger par mot de passe...", "--action=protect"),
    ("FileStudent_DetectAI", "FileStudent - Detecter texte IA", "--action=detect-ai"),
    ("FileStudent_Open", "FileStudent - Ouvrir dans FileStudent", ""),
]

FOLDER_VERBS: list[tuple[str, str, str]] = [
    ("FileStudent_Archive", "FileStudent - Compresser en .tar.gz", "--action=archive"),
]

FILE_PARENT = r"Software\Classes\*\shell"
FOLDER_PARENT = r"Software\Classes\Directory\shell"
BACKGROUND_ROOT = r"Software\Classes\Directory\Background\shell\FileStudent"

ALL_ROOTS = tuple(f"{FILE_PARENT}\\{verb_id}" for verb_id, _label, _action in FILE_VERBS) + tuple(
    f"{FOLDER_PARENT}\\{verb_id}" for verb_id, _label, _action in FOLDER_VERBS
) + (
    f"{FOLDER_PARENT}\\FileStudent_OpenFolder",
    BACKGROUND_ROOT,
)


def is_windows() -> bool:
    return sys.platform == "win32"


def is_frozen() -> bool:
    """Vrai uniquement pour un executable construit par PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def _winreg():  # pragma: no cover - trivial, remplace en test
    import winreg

    return winreg


def _set_default(winreg, key, value: str) -> None:
    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)


def _create_verb(winreg, verb_path: str, label: str, command: str, icon: str) -> None:
    """Cree une entree de clic droit DIRECTE (pas de sous-menu)."""
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, verb_path) as key:
        _set_default(winreg, key, label)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, f'"{icon}"')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{verb_path}\\command") as key:
        _set_default(winreg, key, command)


def is_installed() -> bool:
    if not is_windows():
        return False
    winreg = _winreg()
    verb_id = FILE_VERBS[0][0]
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"{FILE_PARENT}\\{verb_id}")
    except FileNotFoundError:
        return False
    winreg.CloseKey(key)
    return True


def install(exe_path: str | None = None) -> list[str]:
    """Ecrit les cles de registre du menu contextuel, puis relit tout ce
    qui vient d'etre ecrit pour confirmer que c'est bien present.

    `exe_path` par defaut : l'executable en cours d'execution (utile
    uniquement pour un .exe construit par PyInstaller, pas pour un
    lancement depuis les sources).

    Renvoie la liste des problemes detectes a la relecture (vide si tout
    est en ordre).
    """
    if not is_windows():
        raise RuntimeError("Le menu contextuel n'est disponible que sous Windows.")
    if exe_path is None:
        exe_path = sys.executable

    winreg = _winreg()

    for verb_id, label, action in FILE_VERBS:
        args = f'{action} --file="%1"' if action else '--file="%1"'
        command = f'"{exe_path}" {args}'.strip()
        _create_verb(winreg, f"{FILE_PARENT}\\{verb_id}", label, command, exe_path)

    for verb_id, label, action in FOLDER_VERBS:
        command = f'"{exe_path}" {action} --file="%1"'
        _create_verb(winreg, f"{FOLDER_PARENT}\\{verb_id}", label, command, exe_path)
    _create_verb(
        winreg,
        f"{FOLDER_PARENT}\\FileStudent_OpenFolder",
        "FileStudent - Ouvrir",
        f'"{exe_path}"',
        exe_path,
    )

    _create_verb(winreg, BACKGROUND_ROOT, "Ouvrir FileStudent", f'"{exe_path}"', exe_path)

    return verify()


def verify() -> list[str]:
    """Relit chaque cle censee avoir ete ecrite par `install()` et renvoie
    la liste de celles qui manquent ou dont la valeur est vide. Sert a
    detecter une ecriture partielle plutot que de supposer que tout s'est
    bien passe."""
    if not is_windows():
        return ["Pas sous Windows."]

    winreg = _winreg()
    problems: list[str] = []

    def read_default(path: str) -> str | None:
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            return None
        try:
            value, _type = winreg.QueryValueEx(key, "")
        except FileNotFoundError:
            value = None
        winreg.CloseKey(key)
        return value

    for verb_id, label, _action in FILE_VERBS:
        path = f"{FILE_PARENT}\\{verb_id}"
        if read_default(path) != label:
            problems.append(f"Action manquante ou incorrecte sur les fichiers : {label}")
        if not read_default(f"{path}\\command"):
            problems.append(f"Commande manquante pour : {label}")

    for verb_id, label, _action in FOLDER_VERBS:
        path = f"{FOLDER_PARENT}\\{verb_id}"
        if read_default(path) != label:
            problems.append(f"Action manquante ou incorrecte sur les dossiers : {label}")
        if not read_default(f"{path}\\command"):
            problems.append(f"Commande manquante pour : {label}")

    if not read_default(f"{FOLDER_PARENT}\\FileStudent_OpenFolder"):
        problems.append("Entree 'Ouvrir' sur les dossiers manquante.")
    if not read_default(BACKGROUND_ROOT):
        problems.append("Entree sur le fond de dossier / bureau manquante.")

    return problems


def uninstall() -> None:
    if not is_windows():
        return
    winreg = _winreg()
    for path in ALL_ROOTS:
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, f"{path}\\command", 0, winreg.KEY_ALL_ACCESS
            )
        except FileNotFoundError:
            pass
        else:
            winreg.CloseKey(key)
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{path}\\command")
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
        except FileNotFoundError:
            pass
