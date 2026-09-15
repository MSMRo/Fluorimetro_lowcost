"""Tema claro completo, independiente de la apariencia nativa del sistema."""
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QApplication


def configure_theme():
    app = QApplication.instance()
    app.setStyle('Fusion')
    palette = QPalette()
    colors = {
        'Window': '#f4f7fa', 'WindowText': '#172b40', 'Base': '#ffffff',
        'AlternateBase': '#f1f5f9', 'Text': '#172b40', 'Button': '#ffffff',
        'ButtonText': '#172b40', 'Highlight': '#1e40af',
        'HighlightedText': '#ffffff', 'ToolTipBase': '#172b40',
        'ToolTipText': '#ffffff', 'PlaceholderText': '#64748b',
        'Light': '#ffffff', 'Midlight': '#e2e8f0', 'Mid': '#94a3b8',
        'Dark': '#64748b', 'Shadow': '#334155', 'Link': '#1e40af',
    }
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
        for role, color in colors.items():
            palette.setColor(group, getattr(QPalette.ColorRole, role), QColor(color))
    for role in ('Text', 'ButtonText', 'WindowText'):
        palette.setColor(QPalette.ColorGroup.Disabled, getattr(QPalette.ColorRole, role), QColor('#64748b'))
    app.setPalette(palette)


STYLE = '''
QWidget { color: #172b40; font-size: 13px; }
QMainWindow, QScrollArea { background: #f4f7fa; }
QLabel { background: transparent; }
QLabel#brandTitle {
    color: #172b40;
    font-family: "Palatino", "Iowan Old Style", "Georgia", serif;
    font-size: 28px;
    font-weight: 600;
    letter-spacing: 0.4px;
}
QFrame#brandSeparator { color: #cbd5df; }
QLabel#subtitle { color: #526477; }
QLabel#badge { color: #174f58; background: #e1f0ef; border-radius: 6px; padding: 8px 12px; }
QLabel#mirrorStatus { color: #174f58; background: #e1f0ef; border-radius: 6px; padding: 9px 12px; font-weight: 600; }
QLabel#secondaryText, QLabel#metricCaption { color: #64748b; font-size: 11px; }
QLabel#metricValue { color: #172b40; font-size: 13px; font-weight: 600; }
QGroupBox { background: white; border: 1px solid #d5dfe8; border-radius: 8px;
    margin-top: 14px; padding: 16px 12px 12px; font-weight: 600; }
QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #334155; }
QTabWidget::pane { background: white; border: 1px solid #d5dfe8; border-radius: 8px; }
QTabBar::tab { background: #edf2f7; color: #475569; padding: 12px 18px;
    border: none; border-bottom: 3px solid transparent; margin-right: 3px; }
QTabBar::tab:selected { background: white; color: #1e40af; border-bottom: 3px solid #1e40af; }
QTabBar::tab:hover { background: #e2e8f0; }
QPushButton { background: white; color: #172b40; border: 1px solid #b5c4d2;
    border-radius: 6px; min-height: 28px; padding: 4px 12px; }
QPushButton:hover { background: #edf3fa; border-color: #758ba0; }
QPushButton:pressed { background: #dce6f2; }
QPushButton#primary { background: #1e40af; color: white; border-color: #1e40af; }
QPushButton#primary:hover { background: #1e3a8a; }
QPushButton#recordButton { background: #ffffff; color: #174f58; border: 1px solid #4d8790; font-weight: 600; }
QPushButton#recordButton:hover { background: #edf7f6; border-color: #174f58; }
QPushButton#recordButton[recording="true"] { background: #b42318; color: #ffffff; border-color: #b42318; }
QPushButton#recordButton[recording="true"]:hover { background: #8f1d14; border-color: #8f1d14; }
QPushButton:disabled, QPushButton#primary:disabled, QPushButton#recordButton:disabled { background: #f1f5f9; color: #64748b; border-color: #d5dfe8; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: white; color: #172b40;
    border: 1px solid #b5c4d2; border-radius: 5px; min-height: 28px; padding: 3px 8px; }
QComboBox { padding-right: 26px; }
QComboBox QAbstractItemView { background: white; color: #172b40; selection-background-color: #dbeafe; selection-color: #172b40; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #f1f5f9; color: #64748b; }
QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus { border: 2px solid #2563eb; }
QTableWidget { background: white; alternate-background-color: #f1f5f9; color: #172b40;
    gridline-color: #e2e8f0; border: 1px solid #d5dfe8; selection-background-color: #dbeafe; selection-color: #172b40; }
QHeaderView::section { background: #edf2f7; color: #334155; border: none; padding: 8px; font-weight: 600; }
QTableCornerButton::section { background: #edf2f7; border: none; }
QPlainTextEdit { background: #101e2d; color: #dce7f3; border: none; border-radius: 6px; padding: 8px; }
QLabel#result { background: #e1f0ef; color: #115e59; border-radius: 6px; padding: 12px; font-size: 16px; }
QStatusBar { background: #eaf0f5; color: #334155; border-top: 1px solid #d5dfe8; }
QStatusBar::item { border: none; }
QToolTip { background: #172b40; color: white; padding: 6px; border: none; }
'''
