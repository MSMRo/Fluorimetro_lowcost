import unittest
from copy import deepcopy

from analysis import capture
from test_experiments import frame
from fluorometry import intensity_result, ratio_result, replicate_summary, inverse_calibration, point_method
from experiment_validation import validate_session


def sample(value, exposure='LED A 445 nm', sample_id='M1', role='signal', seq=1):
    data = capture([frame(seq, value), frame(seq + 1, value + 2)], 'test')
    data.update(optics='LED A/B, filtro, cubeta 90 grados', exposure=exposure,
                sample_id=sample_id, role=role, channel='445', reference='LED sucesivos')
    return data


class FluorometryTests(unittest.TestCase):
    def test_signed_background_subtraction_and_raw_preserved(self):
        a, blank = sample(4), sample(9, role='blank', sample_id='')
        before = deepcopy(a)
        result = intensity_result(a, '445', blank)
        self.assertEqual(result['value'], -5)
        self.assertEqual(result['raw_value'], 5)
        self.assertEqual(a, before)

    def test_blank_requires_matching_exposure_pwm_and_role(self):
        a = sample(20)
        for changes in ({'exposure': 'LED B'}, {'pwm_percent': 50, 'pwm_raw': 128},
                        {'gain': '64x'}, {'role': 'signal'}, {'exposure': ''}):
            blank = {**sample(3, role='blank'), **changes}
            with self.assertRaises(ValueError):
                intensity_result(a, '445', blank)
        with self.assertRaises(ValueError):
            intensity_result(a, '445', a)

    def test_ratio_subtracts_each_exposure_and_tracks_methods(self):
        a, b = sample(100), sample(50, exposure='LED B 515 nm')
        ba, bb = sample(10, role='blank'), sample(5, exposure='LED B 515 nm', role='blank')
        result = ratio_result(a, b, '445', '445', 'led', 'LED sucesivos', ba, bb)
        self.assertEqual(result['value'], 2)
        self.assertNotEqual(result['value'], result['raw_value'])
        self.assertNotEqual(result['analysis_method'], ratio_result(a, b, '445', '445', 'led', 'LED sucesivos')['analysis_method'])

    def test_ratio_rejects_nonpositive_corrected_reference_or_signal(self):
        a, b = sample(100), sample(10, exposure='LED B')
        for va, vb in ((101, 3), (1, 11)):
            with self.assertRaises(ValueError):
                ratio_result(a, b, '445', '445', 'led', 'LED sucesivos',
                             sample(va, role='blank'), sample(vb, exposure='LED B', role='blank'))

    def test_ratio_requires_two_new_captures_and_same_sample(self):
        a = sample(100)
        with self.assertRaises(ValueError):
            ratio_result(a, a, '445', '445', 'led', 'LED sucesivos')
        with self.assertRaises(ValueError):
            ratio_result(a, sample(10, sample_id='M2'), '445', '445', 'led', 'LED sucesivos')

    def test_saturation_is_rejected(self):
        with self.assertRaises(ValueError):
            intensity_result(sample(65533), '445')

    def test_replicates_are_full_trials_not_frame_count(self):
        records = [ratio_result(sample(v), sample(9, exposure='B'), '445', '445', 'led', 'LED sucesivos') for v in (19, 29, 39)]
        stats = replicate_summary(records, records[0])
        self.assertEqual(stats['n'], 3)
        self.assertEqual(stats['mean'], 3)
        self.assertEqual(stats['sd'], 1)
        other = ratio_result(sample(99, sample_id='other'), sample(9, exposure='B', sample_id='other'), '445', '445', 'led', 'LED sucesivos')
        self.assertEqual(replicate_summary(records + [other], records[0])['n'], 3)

    def test_reused_measurement_cannot_be_a_replicate(self):
        r = intensity_result(sample(10))
        stats = replicate_summary([r, deepcopy(r)], r)
        self.assertIsNone(stats['sd'])
        self.assertIn('comparten', stats['reason'])

    def test_one_reading_does_not_have_an_empirical_sd(self):
        r = intensity_result(sample(10))
        self.assertIsNone(replicate_summary([r], r)['sd'])

    def calibration(self):
        points = []
        for x in (0, 1, 2):
            r = intensity_result(sample(2*x + 2, sample_id='standard'))
            points.append(dict(x=x, y=r['value'], method=point_method(r['analysis_method'], 'umol/L'),
                               analysis_method=r['analysis_method'], unit='umol/L', evidence=r))
        return points

    def test_inverse_calibration_and_no_extrapolation(self):
        points = self.calibration()
        result = inverse_calibration(intensity_result(sample(3)), points)
        self.assertAlmostEqual(result['concentration'], .5)
        self.assertEqual(result['unit'], 'umol/L')
        self.assertIsNone(inverse_calibration(intensity_result(sample(100)), points)['concentration'])

    def test_calibration_rejects_settings_mismatch_and_self_prediction(self):
        points = self.calibration()
        altered = {**sample(3), 'pwm_percent': 50, 'pwm_raw': 128}
        self.assertIsNone(inverse_calibration(intensity_result(altered), points)['concentration'])
        self.assertIsNone(inverse_calibration(points[0]['evidence'], points)['concentration'])

    def test_restore_recomputes_and_detects_tampering(self):
        a, b = sample(100), sample(50, exposure='B')
        r = ratio_result(a, b, '445', '445', 'led', 'LED sucesivos')
        data = dict(version=3, optics=a['optics'], captures={}, capture_history=[a,b],
                    results=[r], intensity_results=[], points=[], fit=None)
        self.assertEqual(validate_session(data)['results'][0]['value'], r['value'])
        data['results'][0]['value'] = 999
        with self.assertRaises(ValueError):
            validate_session(data)

    def test_restore_rejects_tampered_denominator_and_large_numbers(self):
        a,b = sample(100),sample(50,exposure='B')
        r = ratio_result(a,b,'445','445','led','LED sucesivos')
        data = dict(version=3,optics='test',captures={},capture_history=[],
                    results=[r],intensity_results=[],points=[],fit=None)
        altered = deepcopy(data)
        altered['results'][0]['denominator'] = 999
        with self.assertRaises(ValueError):
            validate_session(altered)
        altered = deepcopy(data)
        altered['results'][0]['value'] = 10**400
        with self.assertRaises(ValueError):
            validate_session(altered)
        altered = {**data,'points':self.calibration()}
        altered['points'][0]['x'] = 10**400
        with self.assertRaises(ValueError):
            validate_session(altered)

    def test_restore_rejects_tampered_calibration_method(self):
        points = self.calibration()
        data = dict(version=3, optics='test', captures={}, capture_history=[],
                    results=[], intensity_results=[], points=points, fit=None)
        self.assertEqual(len(validate_session(data)['points']), 3)
        data['points'][0]['analysis_method'] = 'forged'
        with self.assertRaises(ValueError):
            validate_session(data)
