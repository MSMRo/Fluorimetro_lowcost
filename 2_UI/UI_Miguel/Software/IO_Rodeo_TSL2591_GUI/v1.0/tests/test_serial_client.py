import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from upch_gui import serial_client
from upch_gui.serial_client import SerialClient


class FakeSerial:
    instances = []

    def __init__(self, port, baudrate, timeout, write_timeout):
        self.port = port
        self.is_open = True
        self.incoming = b""
        self.written = []
        FakeSerial.instances.append(self)

    @property
    def in_waiting(self):
        return len(self.incoming)

    def read(self, count):
        payload = self.incoming[:count]
        self.incoming = self.incoming[count:]
        return payload

    def write(self, payload):
        self.written.append(payload)
        return len(payload)

    def close(self):
        self.is_open = False


def test_serial_client_requests_state_and_emits_received_json(monkeypatch):
    app = QApplication.instance() or QApplication([])
    FakeSerial.instances.clear()
    monkeypatch.setattr(serial_client.serial, "Serial", FakeSerial)
    client = SerialClient()
    received = []
    client.message_received.connect(received.append)

    client.connect_to("/dev/fake-upch")
    port = FakeSerial.instances[0]
    port.incoming = b'{"type":"telemetry","mode":"Raw Count"}\n'
    client._poll()

    assert b'"command":"get_state"' in port.written[0]
    assert received == [{"type": "telemetry", "mode": "Raw Count"}]
    client.disconnect()
    app.processEvents()


def test_serial_client_reports_invalid_data_without_crashing(monkeypatch):
    app = QApplication.instance() or QApplication([])
    FakeSerial.instances.clear()
    monkeypatch.setattr(serial_client.serial, "Serial", FakeSerial)
    client = SerialClient()
    errors = []
    client.error_received.connect(errors.append)
    client.connect_to("/dev/fake-upch")
    FakeSerial.instances[0].incoming = b'not-json\n'

    client._poll()

    assert errors == ["El dispositivo envió JSON inválido."]
    client.disconnect()
    app.processEvents()

