"""Coeur de traitement des fichiers (ticket APP-02).

File d'attente de taches en arriere-plan basee sur QThreadPool : chaque
operation de module (conversion, fusion, compression, ...) s'execute dans
un fil separe pour ne jamais figer l'interface. Le resultat ou l'erreur est
relaye vers le fil principal via des signaux Qt, pour que l'interface
puisse afficher une progression et un message clair en cas d'echec, sans
jamais faire planter l'application.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot


class TaskSignals(QObject):
    """Signaux emis par une tache, relayes sur le fil principal."""

    finished = Signal(object)
    error = Signal(str)
    progress = Signal(int)


class Task(QRunnable):
    """Enveloppe une fonction de traitement pour l'executer en arriere-plan.

    Toute exception levee par la fonction est capturee : elle est convertie
    en message d'erreur lisible plutot que de remonter et de faire planter
    l'application.
    """

    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = TaskSignals()

    @Slot()
    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as exc:
            self.signals.error.emit(str(exc) or exc.__class__.__name__)
        else:
            self.signals.finished.emit(result)


class TaskQueue:
    """Point d'entree unique pour lancer un traitement en arriere-plan.

    QThreadPool detruit une tache (`QRunnable.autoDelete`) des que son `run()`
    se termine. Sans precaution, rien ne garde alors de reference Python vers
    la tache ni vers ses signaux entre la fin de `run()` et la livraison du
    signal en file d'attente sur le fil principal : le signal peut se perdre
    et l'interface n'apprend jamais que le traitement est termine. `TaskQueue`
    garde donc chaque tache active en vie jusqu'a ce que son signal ait ete
    livre, puis la relache.
    """

    def __init__(self, max_threads: int | None = None) -> None:
        self.pool = QThreadPool.globalInstance()
        if max_threads is not None:
            self.pool.setMaxThreadCount(max_threads)
        self._active_tasks: set[Task] = set()

    def submit(
        self,
        fn: Callable[..., Any],
        *args: Any,
        on_finished: Callable[[Any], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_progress: Callable[[int], None] | None = None,
        **kwargs: Any,
    ) -> Task:
        """Lance `fn(*args, **kwargs)` en arriere-plan et relie les callbacks."""
        task = Task(fn, *args, **kwargs)
        if on_finished is not None:
            task.signals.finished.connect(on_finished)
        if on_error is not None:
            task.signals.error.connect(on_error)
        if on_progress is not None:
            task.signals.progress.connect(on_progress)

        task.signals.finished.connect(lambda _result, t=task: self._active_tasks.discard(t))
        task.signals.error.connect(lambda _message, t=task: self._active_tasks.discard(t))
        self._active_tasks.add(task)

        self.pool.start(task)
        return task

    def active_count(self) -> int:
        return self.pool.activeThreadCount()

    def wait_for_done(self, timeout_ms: int = -1) -> bool:
        return self.pool.waitForDone(timeout_ms)
