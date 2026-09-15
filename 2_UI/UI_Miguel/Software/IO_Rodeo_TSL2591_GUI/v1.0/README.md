# UPCH GUI

Aplicación PyQt para observar y controlar la copia TSL del firmware desde el
computador. El equipo conserva su pantalla y botones; la GUI recibe los mismos
valores que el firmware usa para dibujarla.

## Arranque

```bash
cd upch_GUI
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m upch_gui
```

Conecta el PyBadge con el contenido de
`../../../Firmware/IO_Rodeo_PyBadge/v2.0_tsl2591_gui/`. En el selector de
puertos elige el segundo puerto serial del PyBadge: es el puerto USB CDC de
datos, no la consola REPL.

## Alcance de esta versión

- Valores en tiempo real de los dos TSL2591.
- Modos `Raw Count`, `Irradiance` y `Relative Units`.
- Ganancia, tiempo de integración y normalización.
- Gráfica de la sesión y exportación CSV.
