# Firmware

## Arduino Mega 2560

[`Arduino_Mega_AS7341/v1.0/`](Arduino_Mega_AS7341/v1.0/) contiene el sketch `.ino`, la implementación C++ y la prueba host del firmware usado con la GUI multicanal.

## IO Rodeo con PyBadge

[`IO_Rodeo_PyBadge/`](IO_Rodeo_PyBadge/) conserva tres estados:

- `reference_upstream`: referencia original del firmware multicanal. No se presenta como trabajo propio.
- `v2.0_tsl2591_gui`: snapshot con telemetría USB para la primera GUI de escritorio.
- `v3.0_as7341`: adaptación posterior con AS7341 a 90 grados y TSL2591 a 180 grados.

Los nombres `v2.0` y `v3.0` indican la secuencia de archivo dentro de este repositorio. Consulta el README de cada snapshot para conocer su función real.

