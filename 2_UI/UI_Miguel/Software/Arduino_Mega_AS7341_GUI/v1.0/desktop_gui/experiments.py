"""Capturas manuales trazables, cocientes y calibración por estándares."""
import csv
import json
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QTabWidget, QHeaderView, QCheckBox)
from analysis import capture, linear_fit
from protocol import CHANNEL_KEYS
from calibration_plot import CalibrationPlot
from session_store import atomic_json
from fluorometry import intensity_result, ratio_result, point_method
from experiment_validation import validate_session


class Experiments(QWidget):
    capture_requested = pyqtSignal(dict)
    data_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pending = None
        self.captures = {}
        self.capture_history = []
        self.results = []
        self.intensity_results = []
        self.points = []
        self.fit = None
        self.connected = False
        self.last_result = None
        self.used_results = set()
        self.autosave_path = None
        self.save_error = None
        self.completed_modes = set()
        root = QVBoxLayout(self)
        top = QHBoxLayout()
        self.label = QLineEdit()
        self.label.setPlaceholderText('Notas de captura: recipiente, posición y observaciones')
        self.count = QSpinBox()
        self.count.setRange(1, 100)
        self.count.setValue(5)
        top.addWidget(self.label, 1)
        top.addWidget(QLabel('Lecturas por captura'))
        top.addWidget(self.count)
        root.addLayout(top)
        conditions = QHBoxLayout()
        self.optics = QLineEdit()
        self.optics.setPlaceholderText('Protocolo óptico: LED A/B, filtros, geometría, corriente')
        self.optics.setAccessibleName('Condiciones ópticas del experimento')
        self.settle = QSpinBox()
        self.settle.setRange(0, 10000)
        self.settle.setValue(1000)
        self.settle.setSuffix(' ms')
        conditions.addWidget(self.optics, 1)
        conditions.addWidget(QLabel('Espera tras el clic'))
        conditions.addWidget(self.settle)
        root.addLayout(conditions)
        identity = QHBoxLayout()
        self.sample_id = QLineEdit()
        self.sample_id.setPlaceholderText('Muestra: mismo ID para repetir el ensayo completo')
        self.exposure = QLineEdit()
        self.exposure.setPlaceholderText('Exposición actual: LED, filtro, posición de lectura')
        identity.addWidget(QLabel('Muestra'))
        identity.addWidget(self.sample_id, 1)
        identity.addWidget(QLabel('Exposición'))
        identity.addWidget(self.exposure, 1)
        root.addLayout(identity)
        self.status = QLabel('Conecta el Mega. Cada captura recoge muestras posteriores al clic.')
        self.status.setWordWrap(True)
        root.addWidget(self.status)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)
        self.capture_buttons = []
        self.selectors = {}
        self.slot_labels = {}
        self.background_choices = []
        self.correct_ratio = {}
        self.ratio_blanks = {}
        for mode, title, instructions, first, second in (
            ('led', 'LED sucesivos', 'Coloca LED A, espera estabilidad y captura A. Cambia manualmente a LED B y captura B. R = A / B.', 'LED A', 'LED B'),
            ('ref', 'Baseline y referencia', 'Captura la referencia y luego la señal del fluorómetro. Q = señal / referencia. El blanco y la referencia óptica tienen significados distintos.', 'Señal', 'Referencia'),
        ):
            page = QWidget()
            layout = QVBoxLayout(page)
            explanation = QLabel(instructions)
            explanation.setWordWrap(True)
            layout.addWidget(explanation)
            if mode == 'ref':
                self.reference_type = QComboBox()
                self.reference_type.addItems(['Selecciona qué representa la referencia', 'Blanco sin fluoróforo', 'Luz de excitación medida directamente', 'Emisión basal del fluoróforo'])
                self.reference_type.setCurrentIndex(2)
                layout.addWidget(self.reference_type)
            for suffix, label in (('a', first), ('b', second)):
                slot = mode + suffix
                row = QHBoxLayout()
                selector = QComboBox()
                selector.addItems(CHANNEL_KEYS)
                self.selectors[slot] = selector
                button = QPushButton('Capturar ' + label)
                button.clicked.connect(lambda checked=False, s=slot: self.begin(s))
                button.setEnabled(False)
                self.capture_buttons.append(button)
                row.addWidget(QLabel(label + ': canal'))
                row.addWidget(selector)
                row.addWidget(button)
                layout.addLayout(row)
                self.slot_labels[slot] = QLabel('Sin captura')
                layout.addWidget(self.slot_labels[slot])
            self.correct_ratio[mode] = QCheckBox('Restar un blanco compatible a cada exposición')
            layout.addWidget(self.correct_ratio[mode])
            blank_row = QHBoxLayout()
            for suffix in ('a', 'b'):
                choice = self.background_choice()
                self.ratio_blanks[mode + suffix] = choice
                blank_row.addWidget(QLabel('Blanco ' + suffix.upper()))
                blank_row.addWidget(choice, 1)
            layout.addLayout(blank_row)
            calculate = QPushButton('Calcular y guardar cociente')
            calculate.setObjectName('primary')
            calculate.clicked.connect(lambda checked=False, m=mode: self.calculate(m))
            layout.addWidget(calculate)
            layout.addStretch()
            self.tabs.addTab(page, title)
        calibration = QWidget()
        layout = QVBoxLayout(calibration)
        row = QHBoxLayout()
        self.concentration = QDoubleSpinBox()
        self.concentration.setDecimals(6)
        self.concentration.setRange(0, 1e9)
        self.unit = QLineEdit('µmol/L')
        self.unit.setMaximumWidth(100)
        self.source = QComboBox()
        self.source.addItems(['Intensidad de un canal', 'Último cociente guardado', 'Intensidad con blanco'])
        self.channel = QComboBox()
        self.channel.addItems(CHANNEL_KEYS)
        for widget in (QLabel('Concentración'), self.concentration, self.unit, self.source, self.channel):
            row.addWidget(widget)
        layout.addLayout(row)
        self.cal_blank = self.background_choice()
        blank_row = QHBoxLayout()
        blank_row.addWidget(QLabel('Blanco para intensidad corregida'))
        blank_row.addWidget(self.cal_blank, 1)
        layout.addLayout(blank_row)
        row = QHBoxLayout()
        add = QPushButton('Guardar punto')
        add.setObjectName('primary')
        add.clicked.connect(self.add_point)
        row.addWidget(add)
        undo = QPushButton('Deshacer último punto')
        undo.clicked.connect(self.undo_point)
        row.addWidget(undo)
        fit = QPushButton('Ajustar curva lineal')
        fit.clicked.connect(self.fit_curve)
        row.addWidget(fit)
        layout.addLayout(row)
        self.plot = CalibrationPlot()
        layout.addWidget(self.plot, 1)
        self.fit_label = QLabel('Guarda al menos tres concentraciones distintas. El intercepto se estima libremente.')
        self.fit_label.setWordWrap(True)
        layout.addWidget(self.fit_label)
        self.point_table = QTableWidget(0, 3)
        self.point_table.setHorizontalHeaderLabels(['Concentración', 'Señal', 'Método'])
        self.point_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.point_table.setMaximumHeight(150)
        self.point_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.point_table)
        self.tabs.addTab(calibration, 'Curva de calibración')
        background = QWidget()
        bg = QVBoxLayout(background)
        info = QLabel('Blanco: solvente o matriz sin fluoróforo, con el mismo recipiente y exposición. '
                      'Guarda el fondo por separado; la resta conserva valores negativos. '
                      'Las lecturas de una captura no son réplicas del ensayo completo.')
        info.setWordWrap(True)
        bg.addWidget(info)
        for slot, title in (('blank', 'blanco'), ('signal', 'señal de muestra')):
            row = QHBoxLayout()
            selector = QComboBox()
            selector.addItems(CHANNEL_KEYS)
            self.selectors[slot] = selector
            button = QPushButton('Capturar ' + title)
            button.clicked.connect(lambda checked=False, s=slot: self.begin(s))
            self.capture_buttons.append(button)
            row.addWidget(QLabel('Canal de ' + title))
            row.addWidget(selector)
            row.addWidget(button)
            bg.addLayout(row)
            self.slot_labels[slot] = QLabel('Sin captura')
            bg.addWidget(self.slot_labels[slot])
        self.signal_choice = QComboBox()
        self.signal_choice.addItem('Selecciona una señal guardada', None)
        self.signal_blank = self.background_choice()
        bg.addWidget(QLabel('Señal guardada y blanco compatible'))
        bg.addWidget(self.signal_choice)
        bg.addWidget(self.signal_blank)
        corrected = QPushButton('Guardar intensidad corregida')
        corrected.setObjectName('primary')
        corrected.clicked.connect(self.save_corrected_intensity)
        bg.addWidget(corrected)
        self.background_table = QTableWidget(0, 5)
        self.background_table.setHorizontalHeaderLabels(['ID', 'Exposición', 'Canal', 'Media raw', 'Lecturas'])
        self.background_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.background_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        bg.addWidget(self.background_table, 1)
        self.tabs.addTab(background, 'Blanco y fondo')
        self.result_label = QLabel('Sin resultados guardados')
        self.result_label.setObjectName('result')
        root.addWidget(self.result_label)
        self.history = QTableWidget(0, 4)
        self.history.setHorizontalHeaderLabels(['Ensayo', 'Fórmula', 'Cociente', 'Capturas'])
        self.history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.history.setMaximumHeight(130)
        root.addWidget(self.history)
        bottom = QHBoxLayout()
        save = QPushButton('Guardar experimento JSON')
        save.clicked.connect(self.save_session)
        load = QPushButton('Abrir experimento JSON')
        load.clicked.connect(self.load_session)
        export = QPushButton('Exportar puntos CSV')
        export.clicked.connect(self.export_points)
        bottom.addWidget(save)
        bottom.addWidget(load)
        bottom.addWidget(export)
        root.addLayout(bottom)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(lambda: self.cancel('Captura cancelada: no llegaron suficientes muestras.'))
        self.update_buttons()

    def background_choice(self):
        choice = QComboBox()
        choice.addItem('Selecciona un blanco guardado', None)
        self.background_choices.append(choice)
        return choice

    def selected_capture(self, choice):
        token = choice.currentData()
        return next((deepcopy(s) for s in self.capture_history if s['id'] == token), None)

    def refresh_background(self):
        blanks = [s for s in self.capture_history if s.get('role') == 'blank']
        for choice in self.background_choices:
            selected = choice.currentData()
            choice.clear()
            choice.addItem('Selecciona un blanco guardado', None)
            for sample in blanks:
                choice.addItem(f"{sample['exposure']} | {sample['gain']} | {sample['integration_time']} | "
                               f"PWM {sample['pwm_percent']} % | {sample['id'][:8]}", sample['id'])
            choice.setCurrentIndex(max(0, choice.findData(selected)))
        selected = self.signal_choice.currentData()
        self.signal_choice.clear()
        self.signal_choice.addItem('Selecciona una señal guardada', None)
        for sample in self.capture_history:
            if sample.get('role') == 'signal':
                self.signal_choice.addItem(f"{sample['sample_id']} | {sample['exposure']} | {sample['id'][:8]}", sample['id'])
        self.signal_choice.setCurrentIndex(max(0, self.signal_choice.findData(selected)))
        self.background_table.setRowCount(len(blanks))
        for row, sample in enumerate(blanks):
            for col, value in enumerate((sample['id'], sample['exposure'], sample['channel'],
                                         sample['channels'][sample['channel']], sample['n'])):
                self.background_table.setItem(row, col, QTableWidgetItem(str(value)))

    def save_corrected_intensity(self):
        try:
            sample = self.selected_capture(self.signal_choice)
            blank = self.selected_capture(self.signal_blank)
            if sample is None or blank is None:
                raise ValueError('Selecciona una señal y su blanco.')
            if any(r['sample']['id'] == sample['id'] for r in self.intensity_results):
                raise ValueError('La señal ya tiene un resultado guardado. Repite la captura para una nueva réplica.')
            result = intensity_result(sample, sample['channel'], blank)
            self.intensity_results.append(result)
            self.result_label.setText(f"Intensidad corregida: {result['value']:.6g} cuentas. Consulta Resultados y calidad.")
            self.autosave()
        except ValueError as error:
            self.status.setText(str(error))

    def set_connected(self, connected):
        self.connected = connected
        if not connected:
            self.cancel('Desconectado. Historial conservado; el próximo ensayo requiere dos capturas nuevas.')
            self.clear_trial('led')
            self.clear_trial('ref')
            self.last_result = None
        self.update_buttons()

    def update_buttons(self):
        for button in self.capture_buttons:
            button.setEnabled(self.connected and self.pending is None)

    def begin(self, slot, metadata=None):
        if not self.connected:
            self.status.setText('Conecta el Mega antes de capturar.')
            return
        if self.pending is not None:
            self.status.setText('Espera a que termine la captura actual.')
            return
        if not self.optics.text().strip():
            self.status.setText('Describe el protocolo óptico antes de capturar (LED, filtros y geometría).')
            return
        if slot in ('blank', 'signal') and not self.exposure.text().strip():
            self.status.setText('Identifica la exposición antes de capturar el blanco o la señal.')
            return
        if slot == 'signal' and not self.sample_id.text().strip():
            self.status.setText('Identifica la muestra para agrupar las réplicas.')
            return
        if slot in ('leda', 'ledb', 'refa', 'refb'):
            mode = slot[:-1]
            if slot in self.captures or mode in self.completed_modes:
                self.clear_trial(mode)
        token = uuid4().hex
        self.pending = dict(slot=slot, frames=[], count=self.count.value(),
                            label=self.label.text(), metadata=metadata, capture_id=token,
                            settle_ms=self.settle.value(),
                            optics=self.optics.text().strip(),
                            sample_id=self.sample_id.text().strip(), exposure=self.exposure.text().strip(),
                            channel=self.selectors[slot].currentText() if slot != 'cal' else metadata['channel'],
                            reference=self.reference_type.currentText())
        self.timeout.start(max(15000, self.count.value() * 4000))
        self.status.setText(f'Capturando {slot}: 0/{self.count.value()} muestras nuevas…')
        self.update_buttons()
        self.capture_requested.emit(dict(type='command', command='begin_capture',
                                         capture_id=token, settle_ms=self.settle.value()))

    def clear_trial(self, mode):
        for suffix in ('a', 'b'):
            slot = mode + suffix
            self.captures.pop(slot, None)
            self.slot_labels[slot].setText('Sin captura, nuevo ensayo')
        self.completed_modes.discard(mode)
        if self.last_result and self.last_result['mode'] == mode:
            self.last_result = None

    def cancel(self, message):
        self.timeout.stop()
        self.pending = None
        self.status.setText(message)
        self.update_buttons()

    def feed(self, frame):
        if self.pending is None:
            return
        p = self.pending
        if frame.get('capture_id') != p['capture_id']:
            return
        if p['frames'] and frame['sequence'] <= p['frames'][-1]['sequence']:
            self.cancel('Captura cancelada: secuencia duplicada o reinicio del equipo.')
            return
        p['frames'].append(deepcopy(frame))
        self.status.setText(f"Capturando: {len(p['frames'])}/{p['count']}")
        if len(p['frames']) < p['count']:
            return
        try:
            sample = capture(p['frames'], p['label'])
            sample.update(optics=p['optics'], channel=p['channel'], reference=p['reference'],
                          sample_id=p['sample_id'], exposure=p['exposure'], role=p['slot'])
            self.capture_history.append(deepcopy(sample))
            if p['slot'] == 'cal':
                meta = p['metadata']
                result = intensity_result(sample, meta['channel'], meta.get('blank'))
                self.store_point(meta['x'], result['value'], result['analysis_method'],
                                 result if meta.get('blank') else sample, meta['unit'])
            else:
                self.captures[p['slot']] = sample
                self.slot_labels[p['slot']].setText(
                    f"Guardada, {sample['n']} muestras, {sample['gain']}, "
                    f"{sample['integration_time']}, PWM {sample['pwm_percent']} %, {sample['label']}")
            self.cancel('Captura guardada. Ya puedes cambiar el LED o la muestra.')
            self.refresh_background()
            self.autosave()
        except ValueError as error:
            self.cancel(str(error))
            self.refresh_background()
            self.autosave()

    def calculate(self, mode):
        try:
            if self.pending or mode in self.completed_modes:
                raise ValueError('Completa un nuevo ensayo A/B antes de guardar otro cociente.')
            a, b = self.captures.get(mode+'a'), self.captures.get(mode+'b')
            if a is None or b is None:
                raise ValueError('Completa las dos capturas primero.')
            reference_type = self.reference_type.currentText() if mode == 'ref' else 'LED sucesivos'
            if mode == 'ref' and self.reference_type.currentIndex() == 0:
                raise ValueError('Selecciona qué representa tu baseline antes de calcular.')
            if mode == 'ref' and self.reference_type.currentIndex() == 1:
                raise ValueError('El blanco sirve para restar fondo; usa una referencia óptica positiva para este cociente.')
            ca, cb = self.selectors[mode+'a'].currentText(), self.selectors[mode+'b'].currentText()
            if a['optics'] != b['optics'] or a['optics'] != self.optics.text().strip():
                raise ValueError('Cambió el protocolo óptico. Repite ambas capturas.')
            if ca != a['channel'] or cb != b['channel']:
                raise ValueError('Cambió el canal seleccionado. Repite ambas capturas.')
            if mode == 'ref' and (a['reference'] != reference_type or b['reference'] != reference_type):
                raise ValueError('Cambió el tipo de referencia. Repite ambas capturas.')
            ba = bb = None
            if self.correct_ratio[mode].isChecked():
                ba = self.selected_capture(self.ratio_blanks[mode+'a'])
                bb = self.selected_capture(self.ratio_blanks[mode+'b'])
                if ba is None or bb is None:
                    raise ValueError('Selecciona los blancos A y B antes de corregir el cociente.')
            result = ratio_result(a, b, ca, cb, mode=mode, reference_type=reference_type,
                                  blank_a=ba, blank_b=bb)
            value = result['value']
            self.results.append(result)
            self.last_result = result
            self.completed_modes.add(mode)
            row = self.history.rowCount()
            self.history.insertRow(row)
            for col, text in enumerate((reference_type, result['formula'], f'{value:.6g}', a['label']+' y '+b['label'])):
                self.history.setItem(row, col, QTableWidgetItem(text))
            self.result_label.setText(f"{result['formula']} = {value:.6g}, adimensional, resultado {len(self.results)}")
            self.status.setText('Ensayo guardado con evidencia raw. Repite ambas capturas para evaluar réplicas.')
            self.autosave()
        except ValueError as error:
            self.status.setText(str(error))

    def add_point(self):
        if not self.unit.text().strip():
            self.status.setText('Indica la unidad de concentración.')
            return
        meta = dict(x=self.concentration.value(), unit=self.unit.text().strip(), channel=self.channel.currentText())
        if self.source.currentIndex() in (0, 2):
            if self.source.currentIndex() == 2:
                meta['blank'] = self.selected_capture(self.cal_blank)
                if meta['blank'] is None:
                    self.status.setText('Selecciona el blanco de la exposición del estándar.')
                    return
            self.begin('cal', meta)
            return
        try:
            if self.last_result is None:
                raise ValueError('Calcula un cociente primero.')
            if self.last_result['a']['optics'] != self.optics.text().strip():
                raise ValueError('El cociente corresponde a otro protocolo óptico.')
            key = (self.last_result['a']['id'], self.last_result['b']['id'])
            if key in self.used_results:
                raise ValueError('Ese par de capturas ya está en la curva. Captura el siguiente estándar.')
            self.store_point(meta['x'], self.last_result['value'], self.last_result['analysis_method'], deepcopy(self.last_result), meta['unit'])
            self.used_results.add(key)
            self.autosave()
        except ValueError as error:
            self.status.setText(str(error))

    def store_point(self, x, y, analysis_method, evidence, unit):
        method = point_method(analysis_method, unit)
        if self.points and self.points[0]['method'] != method:
            raise ValueError('La curva requiere el mismo método, canal, unidad, ganancia, integración y PWM.')
        self.points.append(dict(x=x, y=y, method=method, analysis_method=analysis_method,
                                unit=unit, evidence=deepcopy(evidence)))
        self.refresh_points()
        self.autosave()

    def undo_point(self):
        if self.points:
            point = self.points.pop()
            evidence = point['evidence']
            if 'a' in evidence:
                self.used_results.discard((evidence['a']['id'], evidence['b']['id']))
            self.refresh_points()
            self.autosave()

    def refresh_points(self):
        self.fit = None
        self.fit_label.setText('Puntos actualizados. Pulsa Ajustar curva lineal para recalcular.')
        self.plot.set_points(self.points)
        self.point_table.setRowCount(len(self.points))
        for row, point in enumerate(self.points):
            for col, key in enumerate(('x', 'y', 'method')):
                text = str(point[key]) if key != 'method' else f"{point.get('unit', '')} | método trazable"
                item = QTableWidgetItem(text)
                item.setToolTip(str(point[key]))
                self.point_table.setItem(row, col, item)

    def fit_curve(self):
        try:
            self.fit = linear_fit(self.points)
            f = self.fit
            self.fit_label.setText(f"y = {f['slope']:.6g} x + {f['intercept']:.6g}   |   R² {f['r2']:.5f}   |   RMSE {f['rmse']:.5g}   |   n = {f['n']}")
            self.plot.set_points(self.points, self.fit)
            self.autosave()
        except ValueError as error:
            self.status.setText(str(error))

    def save_session(self):
        destination, _ = QFileDialog.getSaveFileName(self, 'Guardar experimento', 'experimento_as7341.json', 'JSON (*.json)')
        if destination:
            try:
                atomic_json(destination, self.session_data())
                self.autosave_path = Path(destination)
                self.save_error = None
                self.status.setText('Experimento guardado con capturas crudas y resultados.')
            except (OSError, ValueError) as error:
                self.status.setText(f'No se pudo guardar: {error}')

    def session_data(self):
        return dict(version=3, captures=self.captures, results=self.results, intensity_results=self.intensity_results,
                    points=self.points, fit=self.fit, optics=self.optics.text(), capture_history=self.capture_history)

    def autosave(self):
        self.data_changed.emit(deepcopy(self.session_data()))
        if self.autosave_path is None:
            return
        try:
            atomic_json(self.autosave_path, self.session_data())
            self.save_error = None
        except (OSError, ValueError) as error:
            self.save_error = str(error)
            self.status.setText(f'ERROR de autoguardado: {error}. Exporta antes de cerrar.')

    def load_session(self):
        if self.pending:
            self.status.setText('Espera a que termine la captura antes de abrir una sesión.')
            return
        path, _ = QFileDialog.getOpenFileName(self, 'Abrir experimento', '', 'JSON (*.json)')
        if path:
            try:
                if self.autosave_path is not None:
                    self.autosave()
                    if self.save_error:
                        raise ValueError('Guarda la sesión actual antes de abrir otra.')
                previous_path = self.autosave_path
                self.restore_session(Path(path))
                if previous_path:
                    self.autosave_path = previous_path.parent / ('recovered_' + uuid4().hex[:8] + '.json')
                self.autosave()
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.status.setText(f'No se pudo abrir: {error}')

    def restore_session(self, path):
        if Path(path).stat().st_size > 50_000_000:
            raise ValueError('Archivo demasiado grande (máximo 50 MB).')
        data = validate_session(json.loads(Path(path).read_text(encoding='utf-8')))
        self.cancel('Sesión recuperada para revisión. Captura un nuevo ensayo para continuar.')
        self.results, self.points = data['results'], data['points']
        self.intensity_results = data['intensity_results']
        self.capture_history = data['capture_history']
        self.optics.setText(data['optics'])
        self.clear_trial('led')
        self.clear_trial('ref')
        for slot in ('blank', 'signal'):
            self.captures.pop(slot, None)
            self.slot_labels[slot].setText('Historial recuperado; sin captura activa')
        self.refresh_background()
        self.last_result = None
        self.used_results = set()
        self.refresh_points()
        self.history.setRowCount(len(self.results))
        for row, result in enumerate(self.results):
            for col, text in enumerate((result['reference_type'], result['formula'], str(result['value']), result['a']['label']+' y '+result['b']['label'])):
                self.history.setItem(row, col, QTableWidgetItem(text))
        self.result_label.setText(f'{len(self.results)} resultados recuperados, historial, no captura activa')
        self.data_changed.emit(deepcopy(self.session_data()))

    def export_points(self):
        destination, _ = QFileDialog.getSaveFileName(self, 'Exportar calibración', 'calibracion.csv', 'CSV (*.csv)')
        if destination:
            try:
                with open(destination, 'w', newline='', encoding='utf-8') as output:
                    writer = csv.DictWriter(output, fieldnames=('x', 'y', 'method'))
                    writer.writeheader()
                    writer.writerows({k: p[k] for k in ('x', 'y', 'method')} for p in self.points)
                self.status.setText('Puntos exportados.')
            except OSError as error:
                self.status.setText(str(error))
