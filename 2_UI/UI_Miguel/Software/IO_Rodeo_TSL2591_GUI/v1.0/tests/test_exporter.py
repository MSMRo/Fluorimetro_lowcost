from datetime import datetime, timezone

from upch_gui.exporter import CsvExporter


def test_exporter_writes_received_telemetry_as_csv(tmp_path):
    exporter = CsvExporter()
    exporter.append(
        received_at=datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc),
        message={
            "type": "telemetry",
            "sequence": 7,
            "mode": "Raw Count",
            "values": {"sensor_90": 1234, "sensor_180": 5678},
            "display_values": {"sensor_90": "1234", "sensor_180": "5678"},
            "units": None,
            "sensors": {
                "sensor_90": {"gain": "med", "integration_time": "300ms"},
                "sensor_180": {"gain": "high", "integration_time": "400ms"},
            },
        },
    )

    destination = tmp_path / "measurements.csv"
    exporter.write(destination)

    rows = destination.read_text(encoding="utf-8").splitlines()
    assert rows[0].startswith("received_at,sequence,mode")
    assert "1234" in rows[1]
    assert "400ms" in rows[1]

