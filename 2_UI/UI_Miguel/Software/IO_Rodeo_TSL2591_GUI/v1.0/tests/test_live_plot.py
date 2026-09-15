import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication

from upch_gui.live_plot import LivePlot


def test_live_plot_renders_empty_and_numeric_series():
    app = QApplication.instance() or QApplication([])
    plot = LivePlot()
    plot.resize(480, 240)
    plot.show()
    empty_image = plot.grab().toImage()
    plot.append(1.0, "OVFL")
    plot.append(2.0, 4.0)
    data_image = plot.grab().toImage()

    assert not empty_image.isNull()
    assert not data_image.isNull()
    plot.close()
    app.processEvents()

