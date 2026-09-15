"""Ventana principal de observación y control del colorímetro."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from .exporter import CsvExporter
from .live_plot import LivePlot
from .serial_client import SerialClient


MODES = ("Raw Count", "Irradiance", "Relative Units")
GAINS = ("low", "med", "high", "max")
INTEGRATION_TIMES = ("100ms", "200ms", "300ms", "400ms", "500ms", "600ms")


class MainWindow(QMainWindow):
    """Interfaz PyQt que refleja los valores enviados por el firmware."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("UPCH GUI · Colorímetro")
        self.setMinimumSize(900, 660)
        self.exporter = CsvExporter()
        self.client = SerialClient(self)
        self.client.message_received.connect(self.handle_message)
        self.client.connection_changed.connect(self.handle_connection_changed)
        self.client.error_received.connect(self.handle_error)
        self._build_interface()
        self.refresh_ports()
        self._set_device_controls_enabled(False)

    def _build_interface(self) -> None:
        container = QWidget(self)
        layout = QVBoxLayout(container)
        layout.setSpacing(14)
        layout.addLayout(self._connection_bar())
        layout.addLayout(self._measurement_cards())
        layout.addWidget(self._controls())
        self.plot = LivePlot(self)
        layout.addWidget(self.plot, stretch=1)
        layout.addWidget(self._activity_log())
        self.setCentralWidget(container)
        self.setStyleSheet(
            "QMainWindow { background: #f4f7f9; color: #17212b; }"
            "QGroupBox { font-weight: 600; border: 1px solid #ccd5dd; border-radius: 8px; margin-top: 10px; padding: 12px; }"
            "QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }"
            "QFrame#reading { background: white; border: 1px solid #ccd5dd; border-radius: 10px; }"
            "QPushButton { min-height: 28px; padding: 2px 10px; }"
            "QPlainTextEdit { background: #101820; color: #d5e1ea; border-radius: 8px; }"
        )

    def _connection_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Puerto USB:"))
        self.port_selector = QComboBox()
        self.port_selector.setMinimumWidth(350)
        layout.addWidget(self.port_selector)
        refresh = QPushButton("Actualizar puertos")
        refresh.clicked.connect(self.refresh_ports)
        layout.addWidget(refresh)
        self.connect_button = QPushButton("Conectar")
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)
        self.connection_status = QLabel("Desconectado")
        layout.addWidget(self.connection_status)
        layout.addStretch()
        return layout

    def _measurement_cards(self) -> QGridLayout:
        layout = QGridLayout()
        self.mode_label = QLabel("Modo del firmware: —")
        self.mode_label.setStyleSheet("font-size: 17px; font-weight: 600;")
        layout.addWidget(self.mode_label, 0, 0, 1, 2)
        self.sensor_90_value = QLabel("—")
        self.sensor_180_value = QLabel("—")
        layout.addWidget(self._reading_card("Sensor 90°", self.sensor_90_value), 1, 0)
        layout.addWidget(self._reading_card("Sensor 180°", self.sensor_180_value), 1, 1)
        self.battery_label = QLabel("Batería: —")
        layout.addWidget(self.battery_label, 2, 0, 1, 2)
        return layout

    @staticmethod
    def _reading_card(title: str, value_label: QLabel) -> QFrame:
        frame = QFrame()
        frame.setObjectName("reading")
        layout = QVBoxLayout(frame)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #52616e;")
        value_label.setStyleSheet("font-size: 30px; font-weight: 600; color: #0d5273;")
        value_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame

    def _controls(self) -> QGroupBox:
        group = QGroupBox("Controles del equipo")
        layout = QGridLayout(group)
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(MODES)
        self.mode_selector.activated.connect(self.send_mode)
        layout.addWidget(QLabel("Modo"), 0, 0)
        layout.addWidget(self.mode_selector, 0, 1)

        self.sensor_90_gain = self._selector(GAINS, lambda value: self.send_sensor_setting("sensor_90", "gain", value))
        self.sensor_90_time = self._selector(INTEGRATION_TIMES, lambda value: self.send_sensor_setting("sensor_90", "integration_time", value))
        self.sensor_180_gain = self._selector(GAINS, lambda value: self.send_sensor_setting("sensor_180", "gain", value))
        self.sensor_180_time = self._selector(INTEGRATION_TIMES, lambda value: self.send_sensor_setting("sensor_180", "integration_time", value))
        sensor_90_form = QFormLayout()
        sensor_90_form.addRow("Ganancia 90°", self.sensor_90_gain)
        sensor_90_form.addRow("Integración 90°", self.sensor_90_time)
        sensor_180_form = QFormLayout()
        sensor_180_form.addRow("Ganancia 180°", self.sensor_180_gain)
        sensor_180_form.addRow("Integración 180°", self.sensor_180_time)
        layout.addLayout(sensor_90_form, 1, 0)
        layout.addLayout(sensor_180_form, 1, 1)
        self.normalize_button = QPushButton("Tomar normalización")
        self.normalize_button.clicked.connect(lambda: self.client.send({"type": "command", "command": "normalize"}))
        layout.addWidget(self.normalize_button, 2, 0)
        self.export_button = QPushButton("Exportar CSV")
        self.export_button.clicked.connect(self.export_csv)
        layout.addWidget(self.export_button, 2, 1)
        return group

    @staticmethod
    def _selector(values: tuple[str, ...], callback) -> QComboBox:
        selector = QComboBox()
        selector.addItems(values)
        selector.activated.connect(callback)
        return selector

    def _activity_log(self) -> QGroupBox:
        group = QGroupBox("Actividad")
        layout = QVBoxLayout(group)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(100)
        self.log.setMaximumHeight(130)
        layout.addWidget(self.log)
        return group

    def refresh_ports(self) -> None:
        selected_port = self.port_selector.currentData()
        self.port_selector.clear()
        for device, description in self.client.available_ports():
            self.port_selector.addItem(f"{device} — {description}", device)
        index = self.port_selector.findData(selected_port)
        if index >= 0:
            self.port_selector.setCurrentIndex(index)

    def toggle_connection(self) -> None:
        if self.client.is_connected:
            self.client.disconnect()
            return
        port_name = self.port_selector.currentData()
        if not port_name:
            self.handle_error("Seleccione el puerto USB de datos del PyBadge.")
            return
        self.client.connect_to(port_name)

    def send_mode(self, mode: str) -> None:
        self.client.send({"type": "command", "command": "set_mode", "mode": mode})

    def send_sensor_setting(self, sensor: str, setting: str, value: str) -> None:
        self.client.send(
            {
                "type": "command",
                "command": "set_sensor_setting",
                "sensor": sensor,
                "setting": setting,
                "value": value,
            }
        )

    def handle_message(self, message: dict[str, Any]) -> None:
        message_type = message.get("type")
        if message_type == "telemetry":
            self.exporter.append(datetime.now(timezone.utc), message)
            values = message.get("values", {})
            self.plot.append(values.get("sensor_90"), values.get("sensor_180"))
            self._update_readings(message)
        elif message_type in {"hello", "state"}:
            self._update_readings(message)
        elif message_type == "error":
            self.handle_error(message.get("message", "El firmware informó un error."))
        elif message_type == "ack":
            self._append_log(f"Confirmado: {message.get('command', 'comando')}")

    def _update_readings(self, message: dict[str, Any]) -> None:
        mode = message.get("mode")
        if isinstance(mode, str):
            self.mode_label.setText(f"Modo del firmware: {mode}")
            self._set_combo_value(self.mode_selector, mode)
        labels = message.get("labels", {})
        display_values = message.get("display_values", {})
        units = message.get("units") or ""
        if display_values:
            self.sensor_90_value.setText(self._format_reading(display_values.get("sensor_90"), units))
            self.sensor_180_value.setText(self._format_reading(display_values.get("sensor_180"), units))
            self._append_log(f"Telemetría {message.get('sequence', '—')}: {labels.get('sensor_90', '')}")
        sensors = message.get("sensors", {})
        self._set_sensor_controls(sensors)
        battery = message.get("battery", {})
        voltage = battery.get("voltage")
        if isinstance(voltage, (int, float)):
            self.battery_label.setText(f"Batería: {voltage:.1f} V")

    @staticmethod
    def _format_reading(value: object, units: str) -> str:
        if value in (None, ""):
            return "—"
        return f"{value} {units}".strip()

    def _set_sensor_controls(self, sensors: dict[str, Any]) -> None:
        sensor_90 = sensors.get("sensor_90", {})
        sensor_180 = sensors.get("sensor_180", {})
        self._set_combo_value(self.sensor_90_gain, sensor_90.get("gain"))
        self._set_combo_value(self.sensor_90_time, sensor_90.get("integration_time"))
        self._set_combo_value(self.sensor_180_gain, sensor_180.get("gain"))
        self._set_combo_value(self.sensor_180_time, sensor_180.get("integration_time"))

    @staticmethod
    def _set_combo_value(combo: QComboBox, value: object) -> None:
        if not isinstance(value, str) or combo.findText(value) < 0:
            return
        blocker = QSignalBlocker(combo)
        combo.setCurrentText(value)
        del blocker

    def handle_connection_changed(self, connected: bool, status: str) -> None:
        self.connection_status.setText(status)
        self.connect_button.setText("Desconectar" if connected else "Conectar")
        self._set_device_controls_enabled(connected)
        self._append_log(status)

    def _set_device_controls_enabled(self, enabled: bool) -> None:
        for control in (
            self.mode_selector,
            self.sensor_90_gain,
            self.sensor_90_time,
            self.sensor_180_gain,
            self.sensor_180_time,
            self.normalize_button,
        ):
            control.setEnabled(enabled)

    def handle_error(self, message: str) -> None:
        self._append_log(f"Error: {message}")
        self.statusBar().showMessage(message, 8_000)

    def _append_log(self, message: str) -> None:
        self.log.appendPlainText(message)

    def export_csv(self) -> None:
        destination, _ = QFileDialog.getSaveFileName(self, "Guardar telemetría", "mediciones_upch.csv", "CSV (*.csv)")
        if not destination:
            return
        try:
            self.exporter.write(destination)
        except OSError as error:
            QMessageBox.critical(self, "No se pudo exportar", str(error))
            return
        self._append_log(f"CSV exportado: {destination} ({self.exporter.count} lecturas)")

    def closeEvent(self, event) -> None:  # noqa: N802 - nombre requerido por Qt
        self.client.disconnect()
        event.accept()

