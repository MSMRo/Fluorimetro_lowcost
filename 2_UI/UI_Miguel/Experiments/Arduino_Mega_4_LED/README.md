# Demostración con Arduino Mega y cuatro LED

Esta demostración conecta el Arduino Mega 2560, el AS7341 y la GUI de escritorio. Cuatro placas LED se ensayan de forma sucesiva para observar el cambio de la respuesta multicanal.

## Montaje mostrado

- Arduino Mega 2560.
- Sensor AS7341.
- Pantalla Nokia 5110 conectada al firmware.
- GUI PyQt ejecutándose en la computadora.
- Cuatro placas LED intercambiables que no corresponden al LED de 12 V del módulo Excite final.

## Clips

| Etapa | Evidencia | Duración |
| --- | --- | ---: |
| LED 1, emisión azul visible | [`01_LED_AZUL.md`](01_LED_AZUL.md) | 39 s |
| LED 2, emisión ámbar visible | [`02_LED_AMBAR.md`](02_LED_AMBAR.md) | 64 s |
| LED 3 | [`03_LED_3.md`](03_LED_3.md) | 64 s |
| LED 4 | [`04_LED_4.md`](04_LED_4.md) | 34.17 s |

## Cómo reproducir la prueba

1. Carga el firmware de [`../../Firmware/Arduino_Mega_AS7341/v1.0/`](../../Firmware/Arduino_Mega_AS7341/v1.0/).
2. Instala e inicia la GUI de [`../../Software/Arduino_Mega_AS7341_GUI/v1.0/`](../../Software/Arduino_Mega_AS7341_GUI/v1.0/).
3. Conecta el puerto serial a 115200 baudios y espera la verificación del equipo.
4. Fija ganancia, integración y PWM. Anota cualquier cambio entre LED.
5. Con la alimentación desactivada, sustituye la placa LED.
6. Enciende la iluminación, espera estabilización y observa el espectro.
7. Inicia una grabación o captura experimental y guarda los datos.
8. Repite con el mismo montaje geométrico y condiciones comparables.

## Interpretación

Una variación en la curva demuestra que el sensor y la GUI responden al cambio de fuente. No permite asignar una longitud de onda nominal a cada LED ni comparar intensidades absolutas sin calibración, control de corriente, filtros y geometría constantes.

Los registros disponibles están en [`data/`](data/). Son datos de avance y deben revisarse antes de usarlos en un análisis científico.

