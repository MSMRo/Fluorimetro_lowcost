"""Interpretación de evidencia guardada, sin modificar adquisición ni capturas."""
import csv
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

from PyQt6.QtCore import pyqtSignal, QSignalBlocker, Qt
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QTextBrowser, QTabWidget)

from analysis import linear_fit
from fluorometry import intensity_result, inverse_calibration, replicate_summary
from protocol import CHANNEL_KEYS


BIBLIOGRAPHY = """
<h3>Métodos y alcance</h3>
<p>Intensidad corregida: S = media(señal) - media(blanco). El signo se conserva.
El blanco debe corresponder a la misma exposición, ganancia, integración, PWM y protocolo.
La composición del blanco es una decisión experimental, no una selección automática [2].</p>
<p>Cociente corregido: R = (A - blanco A) / (B - blanco B).
Marston et al. describen esta operación en imagen de biosensores (ecuación 2),
y muestran sus limitaciones cuando el denominador contiene mucho ruido [3].
Aquí se adapta a cuentas por banda del AS7341; no se implementa su método NCF
ni se presume equivalencia con un ensayo celular.</p>
<p>Réplicas: media, SD muestral y RSD = 100 SD / |media| entre ensayos completos
con el mismo ID de muestra y método. N lecturas seriales describen dispersión
dentro de una captura, no N repeticiones independientes [1].
Compartir señal o referencia impide tratarlas como réplicas distintas;
compartir blancos puede introducir correlación. No se estima incertidumbre total.</p>
<p>Calibración: mínimos cuadrados ordinarios, y = m c + b, intercepto libre.
Concentración estimada: c = (y - b) / m [4]. Se exige método y unidad compatibles,
una medición nueva y un resultado dentro del intervalo de estándares.
R², RMSE y residuos describen el ajuste; no son una validación externa.</p>
<p>El umbral de referencia baja es un criterio operativo editable en cuentas,
no un LOD, LOQ o umbral de señal/ruido validado. No se calculan estos límites
ni intervalos de confianza con una sola captura. Los cocientes de excitaciones
sucesivas dependen de la óptica y la respuesta espectral [5, 6].</p>
<h3>Bibliografía verificada</h3>
<p>[1] Chen, X., et al. (2024). <i>A low-cost and portable fluorometer based on an
optical pick-up unit for chlorophyll-a detection.</i> Talanta, 269, 125447.
<a href="https://doi.org/10.1016/j.talanta.2023.125447">DOI</a>.
Documento local: low_cost_1.pdf, página PDF 5, secciones 2.5 y 3.1:
promediado de lecturas y tres pruebas separadas por concentración.</p>
<p>[2] Cantwell, H. (ed.) (2025). <i>Blanks in Method Validation</i>, 2.ª ed., Eurachem.
<a href="https://www.eurachem.org/images/stories/Guides/pdf/MV_Guide_Blanks_supplement_2nd_ed_EN.pdf">Guía, sección 3</a>.
Apoya la elección del blanco; no prescribe la resta de baseline de esta GUI.</p>
<p>[3] Marston, D. J., Slattery, S. D., Hahn, K. M., y Tsygankov, D. (2021).
<i>Correcting Artifacts in Ratiometric Biosensor Imaging; an Improved Approach for Dividing Noisy Signals.</i>
Frontiers in Cell and Developmental Biology, 9, 685825.
<a href="https://doi.org/10.3389/fcell.2021.685825">DOI</a>. Ecuación 2 y discusión de denominadores pequeños.</p>
<p>[4] NIST/SEMATECH. <i>e-Handbook of Statistical Methods</i>, sección 2.3.6.6,
<a href="https://itl.nist.gov/div898/handbook/mpc/section3/mpc366.htm">Using the calibration curve</a>.
Inversión de la calibración lineal con el mismo instrumento y proceso controlado.</p>
<p>[5] Zhou, M., et al. (2026). <i>Ratiometric fluorescence arrays: a review of
design strategies, signal decoding, mechanisms, and applications.</i>
Documento local: Ratiometric design.pdf.
Microchemical Journal, 228, 118982.
<a href="https://doi.org/10.1016/j.microc.2026.118982">DOI</a>.
Página PDF 2: referencia interna y cocientes de emisiones seleccionadas.
La lectura sucesiva con LEDs externos es una adaptación, no una reproducción del artículo.</p>
<p>[6] DeRose, P. C. (2008). <i>Standard Guide to Fluorescence: Instrument Calibration and Validation.</i>
NISTIR 7458. <a href="https://doi.org/10.6028/NIST.IR.7458">DOI</a>.
Los datos aquí no incluyen corrección radiométrica de respuesta espectral ni eficiencia cuántica.</p>
"""


