"""Punto de entrada de la aplicación."""

import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> int:
    application = QApplication(sys.argv)
    application.setApplicationName("UPCH GUI")
    window = MainWindow()
    window.show()
    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

