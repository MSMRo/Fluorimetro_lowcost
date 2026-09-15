import tempfile
import unittest

from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from test_experiments import frame


class AutoScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def window(self, directory):
        w = MainWindow(session_dir=directory)
        w.plot.set_animation_enabled(False)
        self.addCleanup(w.close)
        return w

    def test_default_is_fixed_and_toggle_fits_current_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            self.assertFalse(w.auto_scale_button.isChecked())
            w._update_telemetry(frame(value=3000))
            self.assertEqual(w.plot._maximum,2000)
            w.auto_scale_button.click()
            self.assertEqual(w.plot._maximum,3300)
            self.assertEqual(w.scale_maximum.value(),3300)
            self.assertFalse(w.scale_maximum.isEnabled())
            self.assertIn('automático',w.scale_label.text())
            w._update_telemetry(frame(2,100))
            self.assertEqual(w.plot._maximum,110)
            w.auto_scale_button.click()
            w.scale_maximum.setValue(700)
            w._update_telemetry(frame(3,5000))
            self.assertEqual(w.plot._maximum,700)

    def test_clear_nir_and_saturation_do_not_distort_visible_range(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            data = frame(value=100)
            data['channels'].update(clear=65535,nir=65535,**{'445':65535})
            w._update_telemetry(data)
            w.auto_scale_button.click()
            self.assertEqual(w.plot._maximum,110)
            self.assertEqual(w.plot.display_values[1],65535)
            self.assertEqual(w.table.item(1,1).text(),'OVFL')
            w._update_telemetry(frame(2,0))
            self.assertEqual(w.plot._maximum,10)
            w._update_telemetry(frame(3,65000))
            self.assertEqual(w.plot._maximum,65535)
            w._update_telemetry(frame(4,65535))
            self.assertEqual(w.plot._maximum,65535)

    def test_pause_preserves_auto_range_and_resume_uses_latest_reading(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            w._update_telemetry(frame(value=100))
            w.auto_scale_button.click()
            w.toggle_plot_pause(True)
            w._update_telemetry(frame(2,4000))
            self.assertEqual(w.plot._maximum,110)
            self.assertEqual(w.table.item(0,1).text(),'4000')
            self.assertEqual(w.plot.display_values,(100.0,)*8)
            w.toggle_plot_pause(False)
            self.assertEqual(w.plot._maximum,4400)

    def test_auto_does_not_send_commands_or_modify_raw_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            commands = []
            w.client.send = commands.append
            w.auto_scale_button.click()
            self.assertEqual(w.plot._maximum,2000)
            w._update_telemetry(frame(value=950))
            self.assertEqual(w.plot._maximum,1100)
            self.assertEqual(commands,[])
            self.assertEqual(w.plot.display_values,(950.0,)*8)
            self.assertEqual(w.table.item(1,1).text(),'950')

    def test_shrinking_range_does_not_clip_ongoing_transition(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            w._update_telemetry(frame(value=4000))
            w.auto_scale_button.click()
            w.plot.set_animation_enabled(True)
            w._update_telemetry(frame(2,100))
            self.assertGreaterEqual(w.plot._maximum,max(w.plot.display_values))

    def test_saturation_transition_does_not_create_false_valid_values(self):
        with tempfile.TemporaryDirectory() as directory:
            w = self.window(directory)
            w._update_telemetry(frame(value=65535))
            w.auto_scale_button.click()
            w.plot.set_animation_enabled(True)
            w._update_telemetry(frame(2,100))
            self.assertEqual(w.plot._maximum,110)
            w.plot._advance_animation()
            self.assertEqual(w.plot.display_values,(100.0,)*8)
            w._update_telemetry(frame(3,65535))
            w.plot._advance_animation()
            self.assertEqual(w.plot.display_values,(65535.0,)*8)
            self.assertEqual(w.plot._maximum,110)
