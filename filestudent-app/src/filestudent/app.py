"""Point d'entree de l'application FileStudent."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from filestudent.theme import apply_theme
from filestudent.ui.main_window import MainWindow


def _parse_context_menu_args(argv: list[str]) -> tuple[str | None, list[str]]:
    action: str | None = None
    files: list[str] = []
    for arg in argv:
        if arg.startswith("--action="):
            action = arg.split("=", 1)[1]
        elif arg.startswith("--file="):
            files.append(arg.split("=", 1)[1])
    return action, files


def _run_context_menu_action(action: str, files: list[str]) -> None:
    """Execute une action venue du menu contextuel de l'explorateur (ticket
    APP-23) : pas de fenetre principale, juste une boite de dialogue de
    saisie si necessaire, puis un message de resultat avec un raccourci
    "Ouvrir le dossier"."""
    import os

    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    from PySide6.QtWidgets import QInputDialog, QLineEdit, QMessageBox

    from filestudent.core.cli_actions import run_action

    def prompt_text(label: str) -> str | None:
        text, ok = QInputDialog.getText(None, "FileStudent", label)
        return text if ok and text.strip() else None

    def prompt_password(label: str) -> str | None:
        text, ok = QInputDialog.getText(
            None, "FileStudent", label, QLineEdit.EchoMode.Password
        )
        return text if ok and text else None

    try:
        result = run_action(action, files, prompt_text, prompt_password)
    except ValueError as exc:
        QMessageBox.warning(None, "FileStudent", str(exc))
        return
    except Exception as exc:  # noqa: BLE001 - on veut un message, pas un plantage
        QMessageBox.critical(None, "FileStudent", f"Erreur inattendue : {exc}")
        return

    if result is None:
        return  # saisie annulee par l'utilisateur : rien a afficher

    box = QMessageBox()
    box.setWindowTitle("FileStudent")
    box.setIcon(QMessageBox.Icon.Information)
    box.setText(result.message)
    open_button = None
    if result.paths:
        open_button = box.addButton("Ouvrir le dossier", QMessageBox.ButtonRole.ActionRole)
    box.addButton(QMessageBox.StandardButton.Ok)
    box.exec()

    if open_button is not None and box.clickedButton() is open_button:
        folder = os.path.dirname(result.paths[0]) or "."
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def main() -> None:
    argv = sys.argv[1:]

    if "--selftest" in argv:
        from filestudent.core.selftest import main as selftest_main

        selftest_main()
        return

    action, files = _parse_context_menu_args(argv)

    app = QApplication(sys.argv)
    app.setApplicationName("FileStudent")
    apply_theme(app)

    if action:
        _run_context_menu_action(action, files)
        sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
