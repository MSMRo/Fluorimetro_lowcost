import json

import pytest

from upch_gui.protocol import ProtocolError, decode_message, encode_message


def test_round_trip_preserves_a_telemetry_message():
    message = {
        "type": "telemetry",
        "sequence": 3,
        "mode": "Raw Count",
        "values": {"sensor_90": 1234, "sensor_180": 5678},
    }

    encoded = encode_message(message)

    assert encoded.endswith(b"\n")
    assert decode_message(encoded) == message


@pytest.mark.parametrize(
    "payload",
    (
        b"not-json\n",
        b"[]\n",
        b'{"type": 3}\n',
        b'{"command": "get_state"}\n',
    ),
)
def test_decoder_rejects_invalid_messages(payload):
    with pytest.raises(ProtocolError):
        decode_message(payload)


def test_encoder_does_not_mutate_payload():
    message = {"type": "state", "mode": "Irradiance"}

    encoded = encode_message(message)

    assert json.loads(encoded) == message