def number(value):
    return 'N/D' if value is None else f'{value:.6g}'


def table(headers, height=220):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    widget.setAlternatingRowColors(True)
    widget.verticalHeader().hide()
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    widget.horizontalHeader().setStretchLastSection(True)
    widget.setMinimumHeight(height)
    return widget


def fill(widget, rows):
    widget.setRowCount(len(rows))
    for row, values in enumerate(rows):
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setToolTip(str(value))
            widget.setItem(row, col, item)


class ResultsQuality(QWidget):
    open_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = {}
        self.entries = []
        self.report = {'concentration': None}
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 20)
        root.setSpacing(12)
        title = QLabel('Resultados trazables y calidad experimental')
        title.setObjectName('result')
        root.addWidget(title)
        info = QLabel('Revisa capturas y ensayos de esta sesión o abre un experimento JSON. '
                      'La interpretación no cambia los datos raw ni la lectura en vivo.')
        info.setWordWrap(True)
        root.addWidget(info)
        row = QHBoxLayout()
        self.selection = QComboBox()
        self.selection.setMinimumContentsLength(20)
        self.selection.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.selection.setAccessibleName('Evidencia experimental seleccionada')
        self.selection.currentIndexChanged.connect(self.refresh)
        row.addWidget(self.selection, 1)
        load = QPushButton('Abrir experimento JSON')
        load.clicked.connect(lambda: self.open_requested.emit())
        export = QPushButton('Exportar resultados CSV')
        export.clicked.connect(self.export_csv)
        row.addWidget(load)
        row.addWidget(export)
        root.addLayout(row)
        criterion = QHBoxLayout()
        criterion.addWidget(QLabel('Avisar si referencia ≤'))
        self.reference_floor = QDoubleSpinBox()
        self.reference_floor.setRange(0, 65535)
        self.reference_floor.setDecimals(3)
        self.reference_floor.setValue(1)
        self.reference_floor.setSuffix(' cuentas')
        self.reference_floor.valueChanged.connect(self.refresh)
        criterion.addWidget(self.reference_floor)
        caption = QLabel('Criterio operativo editable; no equivale a LOD/LOQ.')
        caption.setWordWrap(True)
        criterion.addWidget(caption, 1)
        root.addLayout(criterion)
        self.summary = QLabel('Sin evidencia guardada. Captura un ensayo en Experimentos y calibración.')
        self.summary.setWordWrap(True)
        self.summary.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.summary)
        self.protocol_info = QLabel('')
        self.protocol_info.setWordWrap(True)
        self.protocol_info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self.protocol_info)
        self.quality = QLabel('')
        self.quality.setWordWrap(True)
        root.addWidget(self.quality)
        detail_tabs = QTabWidget()
        root.addWidget(detail_tabs, 1)
        evidence = QWidget()
        layout = QVBoxLayout(evidence)
        layout.addWidget(QLabel('Componentes del resultado (media y SD de lecturas, no incertidumbre)'))
        self.components = table(['Componente', 'Canal', 'Valor (cuentas)', 'SD lecturas',
                                 'N lecturas', 'Ganancia', 'Integración', 'PWM %', 'Exposición', 'ID'])
        layout.addWidget(self.components)
        self.replicas = QLabel('Sin réplicas completas disponibles.')
        self.replicas.setWordWrap(True)
        layout.addWidget(self.replicas)
        self.replica_table = table(['Ensayo', 'Muestra', 'Resultado', 'Señal(es) ID', 'Blanco(s) ID'], 150)
        layout.addWidget(self.replica_table)
        detail_tabs.addTab(evidence, 'Señales y réplicas')
        calibration = QWidget()
        layout = QVBoxLayout(calibration)
        self.concentration = QLabel('Sin curva compatible.')
        self.concentration.setWordWrap(True)
        layout.addWidget(self.concentration)
        self.fit_info = QLabel('')
        self.fit_info.setWordWrap(True)
        layout.addWidget(self.fit_info)
        self.residuals = table(['Concentración estándar', 'Señal medida', 'Señal ajustada', 'Residuo', 'Unidad'])
        layout.addWidget(self.residuals)
        layout.addStretch()
        detail_tabs.addTab(calibration, 'Calibración e interpretación')
        bibliography = QTextBrowser()
        bibliography.setOpenExternalLinks(True)
        bibliography.setHtml(BIBLIOGRAPHY)
        detail_tabs.addTab(bibliography, 'Métodos y bibliografía')
        self.export_status = QLabel('Los CSV derivados se guardan inicialmente en records/. El JSON conserva toda la evidencia.')
        self.export_status.setWordWrap(True)
        root.addWidget(self.export_status)

    def set_session(self, data):
        self.data = deepcopy(data)
        selected = self.selection.currentData()
        self.entries = []
        for capture in self.data.get('capture_history', []):
            self.entries.append(dict(token='capture:'+capture['id'], capture=capture,
                                     title=f"{capture.get('role', 'raw')} | {capture.get('sample_id') or capture['label']} | {capture['id'][:8]}"))
        for record in self.data.get('results', []) + self.data.get('intensity_results', []):
            token = record.get('id') or record['a']['id']+record['b']['id']
            self.entries.append(dict(token='result:'+token, record=record,
                                     title=f"{'Corregido' if record.get('corrected') else 'Resultado'} | "
                                           f"{record.get('sample_id') or record.get('formula','')} | {token[:8]}"))
        with QSignalBlocker(self.selection):
            self.selection.clear()
            for entry in self.entries:
                self.selection.addItem(entry['title'], entry['token'])
            index = self.selection.findData(selected)
            self.selection.setCurrentIndex(index if index >= 0 else len(self.entries)-1)
        self.refresh()

    def evaluate(self, entry):
        record = entry.get('record')
        capture = entry.get('capture')
        flags = []
        if capture is not None:
            try:
                record = intensity_result(capture)
            except ValueError as error:
                return dict(record=None, capture=capture, concentration=None, unit='',
                            reason=str(error), flags=[str(error)], replicas=None)
            if capture.get('role') == 'legacy':
                record['legacy'] = True
                record.pop('analysis_method',None)
        if record.get('sample',{}).get('role') == 'blank':
            flags.append('Captura de blanco: describe el fondo, no una concentración de muestra.')
        if record.get('legacy'):
            flags.append('Histórico: firma de método incompleta; no se infiere compatibilidad de calibración.')
        if record.get('corrected') and record['value'] <= 0:
            flags.append('Señal corregida no positiva. Se conserva el signo; revisa blanco y exposición.')
        if 'a' in record and record.get('denominator', record['b']['channels'][record['b']['channel']]) <= self.reference_floor.value():
            flags.append('Referencia baja: el cociente es sensible al fondo y al ruido; concentración no informada.')
        if capture is not None and capture.get('saturated'):
            flags.append('Saturación digital en canales: ' + ', '.join(capture['saturated']) + '. Repite con menor exposición.')
        outcome = inverse_calibration(record, self.data.get('points', []))
        if flags:
            outcome['concentration'] = None
            outcome['reason'] = 'No se informa concentración: ' + ' '.join(flags)
        saved = self.data.get('results', []) + self.data.get('intensity_results', [])
        replicas = replicate_summary(saved, record) if capture is None and record.get('sample',{}).get('role') != 'blank' else None
        return dict(record=record, capture=capture, flags=flags, replicas=replicas, **outcome)

    def refresh(self, *_):
        index = self.selection.currentIndex()
        if not 0 <= index < len(self.entries):
            self.summary.setText('Sin evidencia guardada. Captura un ensayo en Experimentos y calibración.')
            self.quality.clear()
            self.protocol_info.clear()
            self.concentration.setText('Sin curva compatible.')
            self.fit_info.clear()
            self.replicas.setText('Sin réplicas completas disponibles.')
            for widget in (self.components, self.replica_table, self.residuals):
                widget.setRowCount(0)
            self.report = {'concentration': None}
            return
        self.report = self.evaluate(self.entries[index])
        report = self.report
        record = report['record']
        if record is None:
            self.summary.setText('Captura raw conservada; resultado cuantitativo no evaluable.')
        else:
            self.summary.setText(f"Muestra: {record.get('sample_id') or 'sin ID'} | {record['formula']} = {number(record['value'])} "
                                 f"{'(adimensional)' if 'a' in record else '(cuentas)'} | "
                                 f"{'con blanco' if record.get('corrected') else 'sin resta de fondo'} | "
                                 f"raw: {number(record.get('raw_value',record['value']))}")
        self.quality.setText('\n'.join(report['flags']) or
                             'Sin bloqueo numérico detectado. La matriz, estabilidad, deriva y respuesta espectral requieren validación experimental.')
        self.quality.setStyleSheet('color: #92400e;' if report['flags'] else 'color: #155e75;')
        samples = []
        if report.get('capture'):
            samples = [('Captura', report['capture'])]
        elif record and 'a' in record:
            samples = [('Señal A',record['a']), ('Referencia B',record['b'])]
            samples += [(label,record[key]) for label,key in (('Blanco A','blank_a'),('Blanco B','blank_b')) if record.get(key)]
        elif record:
            samples = [('Señal',record['sample'])]
            if record.get('blank'):
                samples.append(('Blanco',record['blank']))
        rows = []
        self.protocol_info.setText('Protocolo declarado: ' + (' | '.join(dict.fromkeys(s['optics'] for _,s in samples))) +
                                   '\nFinalización de captura: ' + ' | '.join(s.get('received_at','N/D') for _,s in samples))
        for label, sample in samples:
            channels = CHANNEL_KEYS if report.get('capture') else (sample['channel'],)
            for channel in channels:
                rows.append((label,channel,number(sample['channels'][channel]),
                             number(sample['sd'][channel]) if sample['n'] > 1 else 'N/D',
                             sample['n'],sample['gain'],sample['integration_time'],
                             sample['pwm_percent'],sample.get('exposure',''),sample['id']))
        if record and record.get('corrected'):
            derivatives = [('A - blanco A',record['a']['channel'],record['numerator']),
                           ('B - blanco B',record['b']['channel'],record['denominator'])] if 'a' in record else [('Señal - blanco',record['channel'],record['value'])]
            rows += [(label,ch,number(value),'No evaluada','N/D','','','','','') for label,ch,value in derivatives]
        fill(self.components, rows)
        stats = report['replicas']
        if stats:
            self.replicas.setText(f"Ensayos completos: {stats['n']} | Media {number(stats['mean'])} | "
                                  f"SD {number(stats['sd'])} | RSD {number(stats['rsd'])} %\n{stats['reason']}")
        else:
            self.replicas.setText('Esta vista raw describe lecturas dentro de una captura. Guarda resultados de ensayos completos para evaluar réplicas.')
        trials = [r for r in self.data.get('results',[])+self.data.get('intensity_results',[]) if record and record.get('sample_id')
                  and r.get('sample_id') == record['sample_id'] and r.get('analysis_method') == record.get('analysis_method')]
        fill(self.replica_table, [(i+1,r.get('sample_id',''),number(r['value']),
                                  ', '.join(r.get('measurement_ids',[])),
                                  ', '.join(s['id'] for s in (r.get('blank'),r.get('blank_a'),r.get('blank_b')) if s)) for i,r in enumerate(trials)])
        self.concentration.setText(f"Concentración estimada: {number(report['concentration'])} {report.get('unit','')}\n{report['reason']}")
        points = self.data.get('points', [])
        try:
            fit = linear_fit(points)
            self.fit_info.setText(f"y = {fit['slope']:.6g} c + {fit['intercept']:.6g} | R² {fit['r2']:.5f} | "
                                  f"RMSE {fit['rmse']:.6g} | {fit['n']} puntos, {len({p['x'] for p in points})} niveles.\n"
                                  'Ajuste descriptivo de la curva guardada. Comprueba residuos y controles independientes.')
            fill(self.residuals, [(number(p['x']),number(p['y']),number(fit['slope']*p['x']+fit['intercept']),
                                   number(residual),p.get('unit','Histórico')) for p,residual in zip(points,fit['residuals'])])
        except ValueError as error:
            self.fit_info.setText(str(error))
            self.residuals.setRowCount(0)

    def write_csv(self, destination):
        fields = ('sample_id','evidence_id','evidence_type','kind','formula','value','raw_value','corrected','measurement_ids',
                  'blank_ids','configurations','analysis_method','n_trials','trial_mean','trial_sd','trial_rsd_percent',
                  'reference_floor_counts','concentration','unit','calibration_range','flags','interpretation')
        with Path(destination).open('w', newline='', encoding='utf-8-sig') as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            for entry in self.entries:
                report = self.evaluate(entry)
                r = report['record']
                if r is None:
                    sample = report['capture']
                    r = dict(sample=sample,sample_id=sample.get('sample_id',''),id=sample['id'],kind='intensity',
                             formula=f"{sample['channel']}(captura raw)",value=None,
                             raw_value=sample['channels'][sample['channel']])
                stats = report['replicas'] or {}
                samples = [r['a'],r['b']] if 'a' in r else [r['sample']]
                writer.writerow(dict(sample_id=r.get('sample_id',''),evidence_id=(entry['capture']['id'] if 'capture' in entry else r.get('id',entry['token'])),
                    evidence_type='capture' if 'capture' in entry else 'result',
                    kind=r.get('kind','ratio'),formula=r['formula'],value=r['value'],raw_value=r.get('raw_value',r['value']),
                    corrected=r.get('corrected',False),measurement_ids=json.dumps(r.get('measurement_ids',[s['id'] for s in samples])),
                    blank_ids=json.dumps([s['id'] for s in (r.get('blank'),r.get('blank_a'),r.get('blank_b')) if s]),
                    configurations=json.dumps([dict(gain=s['gain'],integration=s['integration_time'],pwm=s['pwm_percent'],
                                                   optics=s['optics'],exposure=s.get('exposure','')) for s in samples],ensure_ascii=False),
                    analysis_method=r.get('analysis_method',''),n_trials=stats.get('n',0),trial_mean=stats.get('mean'),
                    trial_sd=stats.get('sd'),trial_rsd_percent=stats.get('rsd'),reference_floor_counts=self.reference_floor.value(),
                    concentration=report['concentration'],unit=report.get('unit',''),calibration_range=json.dumps(report.get('range')),
                    flags='; '.join(report['flags']),interpretation=report['reason'] + ' ' + stats.get('reason','')))

    def export_csv(self):
        if not self.entries:
            self.export_status.setText('Guarda una captura o un resultado de ensayo antes de exportar derivados.')
            return
        directory = Path(__file__).resolve().parents[1] / 'records'
        path, _ = QFileDialog.getSaveFileName(self, 'Exportar resultados trazables',
            str(directory / ('resultados_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.csv')), 'CSV (*.csv)')
        if path:
            try:
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                self.write_csv(path)
                self.export_status.setText('Resultados exportados: ' + path)
            except (OSError, ValueError) as error:
                self.export_status.setText('No se pudo exportar: ' + str(error))
