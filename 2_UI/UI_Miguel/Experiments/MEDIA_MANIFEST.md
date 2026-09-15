# Manifiesto de medios originales

Los originales permanecen fuera del repositorio. Se registran sus hashes para comprobar que los clips proceden de los archivos correctos.

| Archivo original | Duración | Resolución y tasa | SHA-256 | Uso |
| --- | ---: | --- | --- | --- |
| `IMG_7660.MOV` | 7.518 s | 3840 x 2160, 60 fps | `97373979a640ff70cb354c0268efe7090922c1629f4382dc448e66fb32d91656` | Demostración corta del IO Rodeo |
| `IMG_7704.MOV` | 201.165 s | 3840 x 2160, 59.94 fps | `6ea71553eface19bb1c0285349036ac75526879f4405b5b395dfdda7497e571c` | Demostración del Mega y cuatro LED |

## Conversión

Los derivados se codificaron como H.264 con audio AAC, 30 fps y reproducción progresiva para facilitar su uso en GitHub. Los clips del Mega son 1920 x 1080. El video vertical del IO Rodeo es 1080 x 1920. Se retiraron los metadatos de ubicación de los derivados.

## Cortes de `IMG_7704.MOV`

| Clip | Intervalo del original |
| --- | --- |
| `01_led_azul.mp4` | 00:00.000 a 00:39.000 |
| `02_led_ambar.mp4` | 00:39.000 a 01:43.000 |
| `03_led_3.mp4` | 01:43.000 a 02:47.000 |
| `04_led_4.mp4` | 02:47.000 a 03:21.165 |

Los límites incluyen la sustitución física de cada placa LED para no perder la continuidad de la demostración.

