# Firmware latest + AS7341 a 90 grados

Esta carpeta conserva el firmware `latest` y añade soporte para:

- AS7341 a 90 grados en el canal 3 del PCA9546A.
- TSL2591 a 180 grados en el canal 0 del PCA9546A.
- Nueva opción `Multichannel 90` dentro del menú existente.

No se reemplazaron el arranque, el splash, el menú, las pantallas normales ni
el funcionamiento de los botones de `latest`.

## Menú

Las opciones aparecen en este orden:

1. `Raw Count`
2. `Relative Units`
3. `Multichannel 90`
4. `About`

`Raw Count`, `Relative Units` y `About` mantienen el formato de `latest`.
Se retiró `Irradiance` porque el AS7341 de 90 grados no tiene una calibración
absoluta para este montaje. `Multichannel 90` es el agregado.

## Multichannel 90

Muestra los diez canales del AS7341:

| Página 1 | Página 2 |
| --- | --- |
| 415 nm | 590 nm |
| 445 nm | 630 nm |
| 480 nm | 680 nm |
| 515 nm | NIR |
| 555 nm | clear |

Controles dentro de esta opción:

- `RIGHT`: página siguiente.
- `LEFT`: página anterior.
- `GAIN`: cambia la ganancia del AS7341.
- `ITIME`: cambia el tiempo de integración del AS7341.
- `MENU`: regresa al menú normal.

La pantalla conserva los colores, tipografías y pie de batería de `latest`.
`OVFL` en rojo significa que esa banda está saturada.

## Compatibilidad con las opciones anteriores

En `Raw Count`, el valor de 90 grados corresponde al canal `clear` del
AS7341; el valor de 180 grados continúa proviniendo del TSL2591.

El AS7341 no incorpora una calibración absoluta de irradiancia para este
montaje. `Relative Units` continúa disponible, pero la lectura de 90 grados
es una señal `clear` normalizada por ganancia y tiempo. Para reportarla como
irradiancia absoluta se requiere una calibración experimental.

## Configuración

El archivo conserva el formato de `latest`:

```json
{
  "startup": "Relative Units",
  "gain_sensor_90": "128x",
  "itime_sensor_90": "300ms",
  "gain_sensor_180": "med",
  "itime_sensor_180": "300ms",
  "ref_irradiance_180": 1000
}
```

Ganancias válidas para el AS7341:

`0.5x`, `1x`, `2x`, `4x`, `8x`, `16x`, `32x`, `64x`, `128x`, `256x`,
`512x`.

Tiempos válidos:

`50ms`, `100ms`, `200ms`, `300ms`, `400ms`, `600ms`.

## Instalación en el PyBadge

1. Apagar el equipo.
2. Verificar AS7341 en `PCA9546A[3]` y TSL2591 en `PCA9546A[0]`.
3. Conectar el PyBadge y abrir `CIRCUITPY`.
4. Copiar el contenido completo de este snapshot a la raíz de `CIRCUITPY`.
5. Reiniciar el PyBadge o usar `Ctrl+D` en la consola serial.

La carpeta incluye `adafruit_as7341.mpy` y `adafruit_register`, además de las
librerías originales.

## Errores

El formato de errores es el mismo de `latest`:

- Si el AS7341 no responde en el canal 3: pantalla `Abort` con
  `missing sensor? ...`.
- Si el TSL2591 no responde en el canal 0: pantalla `Abort` con
  `missing sensor? ...`.
- Si una banda llega al máximo ADC: se muestra `OVFL` en rojo.

Ante `OVFL`, reducir primero `GAIN`; si continúa, reducir `ITIME` o la
intensidad de la fuente.
