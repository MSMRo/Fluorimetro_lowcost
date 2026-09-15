"""Gráfica ligera de las dos lecturas, sin dependencias adicionales."""

from __future__ import annotations

from collections import deque

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class LivePlot(QWidget):
    """Muestra las últimas lecturas numéricas de 90° y 180°."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._sensor_90: deque[float | None] = deque(maxlen=240)
        self._sensor_180: deque[float | None] = deque(maxlen=240)
        self.setMinimumHeight(210)

    def append(self, sensor_90: object, sensor_180: object) -> None:
        self._sensor_90.append(_numeric_value(sensor_90))
        self._sensor_180.append(_numeric_value(sensor_180))
        self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 - nombre requerido por Qt
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#101820"))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        margins = 34, 16, 16, 26
        left, top, right, bottom = margins
        width = max(1, self.width() - left - right)
        height = max(1, self.height() - top - bottom)

        painter.setPen(QPen(QColor("#54606b"), 1))
        for fraction in (0.0, 0.5, 1.0):
            y = top + height * fraction
            painter.drawLine(left, int(y), left + width, int(y))

        all_values = [
            value
            for series in (self._sensor_90, self._sensor_180)
            for value in series
            if value is not None
        ]
        if not all_values:
            painter.setPen(QColor("#c7d0d9"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Esperando lecturas del equipo")
            return

        minimum = min(all_values)
        maximum = max(all_values)
        if minimum == maximum:
            minimum -= 1.0
            maximum += 1.0

        self._draw_series(painter, self._sensor_90, QColor("#4ac3ff"), minimum, maximum, left, top, width, height)
        self._draw_series(painter, self._sensor_180, QColor("#ffb447"), minimum, maximum, left, top, width, height)

        painter.setPen(QColor("#c7d0d9"))
        painter.drawText(6, top + 4, f"{maximum:.3g}")
        painter.drawText(6, top + height, f"{minimum:.3g}")
        painter.setPen(QColor("#4ac3ff"))
        painter.drawText(left, self.height() - 7, "90°")
        painter.setPen(QColor("#ffb447"))
        painter.drawText(left + 42, self.height() - 7, "180°")

    @staticmethod
    def _draw_series(
        painter: QPainter,
        values: deque[float | None],
        color: QColor,
        minimum: float,
        maximum: float,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        painter.setPen(QPen(color, 2))
        previous = None
        total = max(1, len(values) - 1)
        for index, value in enumerate(values):
            if value is None:
                previous = None
                continue
            x = left + width * index / total
            y = top + height * (maximum - value) / (maximum - minimum)
            if previous is not None:
                painter.drawLine(int(previous[0]), int(previous[1]), int(x), int(y))
            previous = x, y


def _numeric_value(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None

