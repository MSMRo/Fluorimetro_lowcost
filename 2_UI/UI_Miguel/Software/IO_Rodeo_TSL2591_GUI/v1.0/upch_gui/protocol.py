"""Contrato JSON Lines compartido por la GUI y el firmware."""

from __future__ import annotations

import json
from typing import Any


class ProtocolError(ValueError):
    """El mensaje no respeta el contrato JSON Lines de UPCH."""


def encode_message(message: dict[str, Any]) -> bytes:
    """Codifica un mensaje como una única línea UTF-8."""
    _validate_message(message)
    return (json.dumps(message, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def decode_message(payload: bytes | str) -> dict[str, Any]:
    """Decodifica y valida un mensaje JSON Lines."""
    try:
        message = json.loads(payload)
    except (TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProtocolError("El dispositivo envió JSON inválido.") from error
    _validate_message(message)
    return message


def _validate_message(message: Any) -> None:
    if not isinstance(message, dict):
        raise ProtocolError("Cada mensaje debe ser un objeto JSON.")
    message_type = message.get("type")
    if not isinstance(message_type, str) or not message_type:
        raise ProtocolError("Cada mensaje debe incluir un campo 'type' de texto.")

