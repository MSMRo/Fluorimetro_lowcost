"""Gráfica espectral académica con animación visual no destructiva."""

from __future__ import annotations

from time import monotonic

from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QWidget

from protocol import PLOT_KEYS, PLOT_WAVELENGTHS

ANIMATION_DURATION_SECONDS = 0.22
FRAME_INTERVAL_MS = 16
SPECTRAL_COLORS = (
    "#6d28d9", "#2563eb", "#0891b2", "#15803d",
    "#65a30d", "#d97706", "#ea580c", "#b91c1c",
)


def _spectral_gradient(rect: QRectF, vertical: bool = False) -> QLinearGradient:
    gradient = (
        QLinearGradient(rect.left(), rect.bottom(), rect.left(), rect.top())
        if vertical
        else QLinearGradient(rect.left(), 0, rect.right(), 0)
    )
    wavelength_span = PLOT_WAVELENGTHS[-1] - PLOT_WAVELENGTHS[0]
    for wavelength, color in zip(PLOT_WAVELENGTHS, SPECTRAL_COLORS, strict=True):
        gradient.setColorAt((wavelength - PLOT_WAVELENGTHS[0]) / wavelength_span, QColor(color))
    return gradient


class SpectralPlot(QWidget):
    """Dibuja F1-F8; NIR y Clear permanecen disponibles en la tabla raw."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._display_values: list[float] | None = None
        self._start_values: list[float] | None = None
        self._target_values: list[float] | None = None
        self._pending_values: list[float] | None = None
        self._maximum = 2000
        self._paused = False
        self._animation_enabled = True
        self._animation_started = 0.0
        self._animation_timer = QTimer(self)
        self._animation_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._animation_timer.setInterval(FRAME_INTERVAL_MS)
        self._animation_timer.timeout.connect(self._advance_animation)
        self.setMinimumHeight(300)
        self.setAccessibleName("Espectro visible AS7341 entre 415 y 680 nanómetros")
        self.setToolTip(
            "La curva es una guía visual suavizada. Los marcadores y la tabla "
            "representan las cuentas raw medidas en cada canal."
        )

    @property
    def display_values(self) -> tuple[float, ...] | None:
        return tuple(self._display_values) if self._display_values is not None else None

    @property
    def paused(self) -> bool:
        return self._paused

    def set_channels(self, channels: dict[str, int]) -> None:
        values = [float(channels[key]) for key in PLOT_KEYS]
        self._pending_values = values
        if not self._paused:
            self._begin_transition(values)

    def set_paused(self, paused: bool) -> None:
        self._paused = bool(paused)
        if self._paused:
            self._animation_timer.stop()
            return
        if self._pending_values is not None:
            self._begin_transition(self._pending_values)

    def set_animation_enabled(self, enabled: bool) -> None:
        self._animation_enabled = bool(enabled)
        if not enabled and self._target_values is not None:
            self._animation_timer.stop()
            self._display_values = self._target_values.copy()
            self.update()

    def set_maximum(self, maximum: int) -> None:
        if type(maximum) is not int or not 1 <= maximum <= 65535:
            raise ValueError("El límite debe ser un entero entre 1 y 65535 cuentas.")
        self._maximum = maximum
        self.update()

    def _begin_transition(self, values: list[float]) -> None:
        if self._display_values is None:
            self._display_values = [0.0] * len(values)
        self._start_values = self._display_values.copy()
        self._target_values = values.copy()
        # Una saturación no es una medida interpolable. Mantener la animación
        # sólo entre lecturas cuantificables, sin crear valores desde OVFL.
        for index, (start, target) in enumerate(zip(self._start_values, values, strict=True)):
            if start >= 65535 or target >= 65535:
                self._start_values[index] = target
                self._display_values[index] = target
        if not self._animation_enabled:
            self._display_values = values.copy()
            self.update()
            return
        self._animation_started = monotonic()
        if not self._animation_timer.isActive():
            self._animation_timer.start()
        self.update()

    def _advance_animation(self) -> None:
        if self._start_values is None or self._target_values is None:
            self._animation_timer.stop()
            return
        progress = min(1.0, (monotonic() - self._animation_started) / ANIMATION_DURATION_SECONDS)
        eased = 1.0 - (1.0 - progress) ** 3
        self._display_values = [
            start + (target - start) * eased
            for start, target in zip(self._start_values, self._target_values, strict=True)
        ]
        self.update()
        if progress >= 1.0:
            self._animation_timer.stop()

    def paintEvent(self, event) -> None:  # noqa: N802
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#ffffff"))
        if self._display_values is None:
            painter.setPen(QColor("#64748b"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Esperando lecturas del AS7341")
            return

        left, top, right, bottom = 72, 32, 96, 62
        plot_rect = QRectF(left, top, max(1, self.width() - left - right), max(1, self.height() - top - bottom))
        self._draw_grid(painter, plot_rect)
        points = self._measurement_points(plot_rect)
        gradient = _spectral_gradient(plot_rect)
        painter.save()
        painter.setClipRect(plot_rect.adjusted(-5, -5, 5, 5))
        painter.setPen(QPen(QBrush(gradient), 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        segment: list[QPointF] = []
        for point, value in zip(points, self._display_values, strict=True):
            if value < 65535 and value <= self._maximum:
                segment.append(point)
                continue
            if len(segment) >= 2:
                painter.drawPath(self._smooth_path(segment))
            segment = []
        if len(segment) >= 2:
            painter.drawPath(self._smooth_path(segment))

        for point, value, color in zip(points, self._display_values, SPECTRAL_COLORS, strict=True):
            if value >= 65535 or value > self._maximum:
                continue
            painter.setPen(QPen(QColor(color), 2))
            painter.setBrush(QColor("#ffffff"))
            painter.drawEllipse(point, 4.0, 4.0)
        painter.restore()

        self._draw_axes_and_labels(painter, plot_rect)
        self._draw_wavelength_bar(painter, plot_rect)
        if any(self._maximum < value < 65535 for value in self._display_values):
            painter.setPen(QColor("#9a6700"))
            painter.drawText(int(plot_rect.left()), 20, "Hay valores fuera de escala; consulta la tabla o aumenta el límite Y")
        else:
            painter.setPen(QColor("#64748b"))
            painter.drawText(
                QRectF(plot_rect.right() - 230, 5, 230, 18),
                Qt.AlignmentFlag.AlignRight,
                "Curva visual; marcadores = datos raw",
            )

    def _measurement_points(self, rect: QRectF) -> list[QPointF]:
        span = PLOT_WAVELENGTHS[-1] - PLOT_WAVELENGTHS[0]
        return [
            QPointF(
                rect.left() + rect.width() * (wavelength - PLOT_WAVELENGTHS[0]) / span,
                rect.bottom() - rect.height() * min(value, self._maximum) / self._maximum,
            )
            for wavelength, value in zip(PLOT_WAVELENGTHS, self._display_values, strict=True)
        ]

    @staticmethod
    def _smooth_path(points: list[QPointF]) -> QPainterPath:
        path = QPainterPath(points[0])
        for p1, p2 in zip(points, points[1:]):
            middle_x = (p1.x() + p2.x()) / 2
            control1 = QPointF(middle_x, p1.y())
            control2 = QPointF(middle_x, p2.y())
            path.cubicTo(control1, control2, p2)
        return path

    def _draw_grid(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QPen(QColor("#dce3ea"), 1))
        for step in range(5):
            y = rect.top() + rect.height() * step / 4
            painter.drawLine(QPointF(rect.left(), y), QPointF(rect.right(), y))
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
        painter.drawLine(rect.topLeft(), rect.bottomLeft())

    def _draw_axes_and_labels(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(QColor("#334155"))
        for step in range(5):
            value = round(self._maximum * (4 - step) / 4)
            y = rect.top() + rect.height() * step / 4
            painter.drawText(QRectF(4, y - 9, 60, 18), Qt.AlignmentFlag.AlignRight, str(value))
        for wavelength in PLOT_WAVELENGTHS:
            x = rect.left() + rect.width() * (wavelength - PLOT_WAVELENGTHS[0]) / (PLOT_WAVELENGTHS[-1] - PLOT_WAVELENGTHS[0])
            painter.drawText(QRectF(x - 22, rect.bottom() + 8, 44, 20), Qt.AlignmentFlag.AlignCenter, str(wavelength))
        painter.setFont(QFont(painter.font().family(), 10))
        painter.drawText(QRectF(rect.left(), rect.bottom() + 34, rect.width(), 20), Qt.AlignmentFlag.AlignCenter, "Longitud de onda (nm)")
        painter.save()
        painter.translate(18, rect.center().y())
        painter.rotate(-90)
        painter.drawText(QRectF(-rect.height() / 2, -10, rect.height(), 20), Qt.AlignmentFlag.AlignCenter, "Cuentas ADC raw")
        painter.restore()

    def _draw_wavelength_bar(self, painter: QPainter, rect: QRectF) -> None:
        bar = QRectF(rect.right() + 35, rect.top(), 12, rect.height())
        gradient = _spectral_gradient(bar, vertical=True)
        painter.fillRect(bar, QBrush(gradient))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(QColor("#94a3b8"), 1))
        painter.drawRect(bar)
        painter.setPen(QColor("#334155"))
        painter.drawText(QRectF(bar.left() - 10, bar.top() - 25, 46, 20), Qt.AlignmentFlag.AlignCenter, "λ (nm)")
        for wavelength in (415, 480, 555, 630, 680):
            fraction = (wavelength - PLOT_WAVELENGTHS[0]) / (PLOT_WAVELENGTHS[-1] - PLOT_WAVELENGTHS[0])
            y = bar.bottom() - bar.height() * fraction
            painter.drawText(QRectF(bar.right() + 5, y - 9, 36, 18), Qt.AlignmentFlag.AlignLeft, str(wavelength))
