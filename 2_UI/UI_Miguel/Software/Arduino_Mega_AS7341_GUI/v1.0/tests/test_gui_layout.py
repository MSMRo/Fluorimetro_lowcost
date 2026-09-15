import tempfile
import unittest
import csv
from pathlib import Path
from time import monotonic
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication, QLabel
from main_window import MainWindow
from protocol import nokia_lines
from test_experiments import frame


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_dark_system_palette_does_not_hide_content(self):
        dark = QPalette()
        dark.setColor(QPalette.ColorRole.WindowText, QColor('white'))
        dark.setColor(QPalette.ColorRole.Text, QColor('white'))
        dark.setColor(QPalette.ColorRole.Base, QColor('black'))
        self.app.setPalette(dark)
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(session_dir=directory)
            window.resize(980, 680)
            window.show()
            self.app.processEvents()
            self.assertEqual(window.port_selector.palette().color(QPalette.ColorRole.Text).name(), '#172b40')
            self.assertGreaterEqual(window.plot.width(), 360)
            self.assertGreaterEqual(window.plot.height(), 280)
            self.assertGreaterEqual(window.table.height(), 340)
            self.assertFalse(window.plot.geometry().intersects(window.table.geometry()))
            self.assertGreaterEqual(window.acquisition_scroll.verticalScrollBar().maximum(), 0)
            window.tabs.setCurrentWidget(window.experiments_scroll)
            window.experiments.tabs.setCurrentIndex(2)
            self.app.processEvents()
            self.assertGreaterEqual(window.experiments.plot.height(), 190)
            window.close()

    def test_complete_iorodeo_view_has_no_hidden_values(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(session_dir=directory)
            data = frame()
            data['display_lines'] = nokia_lines(data)
            window.mirror.feed(data)
            window.tabs.setCurrentWidget(window.mirror)
            window.show()
            for width, height in ((980, 680), (1120, 820)):
                window.resize(width, height)
                self.app.processEvents()
                table = window.mirror.channel_table
                last_cell = table.visualItemRect(table.item(9, 2))
                self.assertTrue(table.viewport().rect().contains(last_cell))
                self.assertEqual(table.verticalScrollBar().maximum(), 0)
                for label in (
                    window.mirror.sequence_value,
                    window.mirror.millis_value,
                    window.mirror.gain_value,
                    window.mirror.integration_value,
                    window.mirror.multichannel_value,
                    window.mirror.tsl_value,
                    window.mirror.relative_value,
                    window.mirror.battery_value,
                ):
                    self.assertEqual(label.visibleRegion().boundingRect().height(), label.height())
            window.close()

    def test_live_view_is_first_and_recording_writes_raw_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            records = Path(directory) / 'records'
            window = MainWindow(session_dir=Path(directory) / 'session', records_dir=records)
            self.assertEqual(window.tabs.tabText(0), 'Adquisición en vivo')
            self.assertNotIn('Registro temporal', [window.tabs.tabText(i) for i in range(window.tabs.count())])
            self.assertEqual(window.scale_maximum.value(), 2000)
            self.assertEqual(window.pwm_control.value(), 25)
            logo = window.findChild(QLabel, 'institutionLogo')
            title = window.findChild(QLabel, 'brandTitle')
            self.assertIsNotNone(logo)
            self.assertFalse(logo.pixmap().isNull())
            self.assertEqual(title.text(), 'Spectral Lab')
            self.assertFalse(hasattr(window, 'previous_page'))
            self.assertFalse(hasattr(window, 'next_page'))

            window._verified = True
            window._last_telemetry_at = monotonic()
            window.toggle_recording()
            path = window._recording_path
            self.assertTrue(window.record_button.property('recording'))
            data = frame(seq=3, value=321)
            data['display_lines'] = nokia_lines(data)
            window.handle_message(data)
            window.toggle_recording()
            self.assertFalse(window.record_button.property('recording'))
            self.assertTrue(path.exists())
            with path.open(encoding='utf-8') as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['445'], '321')
            window.close()

    def test_sequence_reset_finishes_current_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            window = MainWindow(
                session_dir=Path(directory) / 'session',
                records_dir=Path(directory) / 'records',
            )
            window._verified = True
            window._last_telemetry_at = monotonic()
            window.toggle_recording()
            path = window._recording_path
            first = frame(seq=8, value=111)
            first['display_lines'] = nokia_lines(first)
            window.handle_message(first)
            repeated = frame(seq=1, value=999)
            repeated['display_lines'] = nokia_lines(repeated)
            window.handle_message(repeated)
            self.assertIsNone(window._recording_exporter)
            self.assertEqual(window.last_recording_path, path)
            with path.open(encoding='utf-8') as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['445'], '111')
            window.close()
