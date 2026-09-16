"""Charte graphique express (ticket APP-04).

Version minimale pour tenir le delai de 4 jours : une palette de couleurs et
une feuille de style Qt basique, pas de theme sombre pour ce sprint. A
affiner par Julien une fois les elements graphiques du site disponibles
(voir WEB-B1 et le tableau Trello). Les couleurs reprennent celles deja
utilisees dans le canevas de pitch, pour une identite coherente entre le
logiciel et les supports de presentation.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

PAPER = "#F5F6F8"
SURFACE = "#FFFFFF"
INK = "#1A2233"
INK_SOFT = "#566072"
ACCENT = "#1F6F78"
ACCENT_SOFT = "#DCEBEC"
LINE = "#D7DBE2"


def apply_theme(app: QApplication) -> None:
    """Applique la palette et la feuille de style express de FileStudent."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(PAPER))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(INK))
    palette.setColor(QPalette.ColorRole.Base, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.Text, QColor(INK))
    palette.setColor(QPalette.ColorRole.Button, QColor(SURFACE))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(INK))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(SURFACE))
    app.setPalette(palette)

    app.setStyleSheet(f"""
        QMainWindow, QWidget {{ background-color: {PAPER}; color: {INK}; }}
        QTabWidget::pane {{ border: 1px solid {LINE}; border-radius: 6px; background: {SURFACE}; }}
        QTabBar::tab {{
            padding: 8px 16px; margin-right: 2px; color: {INK_SOFT};
            background: {PAPER}; border: 1px solid {LINE}; border-bottom: none;
            border-top-left-radius: 6px; border-top-right-radius: 6px;
        }}
        QTabBar::tab:selected {{ color: {ACCENT}; background: {SURFACE}; font-weight: 600; }}
        QPushButton {{
            background-color: {ACCENT}; color: {SURFACE}; border: none;
            border-radius: 6px; padding: 8px 18px; font-weight: 600;
        }}
        QPushButton:disabled {{ background-color: {LINE}; color: {INK_SOFT}; }}
        QPushButton:hover:!disabled {{ background-color: #195A62; }}
        QProgressBar {{
            border: 1px solid {LINE}; border-radius: 6px; background: {PAPER};
            text-align: center; color: {INK};
        }}
        QProgressBar::chunk {{ background-color: {ACCENT}; border-radius: 5px; }}
        QListWidget {{ border: 1px solid {LINE}; border-radius: 6px; background: {SURFACE}; }}
    """)
