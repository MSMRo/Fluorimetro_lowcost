"""Cliente USB serial no bloqueante para JSON Lines."""

from __future__ import annotations

from typing import Any

import serial
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from serial.tools import list_ports

from protocol import ProtocolError, decode_message, encode_message


class SerialClient(QObject):
    message_received = pyqtSignal(dict)
    connection_changed = pyqtSignal(bool, str)
    error_received = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._serial: serial.Serial | None = None
        self._buffer = b""
        self._discarding = False
        self._timer = QTimer(self)
        self._timer.setInterval(8)
        self._timer.timeout.connect(self._poll)

    @staticmethod
    def available_ports() -> list[tuple[str, str]]:
        ports = [(port.device, port.description) for port in list_ports.comports()]
        return sorted(ports, key=lambda item: SerialClient._port_priority(item[0]))

    @staticmethod
    def _port_priority(device: str) -> tuple[int, str]:
        name = device.lower()
        is_usb = any(marker in name for marker in ('usbmodem', 'usbserial', 'wch', 'slab'))
        is_debug = 'debug-console' in name
        return (0 if is_usb else 2 if is_debug else 1, name)

    @property
    def connected_port(self) -> str | None:
        return str(self._serial.port) if self.is_connected else None

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect_to(self, port_name: str) -> None:
        self.disconnect(emit_status=False)
        # Opening a USB CDC port can begin halfway through a JSON frame. Drop
        # through the first newline to establish a deterministic line boundary.
        self._discarding = True
        try:
            self._serial = serial.Serial(port_name, baudrate=115200, timeout=0, write_timeout=1)
        except serial.SerialException as error:
            self._serial = None
            self.connection_changed.emit(False, f"No se pudo abrir {port_name}: {error}")
            return
        self._buffer = b""
        self._timer.start()
        self.connection_changed.emit(True, f"Conectado a {port_name}")
        self.send({"type": "command", "command": "get_state"})

    def disconnect(self, emit_status: bool = True) -> None:
        self._timer.stop()
        if self._serial is not None:
            try:
                self._serial.close()
            finally:
                self._serial = None
        if emit_status:
            self.connection_changed.emit(False, "Desconectado")

    def send(self, message: dict[str, Any]) -> None:
        if not self.is_connected or self._serial is None:
            self.error_received.emit("Conecte el equipo antes de enviar una orden.")
            return
        try:
            self._serial.write(encode_message(message))
        except (serial.SerialException, ProtocolError) as error:
            self.error_received.emit(f"No se pudo enviar la orden: {error}")
            self.disconnect()

    def _poll(self) -> None:
        if not self.is_connected or self._serial is None:
            return
        try:
            available = self._serial.in_waiting
            if available:
                data = self._serial.read(min(available, 4096))
                if self._discarding:
                    if b'\n' not in data:
                        return
                    data = data.split(b'\n', 1)[1]
                    self._discarding = False
                self._buffer += data
        except serial.SerialException as error:
            self.error_received.emit(f"Conexión perdida: {error}")
            self.disconnect()
            return
        while b"\n" in self._buffer:
            raw_message, self._buffer = self._buffer.split(b"\n", 1)
            if len(raw_message) > 1024:
                self.error_received.emit('Se descartó una línea serial demasiado larga.')
                continue
            if not raw_message:
                continue
            try:
                self.message_received.emit(decode_message(raw_message))
            except ProtocolError as error:
                self.error_received.emit(str(error))
        if len(self._buffer) > 1024:
            self._buffer = b''
            self._discarding = True
            self.error_received.emit('Se descartó una línea serial demasiado larga.')
