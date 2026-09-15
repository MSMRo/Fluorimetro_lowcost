import json
import unittest

from desktop_gui.protocol import CHANNEL_KEYS, ProtocolError, command, decode_message, parse_telemetry


class ProtocolTest(unittest.TestCase):
    def test_parses_complete_telemetry(self) -> None:
        channels = {key: index for index, key in enumerate(CHANNEL_KEYS)}
        message = decode_message(json.dumps({"type": "telemetry", "sequence": 7, "millis": 42, "gain": "128x", "integration_time": "100ms", "page": 1, "channels": channels}))
        telemetry = parse_telemetry(message)
        self.assertEqual(telemetry["channels"]["clear"], 9)
        self.assertEqual(telemetry["page"], 1)
        self.assertEqual((telemetry["pwm_percent"], telemetry["pwm_raw"]), (25, 64))

    def test_rejects_missing_channel(self) -> None:
        with self.assertRaises(ProtocolError):
            parse_telemetry({"type": "telemetry", "sequence": 1, "millis": 1, "gain": "1x", "integration_time": "50ms", "page": 0, "channels": {}})

    def test_rejects_inconsistent_pwm_metadata(self) -> None:
        channels = dict.fromkeys(CHANNEL_KEYS, 1)
        message = {
            "type": "telemetry", "sequence": 1, "millis": 1, "gain": "1x",
            "integration_time": "50ms", "pwm_percent": 50, "pwm_raw": 12,
            "page": 0, "channels": channels,
        }
        with self.assertRaises(ProtocolError):
            parse_telemetry(message)

    def test_serializes_command_as_one_line(self) -> None:
        self.assertEqual(command("set_gain", "64x"), b'{"type":"command","command":"set_gain","value":"64x"}\n')
        self.assertEqual(command("set_pwm", 75), b'{"type":"command","command":"set_pwm","value":75}\n')


if __name__ == "__main__":
    unittest.main()
