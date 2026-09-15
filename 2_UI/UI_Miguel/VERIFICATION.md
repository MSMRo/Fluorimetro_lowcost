# Verificación de la copia organizada

Fecha de verificación: 14 de septiembre de 2026.

## Firmware del Arduino Mega

- Prueba C++ host aprobada: API pública del AS7341, canales raw, configuración, parser, display, barrera de captura y PWM.
- Compilación para `arduino:avr:mega` aprobada con Arduino AVR core 1.8.8.
- Uso informado por el compilador: 27 058 bytes de flash y 3 181 bytes de RAM estática.

## GUI

- GUI del Arduino Mega: 63 de 63 pruebas aprobadas en modo Qt offscreen.
- GUI histórica del IO Rodeo: 13 de 13 pruebas aprobadas.
- La prueba de integración de la GUI histórica se ajustó para localizar el firmware en `Firmware/IO_Rodeo_PyBadge/v2.0_tsl2591_gui/`. Una revisión independiente no encontró regresiones en ese cambio.

## Documentación y archivos

- 51 archivos Markdown revisados sin enlaces locales faltantes.
- Los archivos fuente copiados de Excite, Energy, Detector, firmware Mega y GUI Mega coinciden con sus originales, salvo exclusiones documentadas de cachés y archivos temporales.
- No hay archivos nuevos mayores de 95 MB.
- No se copiaron entornos virtuales, cachés Python, `fp-info-cache`, archivos `.kicad_prl` ni videos MOV originales.

## Medios

- Los cuatro clips del Mega y el video del IO Rodeo decodifican completos, con video y audio, sin errores de FFmpeg.
- Los derivados no contienen etiquetas de ubicación.
- Los intervalos y hashes de los originales están en `Experiments/MEDIA_MANIFEST.md`.

## Limitación conocida

`Firmware/IO_Rodeo_PyBadge/reference_upstream/examples/configuration.json` conserva una coma final del material de referencia y no es JSON estricto. No se usa como configuración de los snapshots adaptados.
