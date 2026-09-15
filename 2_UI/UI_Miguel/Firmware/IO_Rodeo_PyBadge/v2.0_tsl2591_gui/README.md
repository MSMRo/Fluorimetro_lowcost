# Firmware TSL con telemetría para UPCH GUI

Este snapshot parte del firmware `latest` para el PyBadge. Conserva el
comportamiento original de pantalla y botones, y añade un segundo puerto USB
CDC para que la GUI archivada en
`../../../Software/IO_Rodeo_TSL2591_GUI/v1.0/` reciba las mismas lecturas y
envíe cambios de modo, ganancia, integración y normalización.

## Instalación

1. Conecta el PyBadge y abre su unidad `CIRCUITPY`.
2. Copia el contenido de esta carpeta a la raíz de `CIRCUITPY`, incluidos
   `boot.py`, `code.py`, `src/`, `assets/`, `lib/` y `configuration.json`.
3. Reinicia el PyBadge con `Ctrl+D` o desconectándolo y conectándolo de nuevo.
4. Abre la GUI desde
   `../../../Software/IO_Rodeo_TSL2591_GUI/v1.0/` y selecciona el puerto USB
   CDC de datos del PyBadge, no el puerto de la consola REPL.

## Protocolo

El puerto de datos usa JSON Lines (un objeto JSON UTF-8 por línea). El
firmware envía `hello`, `state`, `telemetry`, `ack` y `error`. La GUI inicial
envía `get_state`, `set_mode`, `set_sensor_setting` y `normalize`.

No mezcles esta carpeta con `reference_upstream`: se mantiene aislada para
poder comparar el snapshot con la referencia.
