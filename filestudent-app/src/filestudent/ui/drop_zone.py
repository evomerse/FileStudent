"""Zone de depot de fichiers, reutilisee dans chaque onglet (ticket APP-01)."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from filestudent.core.file_types import detect_file_kind, label_for


class DropZone(QWidget):
    """Zone glisser-deposer avec repli sur une boite de dialogue classique.

    Emet `filesAdded` avec la liste des nouveaux fichiers a chaque ajout, et
    conserve la liste complete et deduplicated dans `self.files`.
    """

    filesAdded = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.files: list[str] = []
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)

        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setStyleSheet(
            "QFrame { border: 2px dashed #D7DBE2; border-radius: 8px; padding: 18px; }"
        )
        frame_layout = QVBoxLayout(self.frame)
        self.hint_label = QLabel("Deposez vos fichiers ici", self.frame)
        self.hint_label.setStyleSheet("border: none; color: #566072; font-size: 13px;")
        frame_layout.addWidget(self.hint_label)

        browse_row = QHBoxLayout()
        self.browse_button = QPushButton("Parcourir des fichiers...", self)
        self.browse_button.clicked.connect(self._browse)
        self.clear_button = QPushButton("Vider la liste", self)
        self.clear_button.clicked.connect(self.clear)
        browse_row.addWidget(self.browse_button)
        browse_row.addWidget(self.clear_button)
        browse_row.addStretch()

        self.list_widget = QListWidget(self)

        layout.addWidget(self.frame)
        layout.addLayout(browse_row)
        layout.addWidget(self.list_widget)

    def _browse(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Choisir des fichiers")
        if paths:
            self._add_files(paths)

    def clear(self) -> None:
        self.files.clear()
        self.list_widget.clear()

    def _add_files(self, paths: list[str]) -> None:
        new_paths = [p for p in paths if p not in self.files]
        if not new_paths:
            return
        for path in new_paths:
            self.files.append(path)
            kind = detect_file_kind(path)
            item = QListWidgetItem(f"{path}  -  {label_for(kind)}")
            self.list_widget.addItem(item)
        self.filesAdded.emit(new_paths)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        if paths:
            self._add_files(paths)
            event.acceptProposedAction()
