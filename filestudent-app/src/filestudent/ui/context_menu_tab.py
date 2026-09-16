"""Onglet d'installation du menu contextuel Windows (ticket APP-23).

Pas de zone de depot de fichiers ici : ce n'est pas un module de
traitement, c'est un interrupteur qui ecrit/retire des cles de registre.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QMessageBox, QProgressBar, QPushButton, QVBoxLayout, QWidget

from filestudent.core import context_menu
from filestudent.core.task_queue import TaskQueue


class ContextMenuTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.task_queue = TaskQueue()

        layout = QVBoxLayout(self)

        desc = QLabel(
            "Ajoute une entree FileStudent au clic droit dans l'explorateur "
            "Windows (sur un fichier, sur un dossier, et sur le bureau), "
            "pour traiter un fichier sans ouvrir la fenetre principale.\n\n"
            "N'ecrit que dans votre compte Windows courant : aucun droit "
            "administrateur necessaire.",
            self,
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #566072; font-size: 13px;")
        layout.addWidget(desc)

        self.status_label = QLabel(self)
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("font-weight: 600; font-size: 13px;")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.install_button = QPushButton("Installer le clic droit dans l'explorateur", self)
        self.install_button.clicked.connect(self._install)
        layout.addWidget(self.install_button)

        self.uninstall_button = QPushButton("Desinstaller", self)
        self.uninstall_button.clicked.connect(self._uninstall)
        layout.addWidget(self.uninstall_button)

        layout.addStretch()
        self._refresh_status()

    def _refresh_status(self) -> None:
        if not context_menu.is_windows():
            self.status_label.setText("Non disponible : reserve a Windows.")
            self.install_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
            return

        if not context_menu.is_frozen():
            self.status_label.setText(
                "Construisez d'abord FileStudent.exe (build.bat), puis relancez "
                "cet executable pour pouvoir installer le clic droit."
            )
            self.install_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
            return

        installed = context_menu.is_installed()
        self.status_label.setText("Installe." if installed else "Non installe.")
        self.install_button.setEnabled(True)
        self.uninstall_button.setEnabled(installed)

    def _set_busy(self, busy: bool) -> None:
        self.install_button.setEnabled(not busy)
        self.uninstall_button.setEnabled(not busy)
        self.progress_bar.setVisible(busy)

    def _install(self) -> None:
        self._set_busy(True)
        self.status_label.setText("Installation en cours...")
        self.task_queue.submit(
            context_menu.install,
            on_finished=self._on_install_finished,
            on_error=self._on_error,
        )

    def _on_install_finished(self, problems: list[str]) -> None:
        self._set_busy(False)
        if problems:
            detail = "\n".join(f"- {p}" for p in problems)
            QMessageBox.warning(
                self,
                "FileStudent",
                "Installation terminee, mais certains elements n'ont pas ete "
                f"ecrits correctement :\n{detail}\n\n"
                "Essayez de desinstaller puis reinstaller. Si le probleme "
                "persiste, fermez completement l'explorateur Windows "
                "(gestionnaire des taches > Explorateur Windows > "
                "Redemarrer) puis reessayez.",
            )
        else:
            QMessageBox.information(
                self,
                "FileStudent",
                "Menu contextuel installe et verifie : 10 entrees sur les "
                "fichiers (prefixees \"FileStudent - \"), 1 sur les dossiers, "
                "1 sur le bureau.\n\n"
                "Si elles n'apparaissent pas tout de suite, redemarrez "
                "completement l'explorateur Windows : gestionnaire des "
                "taches (Ctrl+Maj+Echap), onglet Processus, clic droit sur "
                "\"Explorateur Windows\", Redemarrer.",
            )
        self._refresh_status()

    def _uninstall(self) -> None:
        self._set_busy(True)
        self.status_label.setText("Desinstallation en cours...")
        self.task_queue.submit(
            context_menu.uninstall,
            on_finished=self._on_uninstall_finished,
            on_error=self._on_error,
        )

    def _on_uninstall_finished(self, _result: object) -> None:
        self._set_busy(False)
        QMessageBox.information(self, "FileStudent", "Menu contextuel retire.")
        self._refresh_status()

    def _on_error(self, message: str) -> None:
        self._set_busy(False)
        QMessageBox.critical(self, "FileStudent", message)
        self._refresh_status()
