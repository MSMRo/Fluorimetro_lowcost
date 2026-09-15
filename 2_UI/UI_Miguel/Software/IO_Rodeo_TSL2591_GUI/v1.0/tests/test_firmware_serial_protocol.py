import importlib
import json
import pathlib
import sys
import types


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[4]
FIRMWARE_SOURCE = (
    REPOSITORY_ROOT
    / "Firmware"
    / "IO_Rodeo_PyBadge"
    / "v2.0_tsl2591_gui"
    / "src"
)


class FakeCdcPort:
    def __init__(self, incoming=b""):
        self.incoming = incoming
        self.written = []

    @property
    def in_waiting(self):
        return len(self.incoming)

    def read(self, count):
        result = self.incoming[:count]
        self.incoming = self.incoming[count:]
        return result

    def write(self, payload):
        self.written.append(payload)
        return len(payload)


def load_protocol(port):
    sys.modules["usb_cdc"] = types.SimpleNamespace(data=port)
    sys.path.insert(0, str(FIRMWARE_SOURCE))
    sys.modules.pop("serial_protocol", None)
    return importlib.import_module("serial_protocol")


def test_firmware_protocol_emits_json_line_with_sequence():
    port = FakeCdcPort()
    protocol_module = load_protocol(port)
    protocol = protocol_module.UsbSerialProtocol()

    protocol.send("telemetry", mode="Raw Count")

    message = json.loads(port.written[0])
    assert message == {"type": "telemetry", "sequence": 1, "mode": "Raw Count"}


def test_firmware_protocol_reads_only_valid_command_messages():
    port = FakeCdcPort(
        b'{"type":"command","command":"get_state"}\n'
        b'{"type":"telemetry","mode":"Raw Count"}\n'
    )
    protocol_module = load_protocol(port)
    protocol = protocol_module.UsbSerialProtocol()

    commands = protocol.poll_commands()

    assert commands == [{"type": "command", "command": "get_state"}]
    error_message = json.loads(port.written[0])
    assert error_message["type"] == "error"
