import csv
from copy import deepcopy
import tempfile
import unittest
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from experiments import Experiments
from results_quality import ResultsQuality
from session_store import atomic_json
from test_experiments import feed
from test_fluorometry import sample
from fluorometry import intensity_result, point_method


class ResultsQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def panel(self):
        panel = Experiments()
        panel.set_connected(True)
        panel.optics.setText('Cubeta 90 grados, filtro 445')
        panel.exposure.setText('LED azul 445')
        panel.sample_id.setText('M1')
        panel.count.setValue(1)
        return panel

    def take(self, panel, slot, value, seq):
        panel.begin(slot)
        self.assertIsNotNone(panel.pending)
        feed(panel, seq, value)

    def test_background_ui_and_recovery(self):
        panel = self.panel()
        self.take(panel, 'blank', 10, 1)
        self.take(panel, 'signal', 30, 2)
        panel.signal_choice.setCurrentIndex(1)
        panel.signal_blank.setCurrentIndex(1)
        panel.save_corrected_intensity()
        self.assertEqual(panel.intensity_results[0]['value'], 20)
        self.assertEqual(panel.intensity_results[0]['sample']['n'], 1)
        panel.save_corrected_intensity()
        self.assertEqual(len(panel.intensity_results), 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'experiment.json'
            atomic_json(path, panel.session_data())
            restored = Experiments()
            restored.restore_session(path)
            self.assertEqual(restored.intensity_results[0]['value'], 20)
            self.assertFalse(restored.captures)
            view = ResultsQuality()
            view.set_session(restored.session_data())
            view.selection.setCurrentIndex(view.selection.count()-1)
            self.assertIn('20', view.summary.text())
            self.assertEqual(view.components.item(0, 3).text(), 'N/D')
            self.assertIn('ensayo completo', view.replicas.text())

    def test_ratio_ui_uses_distinct_exposure_blanks(self):
        panel = self.panel()
        self.take(panel, 'blank', 10, 1)
        panel.exposure.setText('LED B')
        self.take(panel, 'blank', 20, 2)
        panel.exposure.setText('LED azul 445')
        self.take(panel, 'leda', 110, 3)
        panel.exposure.setText('LED B')
        self.take(panel, 'ledb', 70, 4)
        panel.correct_ratio['led'].setChecked(True)
        panel.ratio_blanks['leda'].setCurrentIndex(1)
        panel.ratio_blanks['ledb'].setCurrentIndex(2)
        panel.calculate('led')
        self.assertEqual(panel.last_result['value'], 2)
        self.assertEqual(panel.last_result['raw_value'], 110/70)

    def test_corrected_calibration_and_unit_signature(self):
        panel = self.panel()
        self.take(panel, 'blank', 10, 1)
        panel.source.setCurrentIndex(2)
        panel.cal_blank.setCurrentIndex(1)
        for x in (0, 1, 2):
            panel.concentration.setValue(x)
            panel.add_point()
            feed(panel, x+2, 2*x+13)
        panel.fit_curve()
        self.assertEqual(panel.fit['intercept'], 3)
        self.assertEqual(panel.fit['slope'], 2)
        self.assertEqual(panel.points[0]['unit'], 'µmol/L')

    def dataset(self):
        points = []
        for x in (0, 1, 2):
            r = intensity_result(sample(2*x+2, sample_id='standard'+str(x)))
            points.append(dict(x=x, y=r['value'], analysis_method=r['analysis_method'],
                               method=point_method(r['analysis_method'], 'µmol/L'),
                               unit='µmol/L', evidence=r))
        unknown = intensity_result(sample(3, sample_id='unknown'))
        return dict(version=3, optics='test', captures={}, capture_history=[],
                    results=[], intensity_results=[unknown], points=points, fit=None)

    def test_quality_prediction_export_and_blank_not_sample(self):
        view = ResultsQuality()
        data = self.dataset()
        view.set_session(data)
        self.assertAlmostEqual(view.report['concentration'], .5)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'results.csv'
            view.write_csv(path)
            with path.open(encoding='utf-8-sig') as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['sample_id'], 'unknown')
            self.assertEqual(rows[0]['unit'], 'µmol/L')
            self.assertEqual(float(rows[0]['concentration']), .5)
        before = deepcopy(data)
        view.selection.setCurrentIndex(0)
        self.assertEqual(before, data)
        data['capture_history'].append(sample(3, role='blank'))
        view.set_session(data)
        view.selection.setCurrentIndex(0)
        self.assertIsNone(view.report['concentration'])
        self.assertIn('blanco', view.quality.text().lower())

    def test_low_reference_blocks_concentration(self):
        from fluorometry import ratio_result
        a = sample(10, exposure='A')
        b = sample(1, exposure='B')
        record = ratio_result(a, b, '445', '445', 'led', 'LED sucesivos')
        view = ResultsQuality()
        view.reference_floor.setValue(3)
        view.set_session(dict(results=[record], intensity_results=[], capture_history=[], points=[]))
        self.assertIn('Referencia baja', view.quality.text())
        self.assertIsNone(view.report['concentration'])

    def test_saved_blank_is_not_an_unknown_concentration(self):
        view = ResultsQuality()
        data = self.dataset()
        data['intensity_results'] = [intensity_result(sample(3,role='blank'))]
        view.set_session(data)
        self.assertIsNone(view.report['concentration'])
        self.assertIn('blanco',view.quality.text())
        self.assertIsNone(view.report['replicas'])

    def test_raw_unknown_and_saturated_capture_export_without_fake_estimate(self):
        view = ResultsQuality()
        data = self.dataset()
        raw = data['intensity_results'][0]['sample']
        data['intensity_results'] = []
        data['capture_history'] = [raw]
        view.set_session(data)
        self.assertAlmostEqual(view.report['concentration'],.5)
        saturated = sample(65533)
        data['capture_history'].append(saturated)
        view.set_session(data)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'raw-results.csv'
            view.write_csv(path)
            with path.open(encoding='utf-8-sig') as source:
                rows = list(csv.DictReader(source))
            self.assertEqual(rows[0]['evidence_id'],raw['id'])
            self.assertEqual(rows[0]['evidence_type'],'capture')
            self.assertEqual(float(rows[0]['concentration']),.5)
            self.assertEqual(rows[1]['concentration'],'')
            self.assertEqual(rows[1]['value'],'')
            self.assertEqual(float(rows[1]['raw_value']),65534)

    def test_new_sections_are_reachable_at_small_window_size(self):
        from main_window import MainWindow
        with tempfile.TemporaryDirectory() as directory:
            w = MainWindow(session_dir=directory)
            w.resize(980,680)
            w.show()
            self.app.processEvents()
            self.assertEqual(w.tabs.count(),4)
            self.assertEqual(w.tabs.tabText(3),'Resultados y calidad')
            w.tabs.setCurrentIndex(2)
            w.experiments.tabs.setCurrentIndex(3)
            self.app.processEvents()
            self.assertTrue(w.experiments.exposure.isVisible())
            self.assertGreater(w.experiments_scroll.verticalScrollBar().maximum(),0)
            w.tabs.setCurrentIndex(3)
            self.app.processEvents()
            self.assertTrue(w.results_quality.selection.isVisible())
            self.assertGreater(w.results_scroll.verticalScrollBar().maximum(),0)
            self.assertEqual(w.plot._maximum,2000)
            w.close()

    def test_version2_migrates_to_version3_without_inventing_method(self):
        from analysis import capture
        from test_experiments import frame
        def old_sample(value):
            s = capture([frame(value=value)],'histórico')
            s.update(optics='old optics',channel='415',reference='Luz de excitación medida directamente')
            s.pop('pwm_percent')
            s.pop('pwm_raw')
            s['frames'][0].pop('pwm_percent')
            s['frames'][0].pop('pwm_raw')
            return s
        a,b = old_sample(200),old_sample(100)
        points = [dict(x=x,y=2*x+3,method='old counts',evidence=old_sample(2*x+3)) for x in (0,1,2)]
        data = dict(version=2,optics='old optics',captures={},capture_history=[a,b],
                    results=[dict(a=a,b=b,value=2,mode='led',reference_type='LED sucesivos',
                                  formula='415(A) / 415(B)',method='old ratio')],points=points,fit=None)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'legacy.json'
            atomic_json(path,data)
            panel = Experiments()
            panel.restore_session(path)
            self.assertEqual(panel.results[0]['value'],2)
            self.assertNotIn('analysis_method',panel.results[0])
            self.assertEqual(panel.results[0]['a']['pwm_percent'],25)
            self.assertEqual(panel.session_data()['version'],3)
            atomic_json(path,panel.session_data())
            second = Experiments()
            second.restore_session(path)
            self.assertEqual(second.points[2]['y'],7)
            view = ResultsQuality()
            view.set_session(second.session_data())
            view.selection.setCurrentIndex(view.selection.count()-1)
            self.assertIsNone(view.report['concentration'])
            self.assertIn('Histórico',view.quality.text())

    def test_failed_load_preserves_current_session_and_reports_error(self):
        from unittest.mock import patch
        panel = self.panel()
        self.take(panel,'signal',20,1)
        before = deepcopy(panel.session_data())
        data = self.dataset()
        data['points'][0]['x'] = 10**400
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'invalid.json'
            atomic_json(path,data)
            with patch('experiments.QFileDialog.getOpenFileName',return_value=(str(path),'JSON')):
                panel.load_session()
            self.assertIn('No se pudo abrir',panel.status.text())
            self.assertEqual(panel.session_data(),before)
