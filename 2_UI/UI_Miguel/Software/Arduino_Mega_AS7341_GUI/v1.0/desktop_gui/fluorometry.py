"""Derivados instrumentales trazables; no conversiones radiométricas implícitas.

La SD se estima únicamente entre ensayos completos, no mediante propagación
de lecturas seriales potencialmente correlacionadas. Véase SCIENTIFIC_NOTES.md.
"""
from copy import deepcopy
from datetime import datetime, timezone
import json
from math import isfinite
from statistics import mean, stdev
from uuid import uuid4

from analysis import signal, ratio, linear_fit


def configuration(sample):
    return dict(gain=sample['gain'], integration=sample['integration_time'],
                pwm=sample.get('pwm_percent', 25), optics=sample['optics'],
                exposure=sample.get('exposure', ''))


def method_key(kind, samples, channels, **metadata):
    return json.dumps(dict(kind=kind, configurations=[configuration(s) for s in samples],
                           channels=list(channels), **metadata), sort_keys=True,
                      ensure_ascii=False, separators=(',', ':'))


def point_method(analysis_method, unit):
    return json.dumps(dict(analysis_method=analysis_method, unit=unit),
                      sort_keys=True, ensure_ascii=False)


def corrected_signal(sample, blank, channel):
    if sample.get('role') == 'blank':
        raise ValueError('La señal de muestra no puede ser una captura de blanco.')
    if sample['id'] == blank['id']:
        raise ValueError('La señal y el blanco deben ser capturas distintas.')
    if blank.get('role') != 'blank':
        raise ValueError('Selecciona una captura identificada como blanco.')
    if not sample.get('exposure', '').strip():
        raise ValueError('Identifica la exposición óptica para corregir el fondo.')
    if configuration(sample) != configuration(blank):
        raise ValueError('Blanco incompatible: deben coincidir exposición, protocolo, ganancia, integración y PWM.')
    # Mantener el signo evita falsear el ruido cercano al fondo.
    return signal(sample, channel) - signal(blank, channel)


def intensity_result(sample, channel=None, blank=None):
    channel = channel or sample['channel']
    raw = signal(sample, channel)
    value = corrected_signal(sample, blank, channel) if blank else raw
    key = method_key('intensity', [sample], [channel], corrected=blank is not None)
    return dict(id=uuid4().hex, kind='intensity', sample=deepcopy(sample),
                blank=deepcopy(blank), channel=channel, value=value, raw_value=raw,
                corrected=blank is not None, analysis_method=key, method=key,
                formula=f'{channel}(señal)' + (f' - {channel}(blanco)' if blank else ''),
                sample_id=sample.get('sample_id', ''), measurement_ids=[sample['id']],
                received_at=datetime.now(timezone.utc).isoformat())


def ratio_result(a, b, channel_a, channel_b, mode, reference_type, blank_a=None, blank_b=None):
    if a.get('role') == 'blank' or b.get('role') == 'blank':
        raise ValueError('Un blanco se resta al fondo; no se usa como señal o referencia del cociente.')
    if mode not in ('led', 'ref'):
        raise ValueError('Modo de cociente inválido.')
    if mode == 'ref' and reference_type not in (
            'Luz de excitación medida directamente', 'Emisión basal del fluoróforo'):
        raise ValueError('Selecciona una referencia óptica positiva; el blanco no es el denominador.')
    if a['id'] == b['id']:
        raise ValueError('El ensayo requiere dos capturas nuevas A/B.')
    if a.get('sample_id', '') != b.get('sample_id', ''):
        raise ValueError('A y B corresponden a identificadores de muestra diferentes.')
    if a['optics'] != b['optics']:
        raise ValueError('A y B requieren el mismo protocolo óptico declarado.')
    raw = ratio(a, b, channel_a, channel_b)
    if (blank_a is None) != (blank_b is None):
        raise ValueError('La corrección del cociente requiere un blanco compatible para A y otro para B.')
    numerator = corrected_signal(a, blank_a, channel_a) if blank_a else signal(a, channel_a)
    denominator = corrected_signal(b, blank_b, channel_b) if blank_b else signal(b, channel_b)
    if denominator <= 0:
        raise ValueError('La referencia corregida debe ser mayor que cero; revisa señal y blanco B.')
    if blank_a and numerator <= 0:
        raise ValueError('La señal corregida A no es positiva. Se conserva la evidencia, sin cociente cuantitativo.')
    key = method_key('ratio', [a, b], [channel_a, channel_b], mode=mode,
                     reference_type=reference_type, corrected=blank_a is not None)
    formula = (f'({channel_a}(A) - blanco A) / ({channel_b}(B) - blanco B)'
               if blank_a else f'{channel_a}(A) / {channel_b}(B)')
    return dict(id=uuid4().hex, kind='ratio', mode=mode, reference_type=reference_type,
                a=deepcopy(a), b=deepcopy(b), blank_a=deepcopy(blank_a), blank_b=deepcopy(blank_b),
                value=numerator/denominator, raw_value=raw, numerator=numerator,
                denominator=denominator, corrected=blank_a is not None,
                pwm_a=a.get('pwm_percent',25), pwm_b=b.get('pwm_percent',25),
                analysis_method=key, method=key, formula=formula,
                sample_id=a.get('sample_id',''), measurement_ids=[a['id'],b['id']],
                received_at=datetime.now(timezone.utc).isoformat())


