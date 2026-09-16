import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QCoreApplication


@pytest.fixture(scope="session")
def qapp():
    """Une seule QCoreApplication pour toute la session de tests.

    Necessaire pour que les signaux Qt emis depuis un fil de QThreadPool
    soient bien relayes vers le fil principal (connexion en file d'attente).
    """
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def pump(qapp):
    """Vide la boucle d'evenements Qt pour livrer les signaux en attente."""
    def _pump(cycles: int = 50) -> None:
        for _ in range(cycles):
            qapp.processEvents()
    return _pump
