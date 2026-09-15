# PCB Excite

El módulo Excite contiene la etapa de excitación para LED. El proyecto KiCad visible incluye un regulador MIC29150-12WU-TR, un transistor BD681, resistencias, capacitores, una entrada de habilitación y una huella de LED COB. Estos datos describen el esquema archivado, no una validación eléctrica del montaje.

## Fuente de diseño

[`Excite_V1/`](Excite_V1/) contiene el esquema, la PCB, el STEP y los respaldos del proyecto KiCad. El nombre `Excite_V1` se mantuvo a lo largo de varias iteraciones de fabricación.

## Progresión de fabricación

| Versión | Carpeta | Contenido distintivo |
| --- | --- | --- |
| V1 | [`flatcam_files/`](flatcam_files/) | Primer conjunto Gerber, perforado, mapas y rutas CNC |
| V2 | [`flatcam_files_v2/`](flatcam_files_v2/) | Segunda preparación de pista y taladro |
| V3 | [`flatcam_files_v3/`](flatcam_files_v3/) | Tercera preparación y modelo `Excite_V3.step` |
| V4 | [`flatcam_files_v4/`](flatcam_files_v4/) | Cuarta ruta CNC |
| V4 láser | [`flatcam_files_v4_laser/`](flatcam_files_v4_laser/) | DXF y SVG para fabricación con láser |
| V5 láser | [`flatcam_files_v5_laser/`](flatcam_files_v5_laser/) | Iteración más reciente para los LED específicos por banda |

Los cambios eléctricos entre V1 y V5 no se deducen solo a partir de los nombres de las salidas de fabricación. Antes de producir una placa, abre el proyecto KiCad y compara pistas, perforaciones y lista de materiales con la placa física.

