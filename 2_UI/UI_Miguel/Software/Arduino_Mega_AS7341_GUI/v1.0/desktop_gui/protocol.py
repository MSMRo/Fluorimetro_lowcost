"""Contrato JSON Lines compartido por el firmware AS7341 y la GUI."""

from __future__ import annotations

import json
import re
from typing import Any

CHANNEL_KEYS = ("415", "445", "480", "515", "555", "590", "630", "680", "nir", "clear")
PLOT_KEYS = CHANNEL_KEYS[:8]
PLOT_WAVELENGTHS = (415, 445, 480, 515, 555, 590, 630, 680)


class ProtocolError(ValueError):
    """El mensaje no respeta el contrato JSON Lines del AS7341."""


def encode_message(message: dict[str, Any]) -> bytes:
    _validate_message(message)
    return (json.dumps(message, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def decode_message(payload: bytes | str) -> dict[str, Any]:
    try:
        message = json.loads(payload)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("El dispositivo envió JSON inválido.") from error
    _validate_message(message)
    return message


def _validate_message(message: Any) -> None:
    if not isinstance(message, dict) or "type" not in message:
        raise ProtocolError("Cada mensaje debe incluir un campo 'type'.")
    if not isinstance(message["type"], str) or not message["type"]:
        raise ProtocolError("El campo 'type' debe ser texto.")


def parse_telemetry(message: dict[str, Any]) -> dict[str, Any]:
    if message.get("type") != "telemetry":
        raise ProtocolError("El mensaje no es telemetría.")
    channels = message.get("channels")
    if not isinstance(channels, dict) or any(key not in channels for key in CHANNEL_KEYS):
        raise ProtocolError("Faltan canales AS7341.")
    if any(type(channels[key]) is not int or not 0 <= channels[key] <= 65535 for key in CHANNEL_KEYS):
        raise ProtocolError('Las cuentas deben ser enteros de 0 a 65535.')
    if any(type(message.get(key)) is not int or message[key] < 0 for key in ('sequence', 'millis')):
        raise ProtocolError('Secuencia o tiempo inválidos.')
    if type(message.get('page')) is not int or message['page'] not in (0, 1):
        raise ProtocolError('Página inválida.')
    if message.get('gain') not in ('0.5x','1x','2x','4x','8x','16x','32x','64x','128x','256x','512x') or message.get('integration_time') not in ('50ms','100ms','200ms','300ms','400ms','600ms'):
        raise ProtocolError('Configuración de sensor inválida.')
    token = message.get('capture_id', '')
    if not isinstance(token, str) or (token and not re.fullmatch('[0-9a-f]{32}', token)):
        raise ProtocolError('Identificador de captura inválido.')
    lines = message.get('display_lines')
    if message.get('display_mode', 'multi') not in ('multi', 'channel') or message.get('display_channel', '415') not in CHANNEL_KEYS:
        raise ProtocolError('Canal o modo de display inválido.')
    if lines is not None and lines != nokia_lines(message):
        raise ProtocolError('Las líneas del display no coinciden con la telemetría.')
    try:
        pwm_percent = message.get("pwm_percent", 25)
        pwm_raw = message.get("pwm_raw", (pwm_percent * 255 + 50) // 100)
        if type(pwm_percent) is not int or not 0 <= pwm_percent <= 100:
            raise ProtocolError("PWM porcentual inválido.")
        if type(pwm_raw) is not int or not 0 <= pwm_raw <= 255:
            raise ProtocolError("PWM raw inválido.")
        if pwm_raw != (pwm_percent * 255 + 50) // 100:
            raise ProtocolError("PWM porcentual y raw no coinciden.")
        return {
            "sequence": int(message["sequence"]), "millis": int(message["millis"]),
            "gain": str(message["gain"]), "integration_time": str(message["integration_time"]),
            "page": int(message["page"]), "channels": {key: int(channels[key]) for key in CHANNEL_KEYS},
            "capture_id": token, "display_lines": lines,
            "display_mode": message.get('display_mode', 'multi'),
            "display_channel": message.get('display_channel', '415'),
            "pwm_percent": pwm_percent, "pwm_raw": pwm_raw,
        }
    except (KeyError, TypeError, ValueError) as error:
        raise ProtocolError("La telemetría contiene valores inválidos.") from error


def nokia_lines(frame):
    """Contrato de las seis líneas del firmware; se usa para validar, no simular recepción."""
    if frame.get('display_mode') == 'channel':
        key = frame['display_channel']
        label = {'nir': 'NIR', 'clear': 'CLR'}.get(key, key)
        value = 'OVFL' if frame['channels'][key] >= 65535 else str(frame['channels'][key])
        return ['AS7341 @90', f'CANAL {label}', value, 'cuentas ADC',
                f"G{frame['gain']} T{frame['integration_time'][:-2]}", 'LECTURA REAL']
    page = frame['page']
    lines = [f"G{frame['gain']} T{frame['integration_time'][:-2]} {page+1}/2"]
    for key in CHANNEL_KEYS[page*5:page*5+5]:
        label = {'nir': 'NIR', 'clear': 'CLR'}.get(key, key)
        value = 'OVFL' if frame['channels'][key] >= 65535 else str(frame['channels'][key])
        lines.append(f'{label:<5} {value:>5}')
    return lines


def command(name: str, value: str | int | None = None) -> bytes:
    payload: dict[str, str | int] = {"type": "command", "command": name}
    if value is not None:
        payload["value"] = value
    return encode_message(payload)
