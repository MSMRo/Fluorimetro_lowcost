"""Vista de puntos experimentales y ajuste; coordenadas numéricas reales."""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class CalibrationPlot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.points, self.fit = [], None
        self.setMinimumHeight(190)
        self.setAccessibleName('Concentración frente a señal; valores disponibles en la tabla')

    def set_points(self, points, fit=None):
        self.points, self.fit = list(points), fit
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor('#ffffff'))
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor('#475569'))
        if not self.points:
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Tus estándares aparecerán aquí al guardar puntos')
            return
        xs, ys = [a['x'] for a in self.points], [a['y'] for a in self.points]
        lo, hi = min(xs), max(xs)
        if self.fit:
            ys += [self.fit['slope']*x+self.fit['intercept'] for x in (lo, hi)]
        yl, yh = min(ys), max(ys)
        dx, dy = max(hi-lo, 1e-9), max(yh-yl, 1e-9)
        left, top, width, height = 65, 25, max(1, self.width()-100), max(1, self.height()-70)
        def xy(x, y):
            return int(left + width*(x-lo)/dx), int(top+height*(yh-y)/dy)
        p.setPen(QPen(QColor('#cbd5e1'), 1))
        p.drawRect(left, top, width, height)
        p.setPen(QColor('#475569'))
        p.drawText(left, self.height()-12, f'Concentración: {lo:g} … {hi:g}')
        p.drawText(3, top+10, f'{yh:.4g}')
        p.drawText(3, top+height, f'{yl:.4g}')
        if self.fit:
            p.setPen(QPen(QColor('#0f766e'), 2))
            p.drawLine(*xy(lo, self.fit['slope']*lo+self.fit['intercept']),
                       *xy(hi, self.fit['slope']*hi+self.fit['intercept']))
        p.setPen(QPen(QColor('#1d4ed8'), 2))
        for point in self.points:
            x, y = xy(point['x'], point['y'])
            p.drawEllipse(x-4, y-4, 8, 8)
