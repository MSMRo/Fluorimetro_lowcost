import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "desktop_gui"))

from PyQt6.QtWidgets import QApplication

import serial_client
from serial_client import SerialClient


class FakeSerial:
    instances = []

    def __init__(self, port, baudrate, timeout, write_timeout):
        self.port = port
        self.is_open = True
        self.incoming = b""
        self.written = []
        self.__class__.instances.append(self)

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


class SerialClientTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def setUp(self):
        FakeSerial.instances.clear()

    def test_requests_state_and_assembles_a_fragmented_line(self):
        with patch.object(serial_client.serial, "Serial", FakeSerial):
            client = SerialClient()
            received = []
            client.message_received.connect(received.append)
            client.connect_to("/dev/fake-as7341")
            port = FakeSerial.instances[0]
            port.incoming = b'partial boot frame\n{"type":"state","gain":"128x",'
            client._poll()
            port.incoming = b'"integration_time":"100ms","page":0}\n'
            client._poll()

            self.assertIn(b'"command":"get_state"', port.written[0])
            self.assertEqual(received[0]["gain"], "128x")
            client.disconnect()

    def test_prioritizes_usb_hardware_over_debug_console(self):
        class Port:
            def __init__(self, device, description):
                self.device, self.description = device, description

        ports = [Port('/dev/cu.debug-console', 'n/a'),
                 Port('/dev/cu.Bluetooth-Incoming-Port', 'Bluetooth'),
                 Port('/dev/cu.usbmodem1301', 'IOUSBHostDevice')]
        with patch.object(serial_client.list_ports, 'comports', return_value=ports):
            self.assertEqual(SerialClient.available_ports()[0][0], '/dev/cu.usbmodem1301')


if __name__ == "__main__":
    unittest.main()