def measurement_ids(evidence):
    if 'a' in evidence:
        return {evidence['a']['id'], evidence['b']['id']}
    if 'sample' in evidence:
        return {evidence['sample']['id']}
    return {evidence['id']}


def replicate_summary(records, selected):
    empty = dict(n=0, mean=None, sd=None, rsd=None, reason='Indica el mismo ID de muestra para agrupar réplicas completas.')
    if not selected.get('sample_id') or not selected.get('analysis_method'):
        return empty
    trials = [r for r in records if r.get('sample_id') == selected['sample_id']
              and r.get('analysis_method') == selected['analysis_method']]
    seen = set()
    for trial in trials:
        ids = measurement_ids(trial)
        if seen & ids:
            return {**empty, 'n': len(trials), 'reason': 'No evaluable: los ensayos comparten capturas de señal o referencia.'}
        seen.update(ids)
    if not trials:
        return empty
    values = [r['value'] for r in trials]
    average = mean(values)
    deviation = stdev(values) if len(trials) > 1 else None
    reason = 'SD descriptiva entre ensayos completos; no incertidumbre total.'
    if len(trials) == 1:
        reason = 'Falta repetir el ensayo completo. N lecturas no son N réplicas.'
    blank_ids = [s['id'] for r in trials for s in
                 (r.get('blank'), r.get('blank_a'), r.get('blank_b')) if s]
    if len(set(blank_ids)) < len(blank_ids):
        reason += ' Se reutilizan blancos: posible correlación y deriva no evaluadas.'
    return dict(n=len(trials), mean=average, sd=deviation,
                rsd=100*deviation/abs(average) if deviation is not None and abs(average)>1e-15 else None,
                reason=reason)


def inverse_calibration(record, points):
    outcome = dict(concentration=None, unit='', range=None, fit=None,
                   reason='No hay una curva compatible disponible.')
    if not points or not record.get('analysis_method'):
        return outcome
    if record.get('sample', {}).get('role') == 'blank' or (record.get('corrected') and record['value'] <= 0):
        return {**outcome, 'reason': 'Blanco o señal corregida no positiva: no se estima concentración de muestra.'}
    if any(p.get('analysis_method') != record['analysis_method'] for p in points):
        return {**outcome, 'reason': 'Curva incompatible: canal, señal, fondo o configuración distintos.'}
    units = {p.get('unit', '') for p in points}
    if len(units) != 1 or not next(iter(units)):
        return {**outcome, 'reason': 'La unidad de concentración no es verificable.'}
    if any(p.get('method') != point_method(p['analysis_method'],p['unit']) for p in points):
        return {**outcome, 'reason': 'La firma de la curva no coincide con sus unidades y método.'}
    if any(measurement_ids(record) & measurement_ids(p['evidence']) for p in points):
        return {**outcome, 'reason': 'Es un estándar de la curva; mide una muestra nueva para estimar concentración.'}
    try:
        fit = linear_fit(points)
    except ValueError as error:
        return {**outcome, 'reason': str(error)}
    value = (record['value'] - fit['intercept'])/fit['slope']
    bounds = (min(p['x'] for p in points), max(p['x'] for p in points))
    outcome.update(unit=next(iter(units)), range=bounds, fit=fit)
    if not isfinite(value) or value < bounds[0] or value > bounds[1] or value < 0:
        return {**outcome, 'reason': 'Fuera del rango calibrado: no se informa una concentración por extrapolación.'}
    return {**outcome, 'concentration': value,
            'reason': 'Estimación por inversión lineal, dentro del intervalo de estándares. Sin intervalo de incertidumbre ni validación externa.'}
