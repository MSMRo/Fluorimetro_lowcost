# Open-Ratio Fluorimeter

Repositorio de trabajo para la adaptación del fluorímetro ratiométrico de IO Rodeo. Reúne el firmware, las interfaces gráficas, las PCB, la carcasa y las evidencias experimentales desarrolladas durante la pasantía en la UPCH.

## Estado actual

Hay dos montajes documentados:

1. El IO Rodeo con PyBadge, pantalla integrada y adaptación para el sensor AS7341.
2. La versión de demostración con Arduino Mega 2560, AS7341, pantalla Nokia 5110, GUI de escritorio y cuatro placas LED intercambiables.

La PCB Excite V5 es la iteración más reciente del módulo de excitación y está orientada al uso de LED seleccionados por banda. La PCB Energy entrega las líneas de alimentación usadas por el montaje, incluida la alimentación de 5 V para el Arduino Mega y la línea de 12 V para la iluminación. La PCB Detector se conserva como avance de diseño, pero no forma parte del montaje actual porque la detección se realizará con un módulo AST.

## Contenido

| Sección | Contenido |
| --- | --- |
| [`Firmware/`](Firmware/) | Firmware del Arduino Mega y snapshots del IO Rodeo con PyBadge |
| [`Software/`](Software/) | GUI del Mega y GUI anterior para el IO Rodeo |
| [`Hardware/Electronics/`](Hardware/Electronics/) | PCB Excite, Energy y Detector, con sus iteraciones de fabricación |
| [`Hardware/3D_Models/`](Hardware/3D_Models/) | Carcasa final en STL |
| [`Experiments/`](Experiments/) | Videos, clips por LED, pósteres y datos registrados |
| [`Papers/`](Papers/) | Artículos de referencia reunidos para el proyecto |
| [`PROGRESS.md`](PROGRESS.md) | Cronología y relación entre versiones |
| [`VERIFICATION.md`](VERIFICATION.md) | Pruebas ejecutadas sobre la copia organizada |
| [`UPLOAD_CHECKLIST.md`](UPLOAD_CHECKLIST.md) | Revisión previa al commit y al envío a GitHub |

## Por dónde empezar

- Para reproducir la versión con Arduino Mega, consulta [`Firmware/Arduino_Mega_AS7341/`](Firmware/Arduino_Mega_AS7341/) y [`Software/Arduino_Mega_AS7341_GUI/`](Software/Arduino_Mega_AS7341_GUI/).
- Para revisar la progresión de la PCB de excitación, abre [`Hardware/Electronics/Excitation/README.md`](Hardware/Electronics/Excitation/README.md).
- Para ver la demostración por cada LED, abre [`Experiments/Arduino_Mega_4_LED/README.md`](Experiments/Arduino_Mega_4_LED/README.md).
- Para revisar el funcionamiento del IO Rodeo, abre [`Experiments/IO_Rodeo_AS7341/README.md`](Experiments/IO_Rodeo_AS7341/README.md).

## Criterio de archivo

Los nombres originales de los proyectos KiCad y de sus archivos de fabricación se conservaron para no romper referencias ni ocultar el historial. Las etiquetas de versión añadidas en esta organización describen el orden de trabajo encontrado en las carpetas. No sustituyen un número de revisión grabado en la PCB.

Los videos originales de cámara no se incluyen porque `IMG_7704.MOV` supera el límite habitual de GitHub. El repositorio contiene versiones H.264 más pequeñas, sin metadatos de ubicación, y un manifiesto con los hashes de los originales.

## Antes de usar el equipo

Revisa tensiones, polaridad, masa común y compatibilidad de niveles lógicos antes de energizar el montaje. Los archivos y las pruebas de software no certifican seguridad eléctrica, calibración óptica ni precisión metrológica.
