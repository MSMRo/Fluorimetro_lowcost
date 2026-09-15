import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from time import monotonic
from PyQt6.QtWidgets import QApplication
from experiments import Experiments
from protocol import parse_telemetry, ProtocolError
from test_experiments import frame
from test_serial_client import FakeSerial
from main_window import MainWindow
from protocol import nokia_lines
import serial_client


class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def acquire(self, panel, slot, value):
        panel.begin(slot)
        panel.feed({**frame(value=value), 'capture_id': panel.pending['capture_id']})

    def test_new_trial_cannot_reuse_old_partner(self):
        panel = Experiments()
        panel.set_connected(True)
        panel.optics.setText('LED405/450; cubeta 90 grados')
        panel.count.setValue(1)
        self.acquire(panel, 'leda', 200)
        self.acquire(panel, 'ledb', 100)
        panel.calculate('led')
        self.assertEqual(panel.last_result['value'], 2)
        self.acquire(panel, 'leda', 600)
        panel.calculate('led')
        self.assertEqual(len(panel.results), 1)
        self.assertNotIn('ledb', panel.captures)

    def test_buffered_frame_ignored(self):
        panel = Experiments()
        panel.set_connected(True)
        panel.optics.setText('test')
        panel.count.setValue(1)
        panel.begin('leda')
        panel.feed(frame(value=999))
        self.assertNotIn('leda', panel.captures)
        panel.feed({**frame(value=123), 'capture_id': panel.pending['capture_id']})
        self.assertEqual(panel.captures['leda']['channels']['415'], 123)

    def test_display_payload_must_match_measurement(self):
        data = frame()
        data['display_lines'] = ['G128x T100 1/2'] + [f'{k:<5} {100:>5}' for k in ('415','445','480','515','555')]
        self.assertEqual(parse_telemetry(data)['display_lines'], data['display_lines'])
        data['display_lines'][1] = '415      999'
        with self.assertRaises(ProtocolError):
            parse_telemetry(data)

    def test_atomic_recovery(self):
        panel = Experiments()
        panel.set_connected(True)
        panel.optics.setText('geometry1')
        panel.count.setValue(1)
        with tempfile.TemporaryDirectory() as directory:
            panel.autosave_path = Path(directory) / 'session.json'
            self.acquire(panel, 'leda', 200)
            self.acquire(panel, 'ledb', 100)
            panel.calculate('led')
            restored = Experiments()
            restored.restore_session(panel.autosave_path)
            self.assertEqual(restored.results[0]['value'], 2)
            self.assertIsNone(restored.last_result)
            self.assertFalse(restored.captures)
            self.assertEqual(len(restored.capture_history), 2)

    def test_verified_connection_stale_data_and_reconnect(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(serial_client.serial, 'Serial', FakeSerial):
            window = MainWindow(session_dir=directory)
            window.client.connect_to('/dev/fake-mega')
            self.assertFalse(window.experiments.connected)
            window.handle_message(dict(type='state', device='other', protocol=2, sensor_ready=True))
            self.assertFalse(window.experiments.connected)
            window.handle_message(dict(type='state', device='upch-mega-as7341', protocol=2,
                                       capabilities=['pwm_control'], sensor_ready=True))
            self.assertFalse(window.experiments.connected)
            data = frame()
            data['display_lines'] = nokia_lines(data)
            window.handle_message(data)
            self.assertTrue(window.experiments.connected)
            self.assertIn('/dev/fake-mega', window.link_status.text())
            self.assertEqual(window.mirror.nokia.text(), '\n'.join(data['display_lines']))
            for row, key in enumerate(('415', '445', '480', '515', '555', '590', '630', '680', 'nir', 'clear')):
                self.assertEqual(window.mirror.channel_table.item(row, 2).text(), str(data['channels'][key]))
            self.assertEqual(window.mirror.channel_table.rowCount(), 10)
            self.assertEqual(window.mirror.channel_table.verticalScrollBar().maximum(), 0)
            self.assertIn('Todos los canales visibles', window.mirror.status.text())
            self.assertEqual(window.mirror.nokia_page.text(), 'Página física: 1/2')
            self.assertIn('Activo, 10 raw', window.mirror.multichannel_value.text())
            self.assertIn('N/D', window.mirror.tsl_value.text())
            window.experiments.optics.setText('test')
            window.experiments.settle.setValue(10000)
            window.experiments.begin('leda')
            window._last_telemetry_at = monotonic() - 6
            window.refresh_link_status()
            self.assertIsNotNone(window.experiments.pending)
            window.experiments.cancel('test complete')
            window._last_telemetry_at = monotonic() - 6
            window.refresh_link_status()
            self.assertFalse(window.experiments.connected)
            self.assertFalse(window.mirror.auto.isEnabled())
            window.client.disconnect()
            window.client.connect_to('/dev/fake-second')
            window.handle_message({**data, 'sequence':2})
            self.assertFalse(window.experiments.connected)
            window.close()

    def test_optical_conditions_cannot_be_mixed(self):
        panel = Experiments()
        panel.set_connected(True)
        panel.count.setValue(1)
        panel.optics.setText('geometry A')
        self.acquire(panel, 'leda', 200)
        panel.optics.setText('geometry B')
        self.acquire(panel, 'ledb', 100)
        panel.calculate('led')
        self.assertFalse(panel.results)

    def test_atomic_write_failure_preserves_previous_file(self):
        from session_store import atomic_json
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'data.json'
            atomic_json(path, {'value': 1})
            previous = path.read_bytes()
            with patch('session_store.os.replace', side_effect=OSError('disk failure')):
                with self.assertRaises(OSError):
                    atomic_json(path, {'value': 2})
            self.assertEqual(path.read_bytes(), previous)
