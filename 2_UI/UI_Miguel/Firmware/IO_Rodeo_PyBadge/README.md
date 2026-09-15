# Firmware del IO Rodeo con PyBadge

## `reference_upstream`

Código de referencia del proyecto multichannel colorimeter. Se conserva para comparar la base con las adaptaciones de la UPCH. Revisa su licencia y README originales antes de redistribuirlo.

Consulta [`reference_upstream/ARCHIVE_NOTES.md`](reference_upstream/ARCHIVE_NOTES.md) antes de usar sus ejemplos.

## `v2.0_tsl2591_gui`

Snapshot basado en el firmware `latest` que agrega un segundo puerto USB CDC. Ese puerto permite a la primera GUI recibir telemetría y enviar cambios de modo, ganancia, integración y normalización.

## `v3.0_as7341`

Snapshot que añade AS7341 a 90 grados en el canal 3 del PCA9546A y conserva un TSL2591 a 180 grados en el canal 0. Incluye la opción `Multichannel 90`, con dos páginas para los diez canales del AS7341.

Para instalar un snapshot, copia su contenido completo a la raíz de `CIRCUITPY`. No mezcles archivos entre snapshots.
