"""Escritura serializada de telemetría fuera del hilo de la interfaz."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from queue import Full, Queue
from threading import Event, Lock, Thread
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from exporter import CsvExporter


@dataclass(frozen=True)
class _AppendTask:
    received_at: datetime
    telemetry: dict[str, Any]
    destinations: tuple[CsvExporter, ...]


@dataclass(frozen=True)
class _BarrierTask:
    completed: Event


class TelemetryWriter(QObject):
    """Mantiene el sondeo serial y el repintado separados de la latencia del disco."""

    error_received = pyqtSignal(object, str)

    def __init__(self, primary: CsvExporter, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.primary = primary
        self._queue: Queue[_AppendTask | _BarrierTask | None] = Queue(maxsize=1024)
        self._errors: dict[int, str] = {}
        self._failed: set[int] = set()
        self._closed = False
        self._lock = Lock()
        self._thread = Thread(target=self._run, name="as7341-csv-writer", daemon=True)
        self._thread.start()

    def append(
        self,
        received_at: datetime,
        telemetry: dict[str, Any],
        secondary: CsvExporter | None = None,
    ) -> bool:
        destinations = (self.primary,) if secondary is None else (self.primary, secondary)
        try:
            self._queue.put_nowait(_AppendTask(received_at, telemetry, destinations))
        except Full:
            self.error_received.emit(None, "La cola de escritura CSV se llenó; se detuvo el registro para evitar datos incompletos.")
            return False
        return True

    def drain(self, timeout_seconds: float = 5.0) -> bool:
        completed = Event()
        try:
            self._queue.put(_BarrierTask(completed), timeout=timeout_seconds)
        except Full:
            return False
        return completed.wait(timeout_seconds)

    def take_error(self, exporter: CsvExporter) -> str | None:
        with self._lock:
            exporter_id = id(exporter)
            self._failed.discard(exporter_id)
            return self._errors.pop(exporter_id, None)

    def close(self) -> bool:
        if self._closed or not self._thread.is_alive():
            self._closed = True
            return True
        if not self.drain():
            return False
        try:
            self._queue.put(None, timeout=1.0)
        except Full:
            return False
        self._thread.join(timeout=5.0)
        self._closed = not self._thread.is_alive()
        return self._closed

    def _run(self) -> None:
        while True:
            task = self._queue.get()
            try:
                if task is None:
                    return
                if isinstance(task, _BarrierTask):
                    task.completed.set()
                    continue
                for exporter in task.destinations:
                    if id(exporter) in self._failed:
                        continue
                    try:
                        exporter.append(task.received_at, task.telemetry)
                    except OSError as error:
                        message = str(error)
                        with self._lock:
                            self._errors[id(exporter)] = message
                            self._failed.add(id(exporter))
                        self.error_received.emit(exporter, message)
            finally:
                self._queue.task_done()
