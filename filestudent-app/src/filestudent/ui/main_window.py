"""Fenetre principale : navigation par onglets, un par module (ticket APP-01)."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from filestudent.core.result import Result
from filestudent.core.task_queue import TaskQueue
from filestudent.modules import (
    ai_compare,
    ai_detect,
    archive,
    compress,
    conversion,
    image_enhance,
    merge,
    pdf_compare,
    pdf_edit,
    redact,
    repair,
    security,
    split,
)
from filestudent.ui.context_menu_tab import ContextMenuTab
from filestudent.ui.drop_zone import DropZone

# Specification des options affichees au-dessus du bouton "Traiter", propres
# a chaque module. kind : "combo" -> QComboBox, "slider" -> QSlider,
# "text" -> QLineEdit (password=True pour masquer la saisie),
# "checkbox" -> QCheckBox (pas de label de formulaire, la case porte le texte).
OptionSpec = dict[str, Any]
OptionWidget = QComboBox | QSlider | QLineEdit | QCheckBox

CONVERSION_OPTIONS: list[OptionSpec] = [
    {
        "key": "target",
        "label": "Format de sortie",
        "kind": "combo",
        "choices": [
            "PDF", "PNG", "JPG", "WEBP", "BMP", "TIFF", "GIF", "DOCX", "PPTX", "XLSX", "MD",
        ],
        "default": "PDF",
    },
]

COMPRESS_OPTIONS: list[OptionSpec] = [
    {"key": "quality", "label": "Qualite", "kind": "slider", "min": 10, "max": 95, "default": 75},
]

ARCHIVE_OPTIONS: list[OptionSpec] = [
    {
        "key": "level",
        "label": "Niveau de compression",
        "kind": "slider",
        "min": 1,
        "max": 9,
        "default": 6,
    },
]

IMAGE_ENHANCE_OPTIONS: list[OptionSpec] = [
    {
        "key": "filter_name",
        "label": "Filtre",
        "kind": "combo",
        "choices": list(image_enhance.FILTERS.keys()),
        "default": "Aucun",
    },
    {
        "key": "resize",
        "label": "Redimensionner",
        "kind": "combo",
        "choices": list(image_enhance.RESIZE_MODES.keys()),
        "default": "Aucun",
    },
    {
        "key": "custom_size",
        "label": "Dimensions exactes (ex. 800x600, optionnel)",
        "kind": "text",
        "placeholder": "800x600",
    },
    {
        "key": "crop_percent",
        "label": "Recadrer (marge en %)",
        "kind": "slider",
        "min": 0,
        "max": 40,
        "default": 0,
    },
    {
        "key": "rotate",
        "label": "Pivoter (degres)",
        "kind": "combo",
        "choices": list(image_enhance.ROTATE_ANGLES.keys()),
        "default": "0",
    },
    {
        "key": "upscale",
        "label": "Agrandissement",
        "kind": "combo",
        "choices": list(image_enhance.UPSCALE_FACTORS.keys()),
        "default": "x1",
    },
    {"key": "watermark_text", "label": "Filigrane (texte, optionnel)", "kind": "text"},
]

SPLIT_OPTIONS: list[OptionSpec] = [
    {
        "key": "action",
        "label": "Action",
        "kind": "combo",
        "choices": split.ACTIONS,
        "default": split.ACTIONS[0],
    },
    {
        "key": "pages",
        "label": "Pages (ex. 1-3,5,8-10 ou 3,1,2,4 pour reorganiser)",
        "kind": "text",
        "placeholder": "1-3,5,8-10",
    },
]

PDF_EDIT_OPTIONS: list[OptionSpec] = [
    {
        "key": "angle",
        "label": "Rotation (degres)",
        "kind": "combo",
        "choices": ["0", "90", "180", "270"],
        "default": "0",
    },
    {
        "key": "crop_percent",
        "label": "Rogner (marge en %)",
        "kind": "slider",
        "min": 0,
        "max": 40,
        "default": 0,
    },
    {"key": "watermark_text", "label": "Filigrane (texte, optionnel)", "kind": "text"},
    {"key": "page_numbers", "label": "Numeroter les pages", "kind": "checkbox"},
]

REDACT_OPTIONS: list[OptionSpec] = [
    {"key": "search_text", "label": "Texte a censurer", "kind": "text", "placeholder": "..."},
]

SECURITY_OPTIONS: list[OptionSpec] = [
    {
        "key": "action",
        "label": "Action",
        "kind": "combo",
        "choices": security.ACTIONS,
        "default": security.ACTIONS[0],
    },
    {"key": "password", "label": "Mot de passe", "kind": "text", "password": True},
]

# Titre, description, fonction de traitement, options -> un onglet par entree.
MODULES: list[tuple[str, str, Callable[..., Any], list[OptionSpec]]] = [
    (
        "Conversion",
        "Convertir entre images, PDF et documents bureautiques (Word, PowerPoint, Excel).",
        conversion.run,
        CONVERSION_OPTIONS,
    ),
    ("Fusion", "Fusionner plusieurs PDF ou images en un seul document.", merge.run, []),
    (
        "Diviser un PDF",
        "Extraire, supprimer ou separer des pages d'un PDF.",
        split.run,
        SPLIT_OPTIONS,
    ),
    (
        "Reduction de taille",
        "Reduire le poids d'un PDF ou d'une image.",
        compress.run,
        COMPRESS_OPTIONS,
    ),
    (
        "Rotation, filigrane, numerotation",
        "Pivoter, rogner, ajouter un filigrane et/ou numeroter les pages d'un PDF.",
        pdf_edit.run,
        PDF_EDIT_OPTIONS,
    ),
    (
        "Reparer PDF",
        "Recuperer un PDF legerement corrompu ou mal forme.",
        repair.run,
        [],
    ),
    (
        "Comparer PDF",
        "Afficher les differences de texte entre deux versions d'un PDF.",
        pdf_compare.run,
        [],
    ),
    (
        "Censurer PDF",
        "Supprimer reellement un texte recherche dans un PDF (pas juste le cacher).",
        redact.run,
        REDACT_OPTIONS,
    ),
    (
        "Securite PDF",
        "Proteger un PDF par mot de passe, ou le deverrouiller.",
        security.run,
        SECURITY_OPTIONS,
    ),
    ("Archive .tar.gz", "Creer ou extraire une archive .tar.gz.", archive.run, ARCHIVE_OPTIONS),
    (
        "Amelioration d'image",
        "Filtres, redimensionnement, rotation, filigrane et upscaling.",
        image_enhance.run,
        IMAGE_ENHANCE_OPTIONS,
    ),
    (
        "Detection de texte IA",
        "Estimer si un texte a ete genere par une IA.",
        ai_detect.run,
        [],
    ),
    (
        "Comparaison de documents",
        "Comparer la similarite entre documents.",
        ai_compare.run,
        [],
    ),
]


class ModuleTab(QWidget):
    """Un onglet complet : depot de fichiers, options, traitement, resultat."""

    def __init__(
        self,
        title: str,
        description: str,
        runner: Callable[..., Any],
        option_specs: list[OptionSpec],
    ) -> None:
        super().__init__()
        self.runner = runner
        self.option_specs = option_specs
        self.option_widgets: dict[str, OptionWidget] = {}
        self.task_queue = TaskQueue()
        self.last_paths: list[str] = []

        layout = QVBoxLayout(self)

        desc_label = QLabel(description, self)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #566072; font-size: 13px;")

        self.drop_zone = DropZone(self)

        layout.addWidget(desc_label)
        layout.addWidget(self.drop_zone, stretch=1)

        if option_specs:
            form = QFormLayout()
            for spec in option_specs:
                row_widget = self._build_option_row(spec)
                if spec["kind"] == "checkbox":
                    form.addRow(row_widget)
                else:
                    form.addRow(spec["label"] + " :", row_widget)
            layout.addLayout(form)

        self.run_button = QPushButton(f"Traiter avec {title}", self)
        self.run_button.clicked.connect(self._run)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # indetermine : la duree reelle depend du fichier
        self.progress_bar.hide()

        self.status_label = QLabel("Pret.", self)
        self.status_label.setStyleSheet("color: #566072; font-size: 12px;")

        self.result_view = QPlainTextEdit(self)
        self.result_view.setReadOnly(True)
        self.result_view.setMaximumHeight(120)
        self.result_view.hide()

        open_row = QHBoxLayout()
        self.open_folder_button = QPushButton("Ouvrir le dossier", self)
        self.open_folder_button.clicked.connect(self._open_folder)
        self.open_file_button = QPushButton("Ouvrir le fichier", self)
        self.open_file_button.clicked.connect(self._open_file)
        open_row.addWidget(self.open_folder_button)
        open_row.addWidget(self.open_file_button)
        open_row.addStretch()
        self.open_folder_button.hide()
        self.open_file_button.hide()

        layout.addWidget(self.run_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.result_view)
        layout.addLayout(open_row)

    def _build_option_row(self, spec: OptionSpec) -> QWidget:
        """Construit le widget a inserer dans le formulaire et enregistre le
        widget porteur de la valeur dans `self.option_widgets`."""
        kind = spec["kind"]

        if kind == "combo":
            combo = QComboBox(self)
            combo.addItems(spec["choices"])
            combo.setCurrentText(spec["default"])
            self.option_widgets[spec["key"]] = combo
            return combo

        if kind == "slider":
            row = QWidget(self)
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            slider = QSlider(Qt.Orientation.Horizontal, row)
            slider.setMinimum(spec["min"])
            slider.setMaximum(spec["max"])
            slider.setValue(spec["default"])
            value_label = QLabel(str(spec["default"]), row)
            value_label.setFixedWidth(30)
            slider.valueChanged.connect(lambda v: value_label.setText(str(v)))
            row_layout.addWidget(slider)
            row_layout.addWidget(value_label)
            self.option_widgets[spec["key"]] = slider
            return row

        if kind == "text":
            line_edit = QLineEdit(self)
            if spec.get("placeholder"):
                line_edit.setPlaceholderText(spec["placeholder"])
            if spec.get("password"):
                line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.option_widgets[spec["key"]] = line_edit
            return line_edit

        if kind == "checkbox":
            checkbox = QCheckBox(spec["label"], self)
            self.option_widgets[spec["key"]] = checkbox
            return checkbox

        raise ValueError(f"Type d'option inconnu : {kind}")

    def _collect_options(self) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for spec in self.option_specs:
            widget = self.option_widgets[spec["key"]]
            key = spec["key"]
            if isinstance(widget, QComboBox):
                values[key] = widget.currentText()
            elif isinstance(widget, QSlider):
                values[key] = widget.value()
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
        return values

    def _run(self) -> None:
        if not self.drop_zone.files:
            self.status_label.setText("Deposez au moins un fichier avant de lancer le traitement.")
            return

        self.run_button.setEnabled(False)
        self.progress_bar.show()
        self.result_view.hide()
        self.open_folder_button.hide()
        self.open_file_button.hide()
        self.status_label.setText("Traitement en cours...")

        options = self._collect_options()
        self.task_queue.submit(
            self.runner,
            list(self.drop_zone.files),
            on_finished=self._on_finished,
            on_error=self._on_error,
            **options,
        )

    def _on_finished(self, result: Any) -> None:
        self.progress_bar.hide()
        self.run_button.setEnabled(True)
        self.status_label.setText("Termine.")

        if isinstance(result, Result):
            message, paths = result.message, result.paths
        elif result:
            message, paths = str(result), []
        else:
            message, paths = "", []

        if message:
            self.result_view.setPlainText(message)
            self.result_view.show()

        self.last_paths = paths
        if paths:
            self.open_folder_button.show()
            self.open_file_button.show()

    def _on_error(self, message: str) -> None:
        self.progress_bar.hide()
        self.run_button.setEnabled(True)
        self.status_label.setText(f"Erreur : {message}")

    def _open_folder(self) -> None:
        if not self.last_paths:
            return
        folder = os.path.dirname(self.last_paths[0]) or "."
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    def _open_file(self) -> None:
        if not self.last_paths:
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.last_paths[0]))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FileStudent")
        self.resize(1000, 740)
        self.setMinimumSize(780, 580)

        tabs = QTabWidget(self)
        tabs.setUsesScrollButtons(True)
        for title, description, runner, option_specs in MODULES:
            tabs.addTab(ModuleTab(title, description, runner, option_specs), title)
        tabs.addTab(ContextMenuTab(), "Menu contextuel Windows")
        self.setCentralWidget(tabs)

        self.statusBar().showMessage("FileStudent - pret.")
