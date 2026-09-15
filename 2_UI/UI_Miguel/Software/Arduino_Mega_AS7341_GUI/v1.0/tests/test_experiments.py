import csv
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop_gui'))
from analysis import capture, ratio, linear_fit
from exporter import CsvExporter
from protocol import CHANNEL_KEYS
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow


def frame(seq=1, value=100):
    return dict(type='telemetry', sequence=seq, millis=seq*100, gain='128x',
                integration_time='100ms', pwm_percent=25, pwm_raw=64,
                page=0, channels={key: value for key in CHANNEL_KEYS})


def feed(panel, seq, value):
    panel.feed({**frame(seq, value), 'capture_id': panel.pending['capture_id']})


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_ratio_validation(self):
        a, b = capture([frame(value=200)], 'A'), capture([frame(value=100)], 'B')
        self.assertEqual(ratio(a,b,'415','415'), 2)
        for invalid in (capture([frame(value=0)], ''), capture([frame(value=65535)], '')):
            with self.assertRaises(ValueError):
                ratio(a, invalid, '415', '415')
        b['gain'] = '64x'
        with self.assertRaises(ValueError):
            ratio(a,b,'415','415')

    def test_fit_known_line_and_degenerate_data(self):
        points = [dict(x=x,y=2*x+3,method='test') for x in (0,1,2)]
        fit = linear_fit(points)
        self.assertEqual((fit['slope'],fit['intercept'],fit['r2']), (2,3,1))
        with self.assertRaises(ValueError):
            linear_fit([dict(x=1,y=y,method='test') for y in (1,2,3)])

    def test_csv_roundtrip(self):
        exporter = CsvExporter()
        exporter.append(datetime.now(timezone.utc), {**frame(), 'pwm_percent': 60, 'pwm_raw': 153})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'test.csv'
            exporter.write(path)
            with path.open() as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(rows[0]['clear'], '100')
            self.assertEqual((rows[0]['pwm_percent'], rows[0]['pwm_raw']), ('60', '153'))
            self.assertEqual(len(rows), 1)

    def test_ui_capture_ratio_calibration(self):
        window = MainWindow(session_dir=tempfile.mkdtemp(prefix='as7341-test-'))
        e = window.experiments
        e.optics.setText('test optics')
        e.set_connected(True)
        e.count.setValue(2)
        e.begin('leda')
        feed(e,1,200)
        self.assertNotIn('leda',e.captures)
        feed(e,2,200)
        e.begin('ledb')
        feed(e,3,100); feed(e,4,100)
        e.calculate('led')
        self.assertEqual(e.last_result['value'], 2)
        e.source.setCurrentIndex(1)
        e.add_point()
        e.add_point()
        self.assertEqual(len(e.points),1)
        e.undo_point()
        self.assertEqual(len(e.points),0)
        e.set_connected(False)
        e.begin('leda')
        self.assertIsNone(e.pending)
        window.close()

    def test_selector_sends_text(self):
        window = MainWindow(session_dir=tempfile.mkdtemp(prefix='as7341-test-'))
        messages = []
        window.client.send = messages.append
        window.gain_selector.textActivated.emit('64x')
        self.assertEqual(messages[0]['value'],'64x')
        window.pwm_control.setValue(60)
        self.assertEqual(messages[1], {'type': 'command', 'command': 'set_pwm', 'value': 60})
        window.close()

    def test_ui_calibration_fresh_samples_and_fit(self):
        window = MainWindow(session_dir=tempfile.mkdtemp(prefix='as7341-test-'))
        e = window.experiments
        e.optics.setText('test optics')
        e.set_connected(True)
        e.count.setValue(1)
        for seq, x in enumerate((0,1,2), 1):
            e.concentration.setValue(x)
            e.add_point()
            feed(e,seq,2*x+3)
        e.fit_curve()
        self.assertEqual(e.fit['slope'],2)
        e.begin('leda')
        e.set_connected(False)
        e.feed(frame(10))
        self.assertNotIn('leda',e.captures)
        window.close()

    def test_changed_settings_cancel_capture(self):
        with self.assertRaises(ValueError):
            capture([frame(), {**frame(2), 'gain':'64x'}], '')
        with self.assertRaises(ValueError):
            capture([frame(), {**frame(2), 'pwm_percent': 50, 'pwm_raw': 128}], '')

    def test_pwm_change_cancels_pending_ui_capture(self):
        window = MainWindow(session_dir=tempfile.mkdtemp(prefix='as7341-test-'))
        window.client.send = lambda message: None
        window.experiments.set_connected(True)
        window.experiments.optics.setText('test optics')
        window.experiments.begin('leda')
        self.assertIsNotNone(window.experiments.pending)
        window.send_setting('set_pwm', 50)
        self.assertIsNone(window.experiments.pending)
        window.close()

    def test_curve_rejects_different_pwm_method(self):
        points = [dict(x=0, y=1, method='counts:445:128x:100ms:pwm25'),
                  dict(x=1, y=2, method='counts:445:128x:100ms:pwm25'),
                  dict(x=2, y=3, method='counts:445:128x:100ms:pwm50')]
        with self.assertRaises(ValueError):
            linear_fit(points)
