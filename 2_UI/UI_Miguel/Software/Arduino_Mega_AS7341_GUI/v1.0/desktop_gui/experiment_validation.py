"""Validación y recuperación de sesiones con evidencia raw (v2/v3)."""
from copy import deepcopy
import math

from analysis import capture, linear_fit
from fluorometry import intensity_result, ratio_result, measurement_ids, point_method
from protocol import CHANNEL_KEYS, parse_telemetry


def finite_number(value):
    try:
        return type(value) in (int,float) and math.isfinite(value)
    except OverflowError:
        return False


def validate_session(payload):
    data = deepcopy(payload)
    if not isinstance(data, dict) or type(data.get('version')) is not int or data['version'] not in (2,3):
        raise ValueError('Se requiere una sesión versión 2 o 3.')
    legacy = data['version'] == 2
    if not isinstance(data.get('optics'), str):
        raise ValueError('Protocolo óptico inválido.')
    data.setdefault('intensity_results', [])
    for key in ('results','points','capture_history','intensity_results'):
        if not isinstance(data.get(key), list) or len(data[key]) > 10000:
            raise ValueError('Estructura o cantidad de registros inválida.')
    if not isinstance(data.get('captures',{}), dict):
        raise ValueError('Capturas inválidas.')
    registry = {}

    def validate_capture(sample):
        if not isinstance(sample,dict):
            raise ValueError('Captura inválida.')
        frames = sample['frames']
        if not isinstance(frames,list) or not 1 <= len(frames) <= 100:
            raise ValueError('Cantidad de lecturas inválida.')
        for frame in frames:
            parse_telemetry({**frame,'type':'telemetry'})
        if any(b['sequence'] <= a['sequence'] for a,b in zip(frames,frames[1:])):
            raise ValueError('Secuencias duplicadas o reinicio dentro de una captura.')
        recomputed = capture(frames,sample['label'])
        sample.setdefault('pwm_percent',recomputed['pwm_percent'])
        sample.setdefault('pwm_raw',recomputed['pwm_raw'])
        for key in ('channels','sd','saturated','n','gain','integration_time','pwm_percent','pwm_raw'):
            if sample[key] != recomputed[key]:
                raise ValueError('La captura no coincide con sus muestras crudas.')
        for key in ('id','label','optics'):
            if not isinstance(sample[key],str) or len(sample[key]) > 2000:
                raise ValueError('Metadatos de captura inválidos.')
        for key,default in (('sample_id',''),('exposure',''),('role','legacy'),('reference','')):
            sample.setdefault(key,default)
            if not isinstance(sample[key],str) or len(sample[key]) > 2000:
                raise ValueError('Metadatos experimentales inválidos.')
        if not sample['id'] or sample['channel'] not in CHANNEL_KEYS:
            raise ValueError('Identificador o canal inválido.')
        if sample['role'] not in ('legacy','signal','blank','cal','leda','ledb','refa','refb'):
            raise ValueError('Rol experimental inválido.')
        if sample['id'] in registry and sample != registry[sample['id']]:
            raise ValueError('Un identificador de captura contiene evidencias contradictorias.')
        registry[sample['id']] = deepcopy(sample)
        return sample

    def validate_result(result):
        if not isinstance(result,dict):
            raise ValueError('Resultado inválido.')
        old = legacy or result.get('legacy') is True
        if 'a' in result:
            a,b = validate_capture(result['a']),validate_capture(result['b'])
            ba,bb = result.get('blank_a'),result.get('blank_b')
            if ba is not None: validate_capture(ba)
            if bb is not None: validate_capture(bb)
            computed = ratio_result(a,b,a['channel'],b['channel'],result['mode'],result['reference_type'],ba,bb)
        else:
            sample = validate_capture(result['sample'])
            blank = result.get('blank')
            if blank is not None: validate_capture(blank)
            computed = intensity_result(sample,result['channel'],blank)
        if not finite_number(result.get('value')) or not math.isclose(computed['value'],result['value'],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('El resultado guardado no coincide con su evidencia.')
        if not old:
            for key in ('analysis_method','method','formula','corrected','raw_value','sample_id','measurement_ids','kind'):
                if result.get(key) != computed[key]:
                    raise ValueError('Método o metadatos del resultado incompatibles con su evidencia.')
            for key in ('numerator','denominator','pwm_a','pwm_b') if 'a' in result else ():
                if result.get(key) != computed[key]:
                    raise ValueError('Los componentes del cociente no coinciden con su evidencia.')
        else:
            result['legacy'] = True
            # No inferir una firma de calibración ausente en datos históricos.
            result.pop('analysis_method',None)
            for key in ('numerator','denominator','raw_value','pwm_a','pwm_b','sample_id','measurement_ids'):
                if key in computed:
                    result[key] = computed[key]
        return computed

    for sample in data['capture_history']:
        validate_capture(sample)
    for sample in data.get('captures',{}).values():
        validate_capture(sample)
    for result in data['results'] + data['intensity_results']:
        validate_result(result)
    seen_points = set()
    for point in data['points']:
        if not all(finite_number(point.get(k)) for k in ('x','y')) or point['x'] < 0:
            raise ValueError('Punto no finito o concentración negativa.')
        evidence = point['evidence']
        if 'a' in evidence or 'sample' in evidence:
            computed = validate_result(evidence)
        else:
            computed = intensity_result(validate_capture(evidence))
        if computed.get('sample',{}).get('role') == 'blank':
            raise ValueError('Un blanco de fondo no se reutiliza como estándar; captura el nivel conocido como calibración.')
        if not math.isclose(point['y'],computed['value'],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('El punto no coincide con su evidencia.')
        ids = measurement_ids(evidence)
        if seen_points & ids:
            raise ValueError('La curva reutiliza una medición como varios estándares.')
        seen_points.update(ids)
        if legacy or point.get('legacy') is True:
            point['legacy'] = True
            point.pop('analysis_method',None)
        elif (not isinstance(point.get('unit'),str) or not point['unit'].strip()
              or point.get('analysis_method') != computed['analysis_method']
              or point.get('method') != point_method(computed['analysis_method'],point['unit'])):
            raise ValueError('El método del punto no coincide con su evidencia.')
        if not isinstance(point.get('method'),str) or point['method'] != data['points'][0]['method']:
            raise ValueError('La curva mezcla métodos.')
    data['fit'] = linear_fit(data['points']) if data.get('fit') is not None else None
    return data
