from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from main_window import MainWindow


if __name__ == "__main__":
    application = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(application.exec())
