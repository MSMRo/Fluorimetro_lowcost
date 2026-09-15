import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from upch_gui.main_window import MainWindow


def test_window_displays_the_firmware_display_values():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.handle_message(
        {
            "type": "telemetry",
            "sequence": 4,
            "mode": "Irradiance",
            "labels": {"sensor_90": "Irradiance @90", "sensor_180": "Irradiance @180"},
            "values": {"sensor_90": 1.2345, "sensor_180": 12.345},
            "display_values": {"sensor_90": "1.234", "sensor_180": "12.35"},
            "units": "µW/cm²",
            "sensors": {
                "sensor_90": {"gain": "med", "integration_time": "300ms"},
                "sensor_180": {"gain": "high", "integration_time": "400ms"},
            },
            "battery": {"voltage": 3.97},
        }
    )

    assert window.sensor_90_value.text() == "1.234 µW/cm²"
    assert window.sensor_180_value.text() == "12.35 µW/cm²"
    assert window.mode_selector.currentText() == "Irradiance"
    assert window.exporter.count == 1
    window.close()
    app.processEvents()

