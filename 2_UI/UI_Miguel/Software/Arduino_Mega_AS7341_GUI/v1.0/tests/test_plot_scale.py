import unittest
from PyQt6.QtWidgets import QApplication
from spectral_plot import SpectralPlot
from protocol import CHANNEL_KEYS


class PlotScaleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_axis_does_not_pump_between_measurements(self):
        plot = SpectralPlot()
        maximum = plot._maximum
        self.assertEqual(maximum, 2000)
        plot.set_animation_enabled(False)
        for value in (10, 1000, 2, 65535):
            plot.set_channels(dict.fromkeys(CHANNEL_KEYS, value))
            self.assertEqual(plot._maximum, maximum)
            self.assertEqual(plot.display_values, (float(value),) * 8)
        plot.set_maximum(2000)
        plot.set_channels(dict.fromkeys(CHANNEL_KEYS, 3000))
        self.assertEqual(plot._maximum, 2000)

    def test_invalid_limits_rejected(self):
        plot = SpectralPlot()
        for maximum in (0, -1, 65536, True, 1.5):
            with self.assertRaises(ValueError):
                plot.set_maximum(maximum)

    def test_pause_freezes_only_the_visible_curve(self):
        plot = SpectralPlot()
        plot.set_animation_enabled(False)
        plot.set_channels(dict.fromkeys(CHANNEL_KEYS, 100))
        plot.set_paused(True)
        plot.set_channels(dict.fromkeys(CHANNEL_KEYS, 900))
        self.assertEqual(plot.display_values, (100.0,) * 8)
        plot.set_paused(False)
        self.assertEqual(plot.display_values, (900.0,) * 8)
