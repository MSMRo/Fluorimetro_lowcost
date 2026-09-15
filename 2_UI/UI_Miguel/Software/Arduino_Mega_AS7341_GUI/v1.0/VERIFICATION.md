# Verificación de firmware y GUI

Fecha: 2026-09-14. Proyecto aislado; no se modificaron `upch_GUI` ni `upch_firmware`.

## Resultados

- 63 pruebas Python/Qt aprobadas en modo offscreen con el entorno `desktop_gui/.venv`.
- Seis pruebas de escala Auto: modo fijo inicial, ajuste y retorno manual, exclusión de NIR/Clear/OVFL, límites, pausa/reanudación, ausencia de comandos al firmware y transiciones animadas válidas o saturadas. Revisión visual del botón a 980 × 680 con datos simulados.
- Nuevas pruebas: resta con signo, blancos por exposición, cocientes corregidos, ensayos completos frente a lecturas seriales, no reutilización de señal como réplica, compatibilidad de calibración, inversión conocida y bloqueo de extrapolación/autopredicción del estándar.
- Recuperación v2→v3→recuperación verificada con cocientes y puntos. Un archivo con resultado/componentes alterados, firma incompatible o concentración excesiva se rechaza; la sesión actual se conserva.
- Exportación CSV verificada para resultados, captura raw de muestra desconocida y captura saturada (sin falsa concentración). El CSV diferencia filas de captura y resultado con `evidence_type`; ambas no deben contarse como réplicas adicionales.
- Revisión de código realizada; los hallazgos sobre blancos y números JSON excesivos se corrigieron y probaron.
- Prueba C++ con sensor, pantalla y UART simulados aprobada: API pública del AS7341, orden raw, ganancias, integraciones, parser, display, captura, negociación de capacidad y PWM D11 en 0 %, 25 %, 50 % y 100 %.
- Compilación real previa del 2026-09-11 para `arduino:avr:mega`, core AVR 1.8.8, con advertencias habilitadas: 27058 bytes de flash (10 %) y 3181 bytes de RAM estática (38 %). Esta ampliación no modifica el firmware ni requiere otra carga.
- Revisión visual offscreen de las secciones nuevas a 980 × 680 y 1100 × 900. Controles y tablas disponen de desplazamiento para conservar acceso a detalles e IDs. Las pruebas de adquisición, escala fija, pausa, grabación y espejo IO Rodeo siguen pasando.

## Repetir las pruebas

Desde la raíz de este proyecto, con PyQt6 y pyserial instalados:

```bash
QT_QPA_PLATFORM=offscreen PYTHONPATH=desktop_gui desktop_gui/.venv/bin/python -m unittest discover -s tests -v
clang++ -std=c++17 -Wall -Wextra -I tests/firmware_host -I .arduino/libraries/ArduinoJson/src tests/firmware_host/test_firmware.cpp -o /tmp/upch-as7341-firmware-test
/tmp/upch-as7341-firmware-test
ARDUINO_DIRECTORIES_USER="$PWD/.arduino" arduino-cli compile --fqbn arduino:avr:mega --warnings all firmware/mega_as7341_multichannel
```

Las versiones de bibliotecas están en README.md. En este Mac se usó el `arduino-cli` incluido en Arduino IDE, en `/Applications/Arduino IDE.app/Contents/Resources/app/lib/backend/resources/arduino-cli`.

## Estado de validación física

El usuario confirmó comunicación con el Mega, recepción multicanal, patrón azul, GUI y Nokia con la configuración anterior. El nuevo control PWM de la versión 2.3.0 está verificado por pruebas y compilación, pero falta cargarlo y comprobar físicamente D11 a 0 %, 25 %, 50 % y 100 %. El modo IO Rodeo reproduce el contenido multicanal disponible; no inventa batería, TSL a 180° ni Relative Units.

La corrección de fondo, las curvas y las estadísticas nuevas están verificadas con datos simulados y evidencia bibliográfica, no con estándares reales del montaje. Falta comprobar matriz del blanco, estabilidad, repetibilidad y controles independientes; no se informa LOD/LOQ, eficiencia cuántica ni incertidumbre certificada.
