# PCB Energy

La PCB Energy se usa para la alimentación del montaje, con una línea de 5 V para el Arduino Mega y una línea de 12 V para la iluminación. El esquema archivado contiene entrada por conector DC, fusible de 10 A, diodo Zener, convertidor MC00100, MOSFET DMP6023LE-13 y filtrado.

## Archivos

- `Untitled.kicad_sch` y `Untitled.kicad_pcb`: fuente KiCad.
- `Energia .step`: modelo 3D exportado.
- `Untitled-backups/`: respaldos cronológicos de abril y mayo de 2026.
- `flatcam_files/`: primera preparación de fabricación.
- `flatcam_files_v2/`: segunda preparación.
- `flatcam_vfinal/`: ruta final conservada.
- `cortadora_laser_v5_energy/`: Gerber y perforaciones para el flujo de corte láser.

Mide ambas salidas sin carga antes de conectar el Mega o los LED. Verifica polaridad, masa común, capacidad de corriente y temperatura de los componentes.

