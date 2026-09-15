"""Registro y exportación de las telemetrías AS7341."""

from __future__ import annotations

import csv
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from protocol import CHANNEL_KEYS


class CsvExporter:
    field_names = (
        "received_at", "sequence", "millis", "gain", "integration_time",
        "pwm_percent", "pwm_raw", "page", *CHANNEL_KEYS,
    )

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(tempfile.mkdtemp(prefix='as7341-')) / 'telemetry.csv'
        self._count = 0

    @property
    def count(self) -> int:
        return self._count

    def append(self, received_at: datetime, telemetry: dict[str, Any]) -> None:
        row = {
            "received_at": received_at.isoformat(),
            "sequence": telemetry["sequence"],
            "millis": telemetry["millis"],
            "gain": telemetry["gain"],
            "integration_time": telemetry["integration_time"],
            "pwm_percent": telemetry.get("pwm_percent", 25),
            "pwm_raw": telemetry.get("pwm_raw", 64),
            "page": telemetry["page"],
            **{key: telemetry['channels'][key] for key in CHANNEL_KEYS},
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open('a', encoding='utf-8', newline='') as output:
            writer = csv.DictWriter(output, fieldnames=self.field_names)
            if self._count == 0:
                writer.writeheader()
            writer.writerow(row)
        self._count += 1

    def write(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.resolve() == self.path.resolve() and self.path.exists():
            return
        if self.path.exists():
            shutil.copyfile(self.path, destination)
            return
        with destination.open("w", encoding="utf-8", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=self.field_names)
            writer.writeheader()
