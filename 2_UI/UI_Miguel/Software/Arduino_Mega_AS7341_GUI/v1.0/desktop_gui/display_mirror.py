"""Lectura IO Rodeo completa y espejo de la pantalla Nokia."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from protocol import CHANNEL_KEYS


CHANNEL_LABELS = {
    "415": ("F1", "415 nm"),
    "445": ("F2", "445 nm"),
    "480": ("F3", "480 nm"),
    "515": ("F4", "515 nm"),
    "555": ("F5", "555 nm"),
    "590": ("F6", "590 nm"),
    "630": ("F7", "630 nm"),
    "680": ("F8", "680 nm"),
    "nir": ("NIR", "Infrarrojo cercano"),
    "clear": ("Clear", "Banda ancha"),
}


class DisplayMirror(QWidget):
    command_requested = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.status = QLabel("Sin datos. Conecta el Mega con firmware 2.3.0.")
        self.status.setObjectName("mirrorStatus")
        self.status.setWordWrap(True)
        self.status.setAccessibleName("Estado de la lectura IO Rodeo y del espejo Nokia")
        root.addWidget(self.status)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(self._build_complete_readout(), 2)
        content.addWidget(self._build_nokia_mirror(), 1)
        root.addLayout(content, 1)
        root.addWidget(self._build_device_summary())
        self.set_ready(False)

    def _build_complete_readout(self):
        group = QGroupBox("IO Rodeo: multicanal a 90° (vista completa)")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        self.channel_table = QTableWidget(len(CHANNEL_KEYS), 3)
        self.channel_table.setHorizontalHeaderLabels(("Canal", "Banda", "Cuenta raw"))
        self.channel_table.setAlternatingRowColors(True)
        self.channel_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.channel_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.channel_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.channel_table.verticalHeader().setVisible(False)
        self.channel_table.verticalHeader().setDefaultSectionSize(18)
        self.channel_table.horizontalHeader().setFixedHeight(24)
        self.channel_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.channel_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.channel_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.channel_table.setMinimumHeight(208)
        self.channel_table.setAccessibleName("Diez canales raw del AS7341 visibles simultáneamente")
        self.channel_table.setToolTip("Puedes seleccionar una o varias celdas para revisar los valores.")
        for row, key in enumerate(CHANNEL_KEYS):
            channel, band = CHANNEL_LABELS[key]
            self.channel_table.setItem(row, 0, QTableWidgetItem(channel))
            self.channel_table.setItem(row, 1, QTableWidgetItem(band))
            value_item = QTableWidgetItem("—")
            value_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.channel_table.setItem(row, 2, value_item)
        layout.addWidget(self.channel_table, 1)
        return group

    def _build_nokia_mirror(self):
        group = QGroupBox("Nokia 5110: pantalla física")
        layout = QVBoxLayout(group)
        layout.setSpacing(5)

        self.nokia = QLabel("Esperando líneas\ndel firmware")
        self.nokia.setTextFormat(Qt.TextFormat.PlainText)
        self.nokia.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.nokia.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.nokia.setAccessibleName("Texto enviado por el firmware a la Nokia 5110")
        self.nokia.setStyleSheet(
            "background:#dce6bd; color:#17200e; padding:10px; "
            "font-family:Menlo; font-size:16px; border:1px solid #a8b58c; "
            "border-radius:8px;"
        )
        layout.addWidget(self.nokia, 1)

        self.nokia_page = QLabel("Página física: —")
        self.nokia_page.setObjectName("secondaryText")
        layout.addWidget(self.nokia_page)

        self.auto = QCheckBox("Alternar la pantalla Nokia automáticamente cada 3 s")
        self.auto.setChecked(True)
        self.auto.setToolTip("La tabla completa de la izquierda siempre conserva visibles los diez canales.")
        self.auto.clicked.connect(
            lambda value: self.command_requested.emit(
                {"type": "command", "command": "set_auto_page", "value": value}
            )
        )
        layout.addWidget(self.auto)
        return group

    def _build_device_summary(self):
        group = QGroupBox("Estado completo del modo IO Rodeo")
        group.setFixedHeight(110)
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(4)
        fields = (
            ("Muestra", "sequence_value", "—"),
            ("Tiempo Mega", "millis_value", "—"),
            ("Ganancia", "gain_value", "—"),
            ("Integración", "integration_value", "—"),
            ("AS7341 90°", "multichannel_value", "Esperando"),
            ("TSL 180°", "tsl_value", "N/D"),
            ("Relative Units", "relative_value", "N/D"),
            ("Batería", "battery_value", "N/D (USB)"),
        )
        for index, (title, attribute, initial) in enumerate(fields):
            row, column = divmod(index, 4)
            value = QLabel(f"{title}: {initial}")
            value.setObjectName("metricValue")
            value.setProperty("metricTitle", title)
            value.setAccessibleName(title)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            setattr(self, attribute, value)
            layout.addWidget(value, row, column)
            layout.setColumnStretch(column, 1)
        return group

    @staticmethod
    def _set_metric(label, value):
        label.setText(f"{label.property('metricTitle')}: {value}")

    def set_ready(self, ready):
        self.auto.setEnabled(ready)

    def feed(self, frame):
        lines = frame.get("display_lines")
        if lines is None:
            self.status.setText("Firmware sin espejo de display. Actualiza antes de validar.")
            return

        self.nokia.setText("\n".join(lines))
        self.nokia_page.setText(f"Página física: {frame['page'] + 1}/2")
        for row, key in enumerate(CHANNEL_KEYS):
            count = frame["channels"][key]
            value_item = self.channel_table.item(row, 2)
            value_item.setText("OVFL" if count >= 65535 else str(count))
            value_item.setForeground(Qt.GlobalColor.red if count >= 65535 else Qt.GlobalColor.black)

        self._set_metric(self.sequence_value, str(frame["sequence"]))
        self._set_metric(self.millis_value, f"{frame['millis']} ms")
        self._set_metric(self.gain_value, frame["gain"])
        self._set_metric(self.integration_value, frame["integration_time"])
        self._set_metric(self.multichannel_value, "Activo, 10 raw")
        self.status.setText(
            f"Todos los canales visibles, raw sin normalizar, muestra {frame['sequence']}, "
            f"ganancia {frame['gain']}, integración {frame['integration_time']}"
        )
