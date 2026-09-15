# Versión 1.0 de la GUI Mega

## Funciones

- Visualización en vivo de F1 a F8, NIR y Clear.
- Control de ganancia, integración y PWM de D11.
- Escala Y fija o automática para F1 a F8.
- Espejo de la pantalla Nokia 5110.
- Grabación CSV, sesiones recuperables y autoguardado.
- Capturas para LED A y B, blancos, cocientes y calibración.
- Estadísticas de réplicas completas, residuos y estimación dentro de una curva compatible.

## Instalación

```bash
cd desktop_gui
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app.py
```

En macOS, el puerto suele aparecer como `/dev/cu.usbmodem*` o `/dev/cu.usbserial*`. Configura 115200 baudios y espera a que la GUI verifique el dispositivo antes de iniciar una captura.

## Pruebas

Desde esta carpeta:

```bash
python3 -m unittest discover -s tests -v
```

Los documentos `CAMBIOS.md`, `SCIENTIFIC_NOTES.md` y `VERIFICATION.md` conservan el detalle técnico y las limitaciones científicas de esta versión.

## Uso experimental mínimo

1. Describe los LED, la corriente, los filtros y la geometría del montaje.
2. Selecciona ganancia, integración y PWM.
3. Espera a que la señal se estabilice.
4. Registra blanco y señal con el mismo ajuste.
5. Para un cociente, captura A y B como un ensayo completo.
6. Repite el ensayo completo para obtener réplicas independientes.
7. Guarda el experimento en JSON y exporta las tablas necesarias a CSV.

No compares directamente cuentas obtenidas con integraciones, ganancias o condiciones ópticas distintas.

