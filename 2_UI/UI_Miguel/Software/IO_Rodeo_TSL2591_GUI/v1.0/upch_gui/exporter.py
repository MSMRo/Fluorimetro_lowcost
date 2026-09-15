"""Registro y exportación de la telemetría recibida."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


class CsvExporter:
    """Mantiene las lecturas de la sesión y las exporta sin alterar datos."""

    FIELD_NAMES = (
        "received_at",
        "sequence",
        "mode",
        "sensor_90_value",
        "sensor_180_value",
        "sensor_90_display",
        "sensor_180_display",
        "units",
        "sensor_90_gain",
        "sensor_90_integration_time",
        "sensor_180_gain",
        "sensor_180_integration_time",
        "battery_voltage",
    )

    def __init__(self) -> None:
        self._rows: list[dict[str, Any]] = []

    @property
    def count(self) -> int:
        return len(self._rows)

    def append(self, received_at: datetime, message: dict[str, Any]) -> None:
        """Agrega una telemetría, conservando tanto valor como texto del equipo."""
        if message.get("type") != "telemetry":
            return
        values = message.get("values", {})
        display_values = message.get("display_values", {})
        sensors = message.get("sensors", {})
        sensor_90 = sensors.get("sensor_90", {})
        sensor_180 = sensors.get("sensor_180", {})
        battery = message.get("battery", {})
        self._rows.append(
            {
                "received_at": received_at.isoformat(),
                "sequence": message.get("sequence"),
                "mode": message.get("mode"),
                "sensor_90_value": values.get("sensor_90"),
                "sensor_180_value": values.get("sensor_180"),
                "sensor_90_display": display_values.get("sensor_90"),
                "sensor_180_display": display_values.get("sensor_180"),
                "units": message.get("units") or "",
                "sensor_90_gain": sensor_90.get("gain"),
                "sensor_90_integration_time": sensor_90.get("integration_time"),
                "sensor_180_gain": sensor_180.get("gain"),
                "sensor_180_integration_time": sensor_180.get("integration_time"),
                "battery_voltage": battery.get("voltage"),
            }
        )

    def write(self, destination: Path) -> None:
        """Escribe todo el registro de la sesión en CSV UTF-8."""
        with destination.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.FIELD_NAMES)
            writer.writeheader()
            writer.writerows(self._rows)

