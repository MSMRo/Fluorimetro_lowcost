import sys
import json
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QComboBox, QPushButton,
                             QLabel, QSlider, QGroupBox)
from PyQt6.QtCore import Qt
import pyqtgraph as pg

class FluorimetroUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Fluorímetro Low Cost - Interfaz de Control")
        self.resize(850, 600)

        # Crear el contenedor principal de pestañas
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Inicializar las dos pestañas solicitadas
        self.init_config_tab()
        self.init_gui_tab()

    def init_config_tab(self):
        tab = QWidget()
        layout = QVBoxLayout()

        # Grupo de Configuración Serial
        group = QGroupBox("Configuración de Conexión Serial")
        group_layout = QVBoxLayout()

        # Selector de Puerto COM
        self.combo_port = QComboBox()
        self.combo_port.addItems(["COM1", "COM2", "COM3", "COM4"]) 
        
        # Selector de Bauds
        self.combo_baud = QComboBox()
        self.combo_baud.addItems(["9600", "57600", "115200"])
        self.combo_baud.setCurrentText("115200") 

        # Botón de Conexión
        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px; border-radius: 3px;")
        
        # Conectar el botón a la función que cambia el estado
        self.btn_connect.clicked.connect(self.toggle_connection)

        # Agregar widgets al layout del grupo
        group_layout.addWidget(QLabel("Puerto COM:"))
        group_layout.addWidget(self.combo_port)
        group_layout.addWidget(QLabel("Baud Rate:"))
        group_layout.addWidget(self.combo_baud)
        group_layout.addSpacing(15)
        group_layout.addWidget(self.btn_connect)

        group.setLayout(group_layout)
        
        # Añadir al layout principal de la pestaña
        layout.addWidget(group, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "Configuración")

    def init_gui_tab(self):
        tab = QWidget()
        layout = QHBoxLayout() # Layout horizontal: Gráfico a la izquierda, Controles a la derecha

        # --- PANEL IZQUIERDO: Gráfico (PyQtGraph) ---
        self.graph_widget = pg.PlotWidget(title="Espectro de Emisión (AS7341)")
        self.graph_widget.setLabel('left', 'Intensidad', units='Fotones')
        self.graph_widget.setLabel('bottom', 'Longitud de Onda', units='nm')
        self.graph_widget.setBackground('w') # Fondo blanco
        self.graph_widget.showGrid(x=True, y=True)

        # Longitudes de onda del AS7341 (F1-F8 + NIR)
        self.wavelengths = [415, 445, 480, 515, 555, 590, 630, 680, 910]
        # Línea de ploteo inicial en cero
        self.plot_line = self.graph_widget.plot(self.wavelengths, [0]*9, 
                                                pen=pg.mkPen(color='b', width=2), 
                                                symbol='o', symbolBrush='b')

        layout.addWidget(self.graph_widget, stretch=3) # El gráfico toma más espacio

        # --- PANEL DERECHO: Controles ---
        control_layout = QVBoxLayout()
        
        # NUEVO: Indicador de Estado de Conexión
        self.lbl_status = QLabel("DESCONECTADO")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 14px; padding: 8px; border-radius: 4px;")
        
        # Añadir indicador sobre el control de excitación
        control_layout.addWidget(self.lbl_status)
        control_layout.addSpacing(10) # Un pequeño espacio de separación

        # Grupo de Control de Excitación
        control_group = QGroupBox("Control de Excitación (LED)")
        group_layout = QVBoxLayout()

        self.lbl_slider = QLabel("Corriente del LED: 0%")
        self.lbl_slider.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_slider.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.slider_led = QSlider(Qt.Orientation.Horizontal)
        self.slider_led.setRange(0, 100)
        self.slider_led.valueChanged.connect(self.update_led_label)

        self.btn_toggle_led = QPushButton("Apagar LED")
        
        group_layout.addWidget(self.lbl_slider)
        group_layout.addWidget(self.slider_led)
        group_layout.addWidget(self.btn_toggle_led)
        group_layout.addStretch()

        control_group.setLayout(group_layout)
        control_layout.addWidget(control_group)
        control_layout.addStretch()

        layout.addLayout(control_layout, stretch=1)
        tab.setLayout(layout)
        self.tabs.addTab(tab, "GUI - Monitor")

    # --- FUNCIONES DE ACCIÓN ---
    
    def toggle_connection(self):
        """Alterna el estado visual de conexión (Solo para la demo UI)"""
        if self.lbl_status.text() == "DESCONECTADO":
            self.lbl_status.setText("CONECTADO")
            self.lbl_status.setStyleSheet("background-color: green; color: white; font-weight: bold; font-size: 14px; padding: 8px; border-radius: 4px;")
            self.btn_connect.setText("Desconectar")
            self.btn_connect.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 5px; border-radius: 3px;")
        else:
            self.lbl_status.setText("DESCONECTADO")
            self.lbl_status.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 14px; padding: 8px; border-radius: 4px;")
            self.btn_connect.setText("Conectar")
            self.btn_connect.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px; border-radius: 3px;")

    def update_led_label(self, value):
        self.lbl_slider.setText(f"Corriente del LED: {value}%")

    def update_plot(self, json_data_string):
        """
        Esta función se llamará cada vez que recibas datos del Arduino.
        """
        try:
            data = json.loads(json_data_string)
            y_values = [
                data.get("415nm", 0), data.get("445nm", 0), data.get("480nm", 0),
                data.get("515nm", 0), data.get("555nm", 0), data.get("590nm", 0),
                data.get("630nm", 0), data.get("680nm", 0), data.get("910nm", 0)
            ]
            self.plot_line.setData(self.wavelengths, y_values)
        except json.JSONDecodeError:
            print("Error al decodificar el JSON del Arduino.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion") 
    main_window = FluorimetroUI()
    main_window.show()
    sys.exit(app.exec())