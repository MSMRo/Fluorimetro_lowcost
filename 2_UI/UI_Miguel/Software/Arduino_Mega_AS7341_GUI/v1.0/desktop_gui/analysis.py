"""Cálculos experimentales independientes de Qt y del puerto serial."""
from copy import deepcopy
from datetime import datetime, timezone
from math import isfinite, sqrt
from statistics import mean, stdev
from uuid import uuid4

from protocol import CHANNEL_KEYS


def capture(frames, label):
    if not frames:
        raise ValueError("No hay muestras nuevas para capturar.")
    settings = {(f['gain'], f['integration_time'], f.get('pwm_percent', 25),
                 f.get('pwm_raw', 64)) for f in frames}
    if len(settings) != 1:
        raise ValueError("La ganancia, integración o PWM cambió durante la captura. Repítela.")
    channels = {key: mean(f['channels'][key] for f in frames) for key in CHANNEL_KEYS}
    deviations = {key: stdev(f['channels'][key] for f in frames) if len(frames) > 1 else 0.0
                  for key in CHANNEL_KEYS}
    return dict(id=uuid4().hex, label=label, received_at=datetime.now(timezone.utc).isoformat(),
                gain=frames[0]['gain'], integration_time=frames[0]['integration_time'],
                pwm_percent=frames[0].get('pwm_percent', 25),
                pwm_raw=frames[0].get('pwm_raw', 64),
                n=len(frames), channels=channels, sd=deviations,
                saturated=[key for key in CHANNEL_KEYS if any(f['channels'][key] >= 65535 for f in frames)],
                frames=deepcopy(frames))


def signal(sample, channel):
    if channel in sample['saturated']:
        raise ValueError(f"Canal {channel} saturado. Reduce ganancia o integración y repite.")
    value = sample['channels'][channel]
    if not isfinite(value) or value < 0:
        raise ValueError("Señal inválida.")
    return value


def ratio(a, b, channel_a, channel_b):
    if (a['gain'], a['integration_time']) != (b['gain'], b['integration_time']):
        raise ValueError("Las dos capturas deben tener la misma ganancia e integración.")
    numerator, denominator = signal(a, channel_a), signal(b, channel_b)
    if denominator <= 0:
        raise ValueError("La referencia debe ser mayor que cero.")
    return numerator / denominator


def linear_fit(points):
    if len(points) < 3 or len({p['x'] for p in points}) < 3:
        raise ValueError("Guarda al menos tres concentraciones diferentes.")
    if len({p['method'] for p in points}) != 1:
        raise ValueError("No mezcles señales, canales ni configuraciones en una curva.")
    xs, ys = [p['x'] for p in points], [p['y'] for p in points]
    if any(not isfinite(v) for v in xs + ys):
        raise ValueError("Los puntos deben ser finitos.")
    mx, my = mean(xs), mean(ys)
    sxx = sum((x - mx)**2 for x in xs)
    slope = sum((x - mx)*(y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    residuals = [y - (slope*x + intercept) for x, y in zip(xs, ys)]
    sse = sum(r*r for r in residuals)
    sst = sum((y - my)**2 for y in ys)
    if sst == 0 or abs(slope) < 1e-15:
        raise ValueError("La señal no varía con la concentración; ajuste no utilizable.")
    return dict(slope=slope, intercept=intercept, r2=1-sse/sst,
                rmse=sqrt(sse/len(points)), residuals=residuals, n=len(points))
