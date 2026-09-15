"""Registro explícito y barrido temporal, sin interpolar ni modificar cuentas."""
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import csv
import shutil

from PyQt6.QtCore import QPointF
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QComboBox, QLineEdit, QSpinBox, QFileDialog, QMessageBox)
from protocol import CHANNEL_KEYS


class TimePlot(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(280)
        self.maximum = 100
        self.points = []
        self.origin = None
        self.window = None
        self.previous = None
        self.frozen = False

    def reset(self):
        self.points.clear()
        self.origin = self.window = self.previous = None
        self.update()

    def feed(self, frame, channel):
        if self.frozen:
            return
        ms = frame['millis']
        if self.origin is None or ms < self.origin:
            self.reset()
            self.origin = ms
        elapsed = (ms - self.origin) / 1000
        window = int(elapsed // 10)
        signature = (frame['gain'], frame['integration_time'], channel)
        linked = (self.previous is not None and
                  frame['sequence'] == self.previous[0] + 1 and
                  0 < ms - self.previous[1] <= 5000 and signature == self.previous[2])
        if window != self.window:
            self.points.clear()
            self.window = window
            linked = False
        self.points.append((elapsed % 10, frame['channels'][channel], linked))
        self.points = self.points[-2000:]
        self.previous = (frame['sequence'], ms, signature)
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#0d1922'))
        w, h = self.width() - 80, self.height() - 65
        p.setPen(QColor('#718894'))
        for i in range(5):
            y = 20 + h * i / 4
            p.drawLine(QPointF(55, y), QPointF(55+w, y))
            p.drawText(3, int(y)+5, str(round(self.maximum*(1-i/4))))
        for i in range(6):
            p.drawText(int(55+w*i/5)-5, self.height()-12, f'{i*2} s')
        previous = None
        outside = False
        p.setPen(QPen(QColor('#00c4ed'), 2))
        for seconds, value, linked in self.points:
            if value >= 65535 or value > self.maximum:
                previous = None
                outside = True
                continue
            point = QPointF(55+w*seconds/10, 20+h*(1-value/self.maximum))
            if linked and previous is not None:
                p.drawLine(previous, point)
            p.drawEllipse(point, 2, 2)
            previous = point
        if outside:
            p.setPen(QColor('#ffcb70'))
            p.drawText(65, 15, 'Señal fuera de escala / OVFL; ajusta el límite Y')
        p.end()


class Acquisition(QWidget):
    def __init__(self, directory):
        super().__init__()
        self.directory = Path(directory)
        self.path = None
        self.running = False
        self.finished = False
        self.ready = False
        self.count = 0
        self.port = ''
        self.first_ms = None
        self.last_ms = None
        layout = QVBoxLayout(self)
        row = QHBoxLayout()
        self.channel = QComboBox()
        self.channel.addItems(CHANNEL_KEYS)
        self.sample = QLineEdit()
        self.sample.setPlaceholderText('Nombre de muestra')
        self.nominal = QSpinBox()
        self.nominal.setRange(0, 2000)
        self.nominal.setSpecialValueText('Sin especificar')
        self.nominal.setSuffix(' nm nominales')
        self.nominal.setToolTip('Dato introducido por el usuario; no es una longitud de onda medida.')
        for widget in (QLabel('Canal'), self.channel, self.sample, self.nominal):
            row.addWidget(widget)
        layout.addLayout(row)
        self.reading = QLabel('— cuentas, esperando medición')
        self.reading.setStyleSheet('font-size: 24px; font-weight: 600;')
        layout.addWidget(self.reading)
        self.plot = TimePlot()
        layout.addWidget(self.plot)
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel('Límite Y fijo, cuentas'))
        self.scale = QSpinBox()
        self.scale.setRange(1, 65535)
        self.scale.setValue(100)
        self.scale.setKeyboardTracking(False)
        self.scale.valueChanged.connect(self.set_scale)
        scale_row.addWidget(self.scale)
        layout.addLayout(scale_row)
        buttons = QHBoxLayout()
        self.start = QPushButton('Iniciar registro')
        self.pause = QPushButton('Pausar registro')
        self.finish = QPushButton('Finalizar')
        self.save = QPushButton('Guardar adquisición CSV…')
        self.freeze = QPushButton('Congelar gráfica')
        self.freeze.setCheckable(True)
        self.nokia = QPushButton('Mostrar canal en Nokia')
        self.nokia.setEnabled(False)
        for button in (self.start, self.pause, self.finish, self.save, self.freeze, self.nokia):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.status = QLabel('Sin registro, barrido de 10 s, escala fija, sin suavizado')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.start.clicked.connect(self.begin)
        self.pause.clicked.connect(self.pause_recording)
        self.finish.clicked.connect(self.end)
        self.save.clicked.connect(self.export)
        self.freeze.toggled.connect(self.freeze_plot)
        self.channel.currentTextChanged.connect(lambda _: self.plot.reset())
        self.update_controls()

    def set_scale(self, value):
        self.plot.maximum = value
        self.plot.update()

    def update_controls(self):
        self.start.setEnabled(self.ready and not self.running)
        self.start.setText('Reanudar registro' if self.path and not self.finished else 'Iniciar registro')
        self.pause.setEnabled(self.running)
        self.finish.setEnabled(self.path is not None and not self.finished)
        self.save.setEnabled(self.path is not None and self.count > 0)
        for field in (self.sample, self.nominal):
            field.setEnabled(not self.path or self.finished)

    def set_ready(self, ready, port):
        self.ready, self.port = ready, port or ''
        if not ready:
            self.nokia.setEnabled(False)
            self.plot.previous = None
            if self.running:
                self.pause_recording()
                self.status.setText('Registro pausado: enlace sin datos vigentes. Reanuda tras verificar conexión.')
        self.update_controls()

    def begin(self):
        if not self.ready:
            return
        if self.path is None or self.finished:
            self.path = self.directory / ('adquisicion_' + uuid4().hex + '.csv')
            self.count = 0
            self.first_ms = self.last_ms = None
        self.finished = False
        self.running = True
        self.status.setText('Registrando, todas las ventanas se conservan en disco')
        self.update_controls()

    def pause_recording(self):
        self.running = False
        self.status.setText(f'Registro pausado, {self.count} muestras conservadas')
        self.update_controls()

    def end(self):
        self.running = False
        self.finished = True
        self.status.setText(f'Registro finalizado, {self.count} muestras, {self.path}')
        self.update_controls()

    def freeze_plot(self, frozen):
        self.plot.frozen = frozen
        self.plot.previous = None
        self.freeze.setText('Reanudar gráfica' if frozen else 'Congelar gráfica')

    def feed(self, frame):
        channel = self.channel.currentText()
        value = frame['channels'][channel]
        label = 'OVFL' if value >= 65535 else str(value)
        self.reading.setText(f'{channel.upper()}, {label} cuentas')
        self.plot.feed(frame, channel)
        if not self.running:
            return
        row = dict(received_at=datetime.now(timezone.utc).isoformat(), sample=self.sample.text(),
                   nominal_led_nm=self.nominal.value() or '', port=self.port,
                   selected_channel=channel, sequence=frame['sequence'], millis=frame['millis'],
                   gain=frame['gain'], integration_time=frame['integration_time'], **frame['channels'])
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('a', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                if self.count == 0:
                    writer.writeheader()
                writer.writerow(row)
        except OSError as error:
            self.pause_recording()
            self.status.setText(f'Error de guardado: {error}')
            return
        self.count += 1
        self.first_ms = frame['millis'] if self.first_ms is None else self.first_ms
        elapsed = max(0, (frame['millis'] - self.first_ms)/1000)
        rate = (self.count-1)/elapsed if elapsed else 0
        self.status.setText(f'Registrando, {self.count} muestras, {elapsed:.1f} s transcurridos, {rate:.1f} muestras/s promedio, {self.port}')
        self.update_controls()

    def export(self):
        destination, _ = QFileDialog.getSaveFileName(self, 'Guardar adquisición', 'adquisicion.csv', 'CSV (*.csv)')
        if not destination or not self.path:
            return
        try:
            if Path(destination).resolve() != self.path.resolve():
                shutil.copyfile(self.path, destination)
        except OSError as error:
            QMessageBox.critical(self, 'Error al guardar', str(error))
