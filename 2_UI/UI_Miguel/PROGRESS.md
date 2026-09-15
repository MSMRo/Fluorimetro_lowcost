# Progresión del proyecto

Esta cronología reúne fechas visibles en los respaldos, documentos y archivos del proyecto. Cuando una carpeta no tiene un registro formal de cambios, se describe solo lo que puede verificarse en sus artefactos.

## Abril de 2026

- 14 de abril: primeros respaldos de Excite V1 y Detector V1.
- 15 de abril: primera preparación de archivos Gerber, perforado y mecanizado para Excite y Energy.
- 21 al 22 de abril: segundas iteraciones de FlatCAM para Excite y Energy.
- 25 de abril: archivos de fabricación de Excite V3 y modelo STEP asociado.
- 27 de abril: respaldo posterior del proyecto KiCad Excite V1.

## Mayo de 2026

- 5 y 6 de mayo: consolidación de la ruta de fabricación final de Energy. La carpeta `flatcam_vfinal` conserva proyectos FlatCAM, mapas, pista y taladro.

## Agosto de 2026

- 26 de agosto: diseño de la comunicación serial y de la GUI UPCH.
- 27 de agosto: diseño de la adaptación para Arduino Mega, adquisición multicanal y pantalla externa.

## Septiembre de 2026

- 8 de septiembre: registro visual del IO Rodeo funcionando con el AS7341. También aparecen respaldos recientes del proyecto Excite.
- 11 de septiembre: control PWM de la salida LED desde la GUI y firmware Mega 2.3.0. Se añadieron trazabilidad de PWM y validaciones de compatibilidad.
- 12 de septiembre: módulos de experimentos, blancos, cocientes, calibración, resultados y controles de calidad. Quedó pendiente la validación óptica con el montaje real.
- 14 de septiembre: escala Y automática opcional en la GUI y registro de la demostración con cuatro placas LED.

## Relación entre ramas

| Rama | Controlador | Sensor principal | Pantalla | Software de escritorio |
| --- | --- | --- | --- | --- |
| IO Rodeo adaptado | PyBadge | AS7341 a 90 grados y TSL2591 a 180 grados | Integrada en el equipo | GUI TSL anterior, cuando se usa el firmware con telemetría |
| Demostración Mega | Arduino Mega 2560 | AS7341 | Nokia 5110 | GUI multicanal en PyQt |

## Estado de las PCB

- Excite V5 es la iteración de fabricación más reciente y se conserva como la versión actual para LED específicos por banda.
- Energy conserva la fuente KiCad, dos rutas FlatCAM previas, una ruta final y archivos para corte láser.
- Detector V1 se archiva como diseño no utilizado en el montaje AST actual.

