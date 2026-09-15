import csv
import tempfile
import unittest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from acquisition import Acquisition, TimePlot
from protocol import CHANNEL_KEYS, nokia_lines, parse_telemetry

APP = QApplication.instance() or QApplication([])


def frame(sequence, millis):
    return dict(type='telemetry', sequence=sequence, millis=millis, page=0,
                gain='128x', integration_time='100ms', channels=dict.fromkeys(CHANNEL_KEYS, 100))


class AcquisitionTests(unittest.TestCase):
    def test_sweep_fixed_scale_and_gap(self):
        plot = TimePlot()
        plot.feed(frame(1, 100), '415')
        plot.feed(frame(2, 10100), '415')
        self.assertEqual(len(plot.points), 1)
        self.assertFalse(plot.points[0][2])
        plot.feed(frame(4, 10200), '415')
        self.assertFalse(plot.points[-1][2])
        self.assertEqual(plot.maximum, 100)

    def test_record_pause_freeze_and_new_file(self):
        with tempfile.TemporaryDirectory() as directory:
            panel = Acquisition(directory)
            panel.set_ready(True, 'test-port')
            panel.begin()
            panel.feed(frame(1, 100))
            panel.freeze_plot(True)
            panel.feed(frame(2, 10100))
            self.assertEqual(panel.count, 2)
            panel.pause_recording()
            panel.feed(frame(3, 10200))
            self.assertEqual(panel.count, 2)
            panel.begin()
            panel.feed(frame(4, 10300))
            first = panel.path
            with first.open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]['port'], 'test-port')
            panel.end()
            panel.begin()
            self.assertNotEqual(first, panel.path)
            self.assertTrue(Path(first).exists())
            panel.set_ready(False, None)
            self.assertFalse(panel.running)

    def test_nokia_selected_channel_contract(self):
        for channel in CHANNEL_KEYS:
            data = frame(1, 100)
            data.update(display_mode='channel', display_channel=channel)
            data['display_lines'] = nokia_lines(data)
            self.assertEqual(len(data['display_lines']), 6)
            self.assertTrue(all(len(line) <= 14 for line in data['display_lines']))
            self.assertEqual(parse_telemetry(data)['display_channel'], channel)
