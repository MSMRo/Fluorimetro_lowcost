"""Ventana principal basada en la arquitectura de upch_GUI."""

from __future__ import annotations

from datetime import datetime, timezone
from math import ceil
from pathlib import Path
from time import monotonic
from uuid import uuid4
from typing import Any

from PyQt6.QtCore import Qt, QSignalBlocker, QTimer
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QTabWidget,
    QScrollArea,
)
from experiments import Experiments
from results_quality import ResultsQuality
from theme import configure_theme, STYLE
from PyQt6.QtWidgets import QHeaderView, QSizePolicy, QLayout, QSpinBox
from display_mirror import DisplayMirror

from exporter import CsvExporter
from protocol import CHANNEL_KEYS, PLOT_KEYS, ProtocolError, parse_telemetry
from serial_client import SerialClient
from spectral_plot import SpectralPlot
from telemetry_writer import TelemetryWriter

GAINS = ("0.5x", "1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x", "256x", "512x")
INTEGRATION_TIMES = ("50ms", "100ms", "200ms", "300ms", "400ms", "600ms")


class MainWindow(QMainWindow):
    def __init__(self, session_dir=None, records_dir=None) -> None:
        super().__init__()
        configure_theme()
        self.setWindowTitle("UPCH: AS7341 multicanal")
        self.setMinimumSize(980, 680)
        self.resize(1120, 820)
        self.session_dir = Path(session_dir) if session_dir else Path(__file__).resolve().parents[1] / 'sessions' / (datetime.now().strftime('%Y%m%d_%H%M%S_') + uuid4().hex[:8])
        self.records_dir = Path(records_dir) if records_dir else Path(__file__).resolve().parents[1] / 'records'
        self.exporter = CsvExporter(self.session_dir / 'telemetry.csv')
        self.telemetry_writer = TelemetryWriter(self.exporter, self)
        self.telemetry_writer.error_received.connect(self._handle_storage_error)
        self._recording_exporter: CsvExporter | None = None
        self._recording_path: Path | None = None
        self.last_recording_path: Path | None = None
        self.last_recording_error: str | None = None
        self._verified = False
        self._last_sequence = None
        self._last_probe = 0
        self._scale_channels: dict[str, int] | None = None
        self.client = SerialClient(self)
        self.client.message_received.connect(self.handle_message)
        self.client.connection_changed.connect(self.handle_connection_changed)
        self.client.error_received.connect(self.handle_error)
        self._build_interface()
        self.experiments.autosave_path = self.session_dir / 'experiment.json'
        self.experiments.capture_requested.connect(self.client.send)
        self._append_log(f'Respaldo técnico de sesión: {self.session_dir}')
        self._last_telemetry_at = None
        self._received_count = 0
        self.link_status = QLabel('Desconectado | Puerto: — | 115200 baudios')
        self.link_status.setAccessibleName('Estado del enlace USB y recepción de mediciones')
        self.link_status.setToolTip('El puerto corresponde al enlace abierto, no al seleccionado. Sin datos tras 5 s indica ausencia de telemetría válida.')
        self.statusBar().addPermanentWidget(self.link_status)
        self.link_timer = QTimer(self)
        self.link_timer.setInterval(500)
        self.link_timer.timeout.connect(self.refresh_link_status)
        self.link_timer.start()
        self.refresh_ports()
        self._set_device_controls_enabled(False)

    def _build_interface(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 18, 20, 10)
        layout.addLayout(self._brand_header())
        layout.addLayout(self._connection_bar())
        self.tabs = QTabWidget()
        acquisition = QWidget()
        acquisition_layout = QVBoxLayout(acquisition)
        acquisition_layout.setContentsMargins(16, 16, 16, 16)
        acquisition_layout.setSpacing(14)
        acquisition_layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        acquisition_layout.addLayout(self._measurement_area())
        acquisition_layout.addWidget(self._controls())
        acquisition_layout.addWidget(self._activity_log())
        self.acquisition_scroll = QScrollArea()
        self.acquisition_scroll.setWidgetResizable(True)
        self.acquisition_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.acquisition_scroll.setWidget(acquisition)
        self.tabs.addTab(self.acquisition_scroll, 'Adquisición en vivo')
        self.mirror = DisplayMirror(self)
        self.mirror.command_requested.connect(self.client.send)
        self.tabs.addTab(self.mirror, 'IO Rodeo y pantalla')
        self.experiments = Experiments(self)
        self.experiments.setMinimumHeight(840)
        self.experiments_scroll = QScrollArea()
        self.experiments_scroll.setWidgetResizable(True)
        self.experiments_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.experiments_scroll.setWidget(self.experiments)
        self.tabs.addTab(self.experiments_scroll, 'Experimentos y calibración')
        self.results_quality = ResultsQuality(self)
        self.results_scroll = QScrollArea()
        self.results_scroll.setWidgetResizable(True)
        self.results_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.results_quality.setMinimumHeight(740)
        self.results_scroll.setWidget(self.results_quality)
        self.tabs.addTab(self.results_scroll, 'Resultados y calidad')
        self.experiments.data_changed.connect(self.results_quality.set_session)
        self.results_quality.open_requested.connect(self.open_results_session)
        self.results_quality.set_session(self.experiments.session_data())
        layout.addWidget(self.tabs)
        self.setCentralWidget(container)
        self.setStyleSheet(STYLE)

    def open_results_session(self):
        self.experiments.load_session()
        self.results_quality.export_status.setText(self.experiments.status.text())

    def _brand_header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(16)

        logo = QLabel()
        logo.setObjectName('institutionLogo')
        logo.setAccessibleName('Universidad Peruana Cayetano Heredia')
        logo.setToolTip('Universidad Peruana Cayetano Heredia')
        logo.setFixedSize(220, 64)
        logo.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        logo_path = Path(__file__).resolve().parent / 'assets' / 'upch_logo.png'
        pixmap = QPixmap(str(logo_path))
        if pixmap.isNull():
            logo.setText('UPCH')
            logo.setStyleSheet('font-size: 24px; font-weight: 700; color: #b20d35;')
        else:
            logo.setPixmap(pixmap.scaled(
                logo.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation))
        header.addWidget(logo)

        separator = QFrame()
        separator.setObjectName('brandSeparator')
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFixedHeight(44)
        separator.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        header.addWidget(separator, 0, Qt.AlignmentFlag.AlignVCenter)

        title = QLabel('Spectral Lab')
        title.setObjectName('brandTitle')
        title.setAccessibleName('Spectral Lab')
        identity = QVBoxLayout()
        identity.setContentsMargins(0, 0, 0, 0)
        identity.setSpacing(1)
        identity.addWidget(title)
        subtitle = QLabel('Caracterización óptica con Arduino Mega, AS7341 y Nokia 5110')
        subtitle.setObjectName('subtitle')
        identity.addWidget(subtitle)
        header.addLayout(identity)
        header.addStretch(1)
        return header

    def _connection_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Puerto USB:"))
        self.port_selector = QComboBox()
        self.port_selector.setMinimumWidth(240)
        layout.addWidget(self.port_selector, 1)
        refresh = QPushButton("Actualizar puertos")
        refresh.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh)
        self.connect_button = QPushButton("Conectar")
        self.connect_button.setObjectName('primary')
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)
        self.connection_status = QLabel("Desconectado")
        self.connection_status.setObjectName('badge')
        layout.addWidget(self.connection_status)
        return layout

    def _measurement_area(self) -> QGridLayout:
        layout = QGridLayout()
        self.summary_label = QLabel("Esperando una lectura del AS7341")
        self.summary_label.setStyleSheet("font-size: 17px; font-weight: 600;")
        layout.addWidget(self.summary_label, 0, 0)
        scale_controls = QVBoxLayout()
        self.scale_label = QLabel('Límite Y fijo (cuentas)')
        scale_controls.addWidget(self.scale_label)
        self.scale_maximum = QSpinBox()
        self.scale_maximum.setRange(1, 65535)
        self.scale_maximum.setValue(2000)
        self.scale_maximum.setKeyboardTracking(False)
        self.scale_maximum.setAccessibleName('Límite superior fijo del eje vertical en cuentas')
        self.scale_maximum.setToolTip('El eje empieza en cero. Activa Auto para ajustar su límite a las lecturas.')
        self.scale_maximum.valueChanged.connect(lambda value: self.plot.set_maximum(value))
        scale_row = QHBoxLayout()
        scale_row.setSpacing(8)
        scale_row.addWidget(self.scale_maximum, 1)
        self.auto_scale_button = QPushButton('Auto')
        self.auto_scale_button.setCheckable(True)
        self.auto_scale_button.setAccessibleName('Activar o desactivar la escala vertical automática')
        self.auto_scale_button.setToolTip('Ajusta F1–F8 con margen superior. NIR, Clear y cuentas saturadas no determinan la escala. Pulsa otra vez para volver al modo fijo.')
        self.auto_scale_button.setStyleSheet(
            'QPushButton:checked { background: #1e40af; color: white; border-color: #1e40af; }'
            'QPushButton:checked:hover { background: #1e3a8a; }'
        )
        self.auto_scale_button.toggled.connect(self.toggle_auto_scale)
        scale_row.addWidget(self.auto_scale_button)
        scale_controls.addLayout(scale_row)
        layout.addLayout(scale_controls, 0, 1)
        self.plot = SpectralPlot(self)
        self.plot.setMinimumWidth(360)
        self.plot.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.plot, 1, 0)
        self.table = QTableWidget(len(CHANNEL_KEYS), 2, self)
        self.table.setHorizontalHeaderLabels(("Canal", "Cuenta"))
        self.table.setMinimumWidth(220)
        self.table.setMaximumWidth(280)
        self.table.setMinimumHeight(340)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(28)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, channel in enumerate(CHANNEL_KEYS):
            self.table.setItem(row, 0, QTableWidgetItem(channel.upper()))
            self.table.setItem(row, 1, QTableWidgetItem("—"))
        layout.addWidget(self.table, 1, 1)
        layout.setColumnStretch(0, 1)
        return layout

    def _controls(self) -> QGroupBox:
        group = QGroupBox("Controles del AS7341")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(20)
        layout.setVerticalSpacing(12)
        self.gain_selector = self._selector(GAINS, lambda value: self.send_setting("set_gain", value))
        self.integration_selector = self._selector(INTEGRATION_TIMES, lambda value: self.send_setting("set_integration", value))
        self.gain_selector.setCurrentText('128x')
        self.integration_selector.setCurrentText('300ms')
        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.addRow("Ganancia", self.gain_selector)
        form.addRow("Integración", self.integration_selector)
        self.pwm_control = QSpinBox()
        self.pwm_control.setRange(0, 100)
        self.pwm_control.setValue(25)
        self.pwm_control.setSuffix(" %")
        self.pwm_control.setKeyboardTracking(False)
        self.pwm_control.setAccessibleName("Potencia PWM del LED externo en porcentaje")
        self.pwm_control.setToolTip("PWM del LED en D11. El valor inicial 25 % equivale a analogWrite(64).")
        self.pwm_control.valueChanged.connect(lambda value: self.send_setting("set_pwm", value))
        form.addRow("PWM LED D11", self.pwm_control)
        layout.addLayout(form, 0, 0)
        actions = QVBoxLayout()
        self.record_button = QPushButton("Iniciar grabación")
        self.record_button.setObjectName("recordButton")
        self.record_button.setProperty("recording", False)
        self.record_button.setAccessibleName("Iniciar grabación de datos raw en CSV")
        self.record_button.clicked.connect(self.toggle_recording)
        actions.addWidget(self.record_button)
        self.record_status = QLabel("Sin grabar. El CSV se guardará en records/")
        self.record_status.setObjectName("secondaryText")
        self.record_status.setWordWrap(True)
        actions.addWidget(self.record_status)
        self.pause_plot_button = QPushButton("Pausar gráfica")
        self.pause_plot_button.setCheckable(True)
        self.pause_plot_button.setAccessibleName("Pausar solo la animación de la gráfica")
        self.pause_plot_button.setToolTip("La tabla, la telemetría y la grabación continúan recibiendo datos.")
        self.pause_plot_button.toggled.connect(self.toggle_plot_pause)
        actions.addWidget(self.pause_plot_button)
        layout.addLayout(actions, 0, 1)
        return group

    @staticmethod
    def _selector(values: tuple[str, ...], callback) -> QComboBox:
        selector = QComboBox()
        selector.addItems(values)
        selector.textActivated.connect(callback)
        return selector

    def _activity_log(self) -> QGroupBox:
        group = QGroupBox("Actividad")
        layout = QVBoxLayout(group)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(100)
        self.log.setMaximumHeight(120)
        layout.addWidget(self.log)
        return group

    def refresh_ports(self) -> None:
        selected_port = self.port_selector.currentData()
        self.port_selector.clear()
        for device, description in self.client.available_ports():
            self.port_selector.addItem(f"{device}, {description}", device)
        index = self.port_selector.findData(selected_port)
        if index >= 0:
            self.port_selector.setCurrentIndex(index)

    def toggle_connection(self) -> None:
        if self.client.is_connected:
            self.client.disconnect()
            return
        port_name = self.port_selector.currentData()
        if not port_name:
            self.handle_error("Seleccione el puerto USB del Arduino Mega.")
            return
        self.client.connect_to(port_name)

    def send_setting(self, command: str, value: str | int) -> None:
        if self.experiments.pending:
            self.experiments.cancel('Captura cancelada por cambio de configuración.')
        self.client.send({"type": "command", "command": command, "value": value})

    def handle_message(self, message: dict[str, Any]) -> None:
        message_type = message.get("type")
        if message_type == "telemetry":
            if not self._verified:
                return
            try:
                telemetry = parse_telemetry(message)
            except ProtocolError as error:
                self.handle_error(str(error))
                return
            if telemetry.get('display_lines') is None:
                self.handle_error('El firmware no envió el espejo del display requerido por protocolo 2.')
                return
            if self._last_sequence is not None and telemetry['sequence'] <= self._last_sequence:
                self._stop_recording('Grabación finalizada por reinicio o repetición de secuencia.')
                self.experiments.set_connected(False)
                self._verified = False
                self._last_telemetry_at = None
                self.refresh_link_status()
                self.handle_error('Reinicio o secuencia repetida: verificando equipo nuevamente.')
                self._last_sequence = None
                return
            self._last_sequence = telemetry['sequence']
            if not self.telemetry_writer.append(
                datetime.now(timezone.utc), telemetry, self._recording_exporter
            ):
                return
            self._last_telemetry_at = monotonic()
            self._received_count += 1
            self.refresh_link_status()
            self._update_telemetry(telemetry)
            self.mirror.feed(telemetry)
            self.experiments.feed(telemetry)
        elif message_type == "state":
            self._verified = (message.get('device') == 'upch-mega-as7341'
                              and type(message.get('protocol')) is int and message['protocol'] == 2
                              and isinstance(message.get('capabilities'), list)
                              and 'pwm_control' in message['capabilities']
                              and message.get('sensor_ready') is True)
            if not self._verified:
                self._stop_recording('Grabación finalizada: equipo incompatible o sensor no disponible.')
                self.experiments.set_connected(False)
                self.handle_error('Equipo incompatible o AS7341 no disponible. Se requiere firmware Mega 2.3.0 con control PWM.')
                lines = message.get('display_lines')
                if (isinstance(lines, list) and len(lines) == 6
                        and all(isinstance(line, str) and len(line) <= 14 and all(32 <= ord(c) <= 126 for c in line) for line in lines)):
                    self.mirror.nokia.setText('\n'.join(lines))
            if type(message.get('auto_page')) is bool:
                self.mirror.auto.setChecked(message['auto_page'])
            self.refresh_link_status()
            self._update_state(message)
        elif message_type == "ack":
            self._append_log(f"Confirmado: {message.get('command', 'comando')}")
        elif message_type == "error":
            self.experiments.cancel('Captura cancelada por error del firmware.')
            if message.get('code') in ('sensor_missing', 'sensor_read_failed', 'sensor_config_failed'):
                self._stop_recording('Grabación finalizada por error del AS7341.')
                self._last_telemetry_at = None
                self.experiments.set_connected(False)
                self.refresh_link_status()
            self.handle_error(f"Firmware: {message.get('code', 'error')}")

    def _update_telemetry(self, telemetry: dict[str, Any]) -> None:
        channels = telemetry["channels"]
        self._scale_channels = channels.copy()
        self.plot.set_channels(channels)
        if self.auto_scale_button.isChecked() and not self.plot.paused:
            self._update_auto_scale()
        for row, channel in enumerate(CHANNEL_KEYS):
            value = channels[channel]
            self.table.item(row, 1).setText("OVFL" if value >= 65535 else str(value))
        self.summary_label.setText(f"Muestra {telemetry['sequence']}, ganancia {telemetry['gain']}, integración {telemetry['integration_time']}")
        self._update_state(telemetry)

    def toggle_auto_scale(self, enabled: bool) -> None:
        self.scale_label.setText('Límite Y automático (cuentas)' if enabled else 'Límite Y fijo (cuentas)')
        self.auto_scale_button.setText('Auto activo' if enabled else 'Auto')
        self.scale_maximum.setEnabled(not enabled)
        if enabled:
            self._update_auto_scale()

    def _update_auto_scale(self) -> None:
        displayed = self.plot.display_values
        if self.plot.paused:
            values = [v for v in (displayed or ()) if 0 <= v < 65535]
        elif self._scale_channels is not None:
            values = [self._scale_channels[key] for key in PLOT_KEYS if self._scale_channels[key] < 65535]
            # No recortar la curva anterior mientras termina su transición visual.
            if displayed is not None:
                values += [v for key,v in zip(PLOT_KEYS,displayed)
                           if self._scale_channels[key] < 65535 and 0 <= v < 65535]
        else:
            return
        if not values:
            return  # Sin canales cuantificables, conservar el último rango.
        peak = ceil(max(values))
        target = max(10, (peak * 110 + 99) // 100)
        step = 10 ** max(0, len(str(target)) - 2)
        maximum = min(65535, ((target + step - 1) // step) * step)
        self.scale_maximum.setValue(maximum)

    def _update_state(self, state: dict[str, Any]) -> None:
        self._set_combo_value(self.gain_selector, state.get("gain"))
        self._set_combo_value(self.integration_selector, state.get("integration_time"))
        self._set_spin_value(self.pwm_control, state.get("pwm_percent"))

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: object) -> None:
        if not isinstance(value, str) or combo.findText(value) < 0:
            return
        blocker = QSignalBlocker(combo)
        combo.setCurrentText(value)
        del blocker

    @staticmethod
    def _set_spin_value(control: QSpinBox, value: object) -> None:
        if type(value) is not int or not control.minimum() <= value <= control.maximum():
            return
        blocker = QSignalBlocker(control)
        control.setValue(value)
        del blocker

    def handle_connection_changed(self, connected: bool, status: str) -> None:
        if not connected and self._recording_exporter is not None:
            self._stop_recording('Grabación finalizada al desconectar el equipo.')
        self._verified = False
        self._last_sequence = None
        self._last_probe = monotonic()
        self._last_telemetry_at = None
        self._received_count = 0
        self.refresh_link_status()
        self.connect_button.setText("Desconectar" if connected else "Conectar")
        self._set_device_controls_enabled(False)
        self.experiments.set_connected(False)
        self._append_log(status)

    def refresh_link_status(self) -> None:
        port = self.client.connected_port
        if port is None:
            text, color = 'Desconectado | Puerto: — | 115200 baudios', '#475569'
        elif not self._verified:
            text, color = f'Puerto abierto, verificando firmware | {port} | 115200 baudios', '#92400e'
            if monotonic() - self._last_probe >= 2:
                self._last_probe = monotonic()
                self.client.send(dict(type='command', command='get_state'))
        elif self._last_telemetry_at is None:
            text, color = f'Mega identificado, esperando datos | {port} | 115200 baudios', '#92400e'
        else:
            age = monotonic() - self._last_telemetry_at
            state = 'Conectado, recibiendo' if age < 5 else 'Puerto abierto, sin datos recientes'
            text = f'{state} | {port} | 115200 baudios | {self._received_count} muestras | Última: {age:.1f} s'
            color = '#166534' if age < 5 else '#92400e'
        self.link_status.setText(text)
        self.link_status.setStyleSheet(f'color: {color}; padding: 4px;')
        self.connection_status.setText('Verificado' if port and self._verified else ('Verificando equipo' if port else 'Desconectado'))
        pending = self.experiments.pending
        freshness_limit = 5 + (pending['settle_ms'] / 1000 if pending and not pending['frames'] else 0)
        ready = bool(port and self._verified and self._last_telemetry_at is not None and monotonic() - self._last_telemetry_at < freshness_limit)
        self._set_device_controls_enabled(ready)
        self.mirror.set_ready(ready)
        if self.experiments.connected != ready:
            self.experiments.set_connected(ready)
        if not ready:
            self.mirror.status.setText('Sin telemetría vigente. El contenido visible es la última recepción, no una confirmación actual.')
        elif self._last_telemetry_at is not None and monotonic() - self._last_telemetry_at >= 5:
            self.mirror.status.setText('Esperando estabilización solicitada. El espejo conserva la última lectura.')

    def _set_device_controls_enabled(self, enabled: bool) -> None:
        for control in (self.gain_selector, self.integration_selector, self.pwm_control):
            control.setEnabled(enabled)
        self.record_button.setEnabled(enabled or self._recording_exporter is not None)

    def handle_error(self, message: str) -> None:
        self._append_log(f"Error: {message}")
        self.statusBar().showMessage(message, 8_000)

    def _handle_storage_error(self, exporter: object, message: str) -> None:
        if exporter is not self.exporter and exporter is not None:
            if exporter is self._recording_exporter:
                self._stop_recording('Grabación incompleta por error de escritura.')
            else:
                self.handle_error(f'Un registro ya finalizado quedó incompleto: {message}')
            return
        self.handle_error(f'No se pudo registrar la lectura en disco: {message}')
        self._stop_recording('Grabación detenida por error del respaldo técnico.')
        self.experiments.set_connected(False)
        self.client.disconnect()

    def _append_log(self, message: str) -> None:
        self.log.appendPlainText(message)

    def toggle_plot_pause(self, paused: bool) -> None:
        self.plot.set_paused(paused)
        if not paused and self.auto_scale_button.isChecked():
            self._update_auto_scale()
        self.pause_plot_button.setText("Reanudar gráfica" if paused else "Pausar gráfica")
        self.pause_plot_button.setAccessibleName(
            "Reanudar la animación de la gráfica" if paused else "Pausar solo la animación de la gráfica"
        )

    def toggle_recording(self) -> None:
        if self._recording_exporter is not None:
            self._stop_recording('Grabación finalizada')
            return
        if not self._verified or self._last_telemetry_at is None or monotonic() - self._last_telemetry_at >= 5:
            self.handle_error('Conecta y verifica telemetría reciente antes de grabar.')
            return
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self._recording_path = self.records_dir / f'as7341_{timestamp}_{uuid4().hex[:8]}.csv'
        self._recording_exporter = CsvExporter(self._recording_path)
        self._set_record_button_state(True)
        self.record_status.setText(f'Grabando en {self._recording_path.name}')
        self._append_log(f'Grabación iniciada: {self._recording_path}')

    def _stop_recording(self, reason: str) -> None:
        exporter = self._recording_exporter
        path = self._recording_path
        if exporter is None or path is None:
            return
        drained = self.telemetry_writer.drain()
        error_message = self.telemetry_writer.take_error(exporter)
        try:
            if not drained:
                raise OSError('La cola de escritura no terminó dentro del tiempo esperado.')
            if error_message:
                raise OSError(error_message)
            exporter.write(path)
        except OSError as error:
            self.handle_error(f'No se pudo finalizar correctamente {path}: {error}')
            final_status = f'Registro incompleto: {path.name}. Revisa el mensaje de error.'
            self.last_recording_error = str(error)
        else:
            final_status = f'Último registro: {path.name} ({exporter.count} muestras)'
            self.last_recording_error = None
        count = exporter.count
        self.last_recording_path = path
        self._recording_exporter = None
        self._recording_path = None
        self._set_record_button_state(False)
        self.record_status.setText(final_status)
        self._append_log(f'{reason}: {path} ({count} muestras)')

    def _set_record_button_state(self, recording: bool) -> None:
        self.record_button.setProperty('recording', recording)
        self.record_button.setText('Detener y guardar CSV' if recording else 'Iniciar grabación')
        self.record_button.setAccessibleName(
            'Detener grabación y guardar CSV' if recording else 'Iniciar grabación de datos raw en CSV'
        )
        self.record_button.style().unpolish(self.record_button)
        self.record_button.style().polish(self.record_button)
        self.record_button.update()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.experiments.pending:
            answer = QMessageBox.question(self, 'Captura en curso',
                '¿Cancelar la captura en curso y cerrar? Las lecturas recibidas permanecen en el CSV.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        if self._recording_exporter is not None:
            self._stop_recording('Grabación finalizada al cerrar la aplicación')
        self.experiments.autosave()
        if self.experiments.save_error:
            QMessageBox.critical(self, 'No se pudo guardar', 'La ventana permanece abierta. Exporta el experimento a una ubicación disponible antes de cerrar.\n' + self.experiments.save_error)
            event.ignore()
            return
        if not self.telemetry_writer.close():
            QMessageBox.critical(self, 'Escritura en curso', 'No se pudo finalizar la cola de escritura. La ventana permanece abierta para proteger los datos.')
            event.ignore()
            return
        self.link_timer.stop()
        self.client.disconnect(emit_status=False)
        event.accept()
